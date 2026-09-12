#!/usr/bin/env python3
"""Exercise real controller/LRC nodes with synthetic scans; no serial or actuators."""

import math
import subprocess
import time

import rclpy
from rclpy.node import Node
from scale_truck_msgs.msg import Lrc2Ocr
from sensor_msgs.msg import LaserScan


def main():
    rclpy.init()
    node = Node("distance_test", namespace="distance_test")
    pub = node.create_publisher(LaserScan, "scan", 10)
    outputs = []
    node.create_subscription(Lrc2Ocr, "lrc2ocr_msg", outputs.append, 10)
    processes = []

    def check(name, expected, ranges=None, stamp_age=0.0, settle=0.4):
        started = time.monotonic()
        deadline = started + 4.0
        while time.monotonic() < deadline:
            outputs.clear()
            if ranges is not None:
                scan = LaserScan()
                stamp_ns = node.get_clock().now().nanoseconds - int(stamp_age * 1e9)
                scan.header.stamp.sec = stamp_ns // 1_000_000_000
                scan.header.stamp.nanosec = stamp_ns % 1_000_000_000
                scan.angle_min = -0.2
                scan.angle_max = 0.2
                scan.angle_increment = 0.2
                scan.range_min = 0.15
                scan.range_max = 25.0
                scan.ranges = ranges
                pub.publish(scan)
            rclpy.spin_once(node, timeout_sec=0.05)
            if time.monotonic() - started >= settle and any(
                abs(msg.tar_vel - expected) < 1e-5 and msg.steer_angle == 0.0
                for msg in outputs
            ):
                print(f"PASS {name}")
                return
        raise AssertionError(f"{name}: expected speed {expected}")

    try:
        common = ["--ros-args", "-r", "__ns:=/distance_test"]
        controller = subprocess.Popen([
            "ros2", "run", "scale_truck_control", "scale_truck_control_node",
            *common, "-p", "params.target_vel:=0.2",
        ], start_new_session=True)
        processes.append(controller)
        processes.append(subprocess.Popen([
            "ros2", "run", "scale_truck_control", "lrc_node", *common,
            "-p", "lrc_params.udp_group_port:=19392",
        ], start_new_session=True))
        check("no scan stops", 0.0)
        check("far target capped", 0.2, [2.0, 2.0, 2.0])
        check("approaching target slows", 0.1, [1.0, 1.0, 1.0])
        check("desired gap stops", 0.0, [0.8, 0.8, 0.8])
        check("close obstacle stops", 0.0, [2.0, 0.4, 2.0])
        check("invalid scan stops", 0.0, [math.nan, math.inf, 0.1])
        check("old acquisition timestamp stops", 0.0, [2.0] * 3, stamp_age=1.0)
        check("future acquisition timestamp stops", 0.0, [2.0] * 3, stamp_age=-1.0)
        check("fresh scan recovers", 0.2, [2.0] * 3)
        check("scan loss stops", 0.0, settle=0.6)
        check("moving before controller loss", 0.2, [2.0] * 3)
        import os
        import signal
        os.killpg(controller.pid, signal.SIGTERM)
        controller.wait(timeout=5)
        check("controller loss stops LRC output", 0.0, settle=0.6)
        print("RESULT: 12 passed; no hardware actuation tested")
    finally:
        import os
        import signal
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
