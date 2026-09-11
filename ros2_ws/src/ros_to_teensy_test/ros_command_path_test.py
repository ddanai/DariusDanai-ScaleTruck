#!/usr/bin/env python3
"""Repeatable ROS 2-to-Teensy fixed-command acceptance test."""

import re
import sys
import time

import rclpy
from rclpy.node import Node
from scale_truck_msgs.msg import Lrc2Ocr
from std_msgs.msg import String
from std_srvs.srv import Trigger


class CommandPathTest(Node):
    def __init__(self):
        super().__init__("ros_command_path_test")
        self.lines = []
        self.command_pub = self.create_publisher(Lrc2Ocr, "lrc2ocr_msg", 1)
        self.create_subscription(String, "firmware/serial_status", self.on_line, 10)
        self.service_clients = {
            name: self.create_client(Trigger, f"firmware/{name}")
            for name in ("arm", "disarm", "clear_faults", "status")
        }
        self.passes = 0
        self.failures = []

    def on_line(self, msg):
        self.lines.append(msg.data)

    def wait_for_services(self):
        for name, client in self.service_clients.items():
            if not client.wait_for_service(timeout_sec=5.0):
                raise RuntimeError(f"firmware/{name} service is unavailable")

    def call(self, name):
        future = self.service_clients[name].call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
        if not future.done() or not future.result().success:
            raise RuntimeError(f"firmware/{name} could not send its command")

    def wait_line(self, pattern, timeout=2.0):
        regex = re.compile(pattern)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            for index, line in enumerate(self.lines):
                if regex.search(line):
                    self.lines.pop(index)
                    return line
        raise RuntimeError(f"no Teensy reply matching {pattern!r}")

    def check(self, name, action, reply_pattern):
        try:
            action()
            line = self.wait_line(reply_pattern)
            self.passes += 1
            print(f"PASS {name}: {line}")
        except RuntimeError as exc:
            self.failures.append(f"{name}: {exc}")
            print(f"FAIL {name}: {exc}")

    def publish_for(self, speed, steering, duration=0.5):
        msg = Lrc2Ocr()
        msg.tar_vel = speed
        msg.steer_angle = steering
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            self.command_pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.05)

    def run(self):
        self.wait_for_services()
        self.check("clear", lambda: self.call("clear_faults"), r"^OK FAULTS_CLEARED$")
        self.check("arm", lambda: self.call("arm"), r"^OK ARMED$")
        self.publish_for(0.2, 0.0)
        self.check(
            "active command",
            lambda: self.call("status"),
            r"^STATUS .*safety_state=ACTIVE throttle_cmd=0\.1000 "
            r"steering_cmd=0\.0000",
        )
        time.sleep(0.35)
        self.check(
            "watchdog neutral",
            lambda: self.call("status"),
            r"^STATUS .*safety_state=WATCHDOG_FAULT throttle_cmd=0\.0000 "
            r"steering_cmd=0\.0000",
        )
        self.check("clear watchdog", lambda: self.call("clear_faults"), r"^OK FAULTS_CLEARED$")
        self.check("disarm", lambda: self.call("disarm"), r"^OK DISARMED$")

        print(f"\nRESULT: {self.passes} passed, {len(self.failures)} failed")
        for failure in self.failures:
            print(f"  - {failure}")
        return 1 if self.failures else 0


def main():
    rclpy.init()
    node = CommandPathTest()
    try:
        return node.run()
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 1
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())
