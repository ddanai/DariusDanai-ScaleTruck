#!/usr/bin/env python3
"""Matched-workload ROS 1 controller for the Xavier benchmark."""

import rospy
from sensor_msgs.msg import Image
from scale_truck_control.msg import xav2lrc

from matched_controller_workload import WORKLOAD_VERSION, process_image


class Controller:
    def __init__(self):
        self.passes = rospy.get_param("~workload_passes", 4)
        self.trace_id = 0
        self.publisher = rospy.Publisher("/xav2lrc_msg", xav2lrc, queue_size=1)
        self.subscriber = rospy.Subscriber(
            "/usb_cam/image_raw", Image, self.on_image, queue_size=1,
            buff_size=8 * 1024 * 1024)
        rospy.loginfo("matched workload=%s passes=%d", WORKLOAD_VERSION, self.passes)

    def on_image(self, image):
        steer, velocity, _ = process_image(
            image.data, image.width, image.height, self.passes)
        self.trace_id += 1
        command = xav2lrc()
        command.trace_id = self.trace_id
        command.sensor_stamp = image.header.stamp if image.header.stamp else rospy.Time.now()
        command.steer_angle = steer
        command.cur_dist = 10.0
        command.tar_dist = 0.8
        command.tar_vel = velocity
        command.beta = False
        command.gamma = False
        self.publisher.publish(command)


if __name__ == "__main__":
    rospy.init_node("matched_controller")
    Controller()
    rospy.spin()
