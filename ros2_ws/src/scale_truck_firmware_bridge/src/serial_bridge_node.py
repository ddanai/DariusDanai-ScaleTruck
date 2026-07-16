#!/usr/bin/env python3

import struct
import threading
import time

import rclpy
from rclpy.node import Node

from scale_truck_msgs.msg import Lrc2Ocr, Ocr2Lrc

try:
    import serial
except ImportError:  # pragma: no cover - handled at runtime on ROS hosts
    serial = None


class SerialBridgeNode(Node):
    """Bridge ROS 2 command/feedback topics to the low-level controller serial link."""

    COMMAND_FORMAT = "<ifffff?"
    FEEDBACK_FORMAT = "<ff"

    def __init__(self):
        super().__init__("serial_bridge_node")

        self.port = self.declare_parameter("port", "/dev/ttyACM0").value
        self.baud = self.declare_parameter("baud", 115200).value
        self.timeout = self.declare_parameter("timeout", 1.0).value
        self.command_topic = self.declare_parameter("command_topic", "lrc2ocr_msg").value
        self.feedback_topic = self.declare_parameter("feedback_topic", "ocr2lrc_msg").value

        self.serial = None
        self.running = True

        self.command_sub = self.create_subscription(
            Lrc2Ocr, self.command_topic, self.command_callback, 10
        )
        self.feedback_pub = self.create_publisher(Ocr2Lrc, self.feedback_topic, 10)

        self.open_serial()
        self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.read_thread.start()

    def destroy_node(self):
        self.running = False
        if self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
        if self.serial is not None:
            self.serial.close()
        super().destroy_node()

    def open_serial(self):
        if serial is None:
            self.get_logger().error("python3-serial is not installed; serial bridge is disabled")
            return

        try:
            self.serial = serial.Serial(self.port, self.baud, timeout=self.timeout)
            self.get_logger().info(f"Opened {self.port} at {self.baud} baud")
        except serial.SerialException as exc:
            self.get_logger().error(f"Could not open serial port {self.port}: {exc}")

    def command_callback(self, msg):
        if self.serial is None:
            return

        packet = struct.pack(
            self.COMMAND_FORMAT,
            msg.index,
            msg.steer_angle,
            msg.cur_dist,
            msg.tar_dist,
            msg.tar_vel,
            msg.pred_vel,
            msg.alpha,
        )
        self.serial.write(packet)

    def read_loop(self):
        packet_size = struct.calcsize(self.FEEDBACK_FORMAT)
        while self.running and rclpy.ok():
            if self.serial is None:
                time.sleep(0.1)
                continue

            data = self.serial.read(packet_size)
            if len(data) != packet_size:
                continue

            cur_vel, u_k = struct.unpack(self.FEEDBACK_FORMAT, data)
            msg = Ocr2Lrc()
            msg.cur_vel = cur_vel
            msg.u_k = u_k
            self.feedback_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SerialBridgeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
