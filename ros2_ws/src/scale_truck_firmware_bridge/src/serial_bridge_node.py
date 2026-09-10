#!/usr/bin/env python3

import threading
import time
import re

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from scale_truck_msgs.msg import Lrc2Ocr
from std_msgs.msg import String, Int32
from std_srvs.srv import Trigger

try:
    import serial
except ImportError:  # pragma: no cover - handled at runtime on ROS hosts
    serial = None


COMMAND_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
)

FEEDBACK_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
)


class SerialBridgeNode(Node):
    """Bridge ROS 2 command/feedback topics to the low-level controller serial link."""

    def __init__(self):
        super().__init__("serial_bridge_node")

        self.port = self.declare_parameter("port", "/dev/ttyACM0").value
        self.baud = self.declare_parameter("baud", 115200).value
        self.timeout = self.declare_parameter("timeout", 1.0).value
        self.command_topic = self.declare_parameter("command_topic", "lrc2ocr_msg").value
        self.commands_enabled = self.declare_parameter("commands_enabled", True).value

        self.serial = None
        self.serial_lock = threading.Lock()
        self.running = True

        self.command_sub = self.create_subscription(
            Lrc2Ocr, self.command_topic, self.command_callback, COMMAND_QOS
        ) if self.commands_enabled else None
        self.encoder_raw_pub = self.create_publisher(String, "motor_encoder/raw", FEEDBACK_QOS)
        self.encoder_count_pub = self.create_publisher(Int32, "motor_encoder/count", FEEDBACK_QOS)
        self.encoder_delta_pub = self.create_publisher(Int32, "motor_encoder/delta", FEEDBACK_QOS)
        self.serial_status_pub = self.create_publisher(
            String, "firmware/serial_status", FEEDBACK_QOS
        )
        self.arm_service = self.create_service(Trigger, "firmware/arm", self.arm_callback)
        self.disarm_service = self.create_service(
            Trigger, "firmware/disarm", self.disarm_callback
        )
        self.clear_service = self.create_service(
            Trigger, "firmware/clear_faults", self.clear_faults_callback
        )
        self.status_service = self.create_service(
            Trigger, "firmware/status", self.status_callback
        )

        self.open_serial()
        self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.read_thread.start()

    def destroy_node(self):
        self.running = False
        if self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
        if self.serial is not None:
            try:
                if self.commands_enabled:
                    self.serial.write(b"DISARM\n")
                    self.serial.flush()
            except serial.SerialException:
                pass
            self.serial.close()
        super().destroy_node()

    def open_serial(self):
        if serial is None:
            self.get_logger().error("python3-serial is not installed; serial bridge is disabled")
            return

        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=self.timeout)
            self.get_logger().info(f"Opened {self.port} at {self.baud} baud")
            time.sleep(2.0)
            self.serial.reset_input_buffer()
            if self.commands_enabled:
                self.write_command("HEARTBEAT OFF")
        except serial.SerialException as exc:
            self.get_logger().error(f"Could not open serial port {self.port}: {exc}")

    def command_callback(self, msg):
        if self.serial is None:
            return

        # Use the same newline-delimited command path exercised by the fixed
        # command acceptance test. ROS publications refresh the firmware's
        # watchdog; if they stop for 250 ms, the Teensy forces neutral.
        command = f"CMD {msg.tar_vel:.6f} {msg.steer_angle:.6f}"
        self.write_command(command)

    def write_command(self, command):
        if self.serial is None or not self.commands_enabled:
            return False
        try:
            with self.serial_lock:
                self.serial.write((command + "\n").encode("ascii"))
                self.serial.flush()
            return True
        except serial.SerialException as exc:
            self.get_logger().error(f"Serial command write failed: {exc}")
            return False

    def trigger_command(self, command, response):
        response.success = self.write_command(command)
        response.message = (
            f"Sent {command}; check Teensy status for acceptance"
            if response.success
            else f"Could not send {command}"
        )
        return response

    def arm_callback(self, request, response):
        del request
        return self.trigger_command("ARM", response)

    def disarm_callback(self, request, response):
        del request
        return self.trigger_command("DISARM", response)

    def clear_faults_callback(self, request, response):
        del request
        return self.trigger_command("CLEAR", response)

    def status_callback(self, request, response):
        del request
        return self.trigger_command("STATUS", response)

    def read_loop(self):
        while self.running and rclpy.ok():
            if self.serial is None:
                time.sleep(0.1)
                continue

            try:
                data = self.serial.readline()
            except serial.SerialException as exc:
                self.get_logger().error(f"Serial read failed: {exc}")
                time.sleep(0.1)
                continue
            if not data:
                continue
            line = data.decode("ascii", errors="replace").strip()
            status_msg = String()
            status_msg.data = line
            self.serial_status_pub.publish(status_msg)
            self.publish_encoder(line)
            if line.startswith("ERR"):
                self.get_logger().warning(f"Teensy: {line}")

    def publish_encoder(self, line):
        match = re.fullmatch(
            r"ENCODER count=(-?\d+) delta=(-?\d+) direction=(FORWARD|REVERSE|STOP)", line
        )
        if match is None:
            return
        count, delta = int(match[1]), int(match[2])
        if not all(-(2**31) <= value < 2**31 for value in (count, delta)):
            return
        direction = "FORWARD" if delta > 0 else "REVERSE" if delta < 0 else "STOP"
        if match[3] != direction:
            return
        raw_msg, count_msg, delta_msg = String(), Int32(), Int32()
        raw_msg.data, count_msg.data, delta_msg.data = line, count, delta
        self.encoder_raw_pub.publish(raw_msg)
        self.encoder_count_pub.publish(count_msg)
        self.encoder_delta_pub.publish(delta_msg)


def main(args=None):
    rclpy.init(args=args)
    node = SerialBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
