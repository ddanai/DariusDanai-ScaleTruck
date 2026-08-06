#!/usr/bin/env python3
"""Restamp replayed ROS 1 images for the Experiment 2 latency benchmark."""

import rospy
from sensor_msgs.msg import Image


class ImageRestamper:
    def __init__(self):
        input_topic = rospy.get_param("~input_topic", "/experiment2/input_image")
        output_topic = rospy.get_param("~output_topic", "/usb_cam/image_raw")
        self.publisher = rospy.Publisher(output_topic, Image, queue_size=1)
        self.subscriber = rospy.Subscriber(
            input_topic, Image, self.callback, queue_size=1,
            buff_size=16 * 1024 * 1024)

    def callback(self, message):
        message.header.stamp = rospy.Time.now()
        self.publisher.publish(message)


if __name__ == "__main__":
    rospy.init_node("experiment2_image_restamper")
    ImageRestamper()
    rospy.spin()
