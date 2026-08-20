#!/usr/bin/env python3
"""Matched-workload ROS 2 controller for the Xavier benchmark."""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from scale_truck_msgs.msg import Xav2Lrc

from matched_controller_workload import WORKLOAD_VERSION, process_image


class Controller(Node):
    def __init__(self):
        super().__init__("matched_controller")
        self.declare_parameter("workload_passes", 8)
        self.passes = self.get_parameter("workload_passes").value
        self.trace_id = 0
        self.publisher = self.create_publisher(Xav2Lrc, "/xav2lrc_msg", 1)
        self.subscriber = self.create_subscription(
            Image, "/usb_cam/image_raw", self.on_image, qos_profile_sensor_data)
        self.get_logger().info(
            "matched workload={} passes={}".format(WORKLOAD_VERSION, self.passes))

    def on_image(self, image):
        steer, velocity, _ = process_image(
            image.data, image.width, image.height, self.passes)
        self.trace_id += 1
        command = Xav2Lrc()
        command.trace_id = self.trace_id
        command.sensor_stamp = image.header.stamp
        command.steer_angle = steer
        command.cur_dist = 10.0
        command.tar_dist = 0.8
        command.tar_vel = velocity
        command.beta = False
        command.gamma = False
        self.publisher.publish(command)


def main():
    rclpy.init()
    node = Controller()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
