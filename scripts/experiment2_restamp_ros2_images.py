#!/usr/bin/env python3
"""Restamp replayed ROS 2 images for the Experiment 2 latency benchmark."""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class ImageRestamper(Node):
    def __init__(self):
        super().__init__("experiment2_image_restamper")
        self.declare_parameter("input_topic", "/experiment2/input_image")
        self.declare_parameter("output_topic", "/usb_cam/image_raw")
        input_topic = self.get_parameter("input_topic").value
        output_topic = self.get_parameter("output_topic").value
        self.publisher = self.create_publisher(
            Image, output_topic, qos_profile_sensor_data)
        self.subscription = self.create_subscription(
            Image, input_topic, self.callback, qos_profile_sensor_data)

    def callback(self, message):
        message.header.stamp = self.get_clock().now().to_msg()
        self.publisher.publish(message)


def main():
    rclpy.init()
    node = ImageRestamper()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
