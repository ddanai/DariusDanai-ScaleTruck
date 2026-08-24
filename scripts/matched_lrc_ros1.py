#!/usr/bin/env python3
"""Minimal 50 Hz, quiet ROS 1 LRC used only by the matched benchmark."""

import threading
import rospy
from scale_truck_control.msg import lrc2ocr, xav2lrc


class MatchedLrc:
    def __init__(self):
        self._lock = threading.Lock()
        self._latest = None
        self._publisher = rospy.Publisher("/lrc2ocr_msg", lrc2ocr, queue_size=1)
        self._subscriber = rospy.Subscriber(
            "/xav2lrc_msg", xav2lrc, self._on_command, queue_size=1)
        self._timer = rospy.Timer(rospy.Duration(0.02), self._publish)
        rospy.loginfo("matched LRC rate_hz=50 logging=state-changes-only")

    def _on_command(self, command):
        with self._lock:
            self._latest = command

    def _publish(self, _event):
        with self._lock:
            command = self._latest
        if command is None:
            return
        output = lrc2ocr()
        output.trace_id = command.trace_id
        output.sensor_stamp = command.sensor_stamp
        output.index = 0
        output.steer_angle = command.steer_angle
        output.cur_dist = command.cur_dist
        output.tar_dist = command.tar_dist
        output.tar_vel = command.tar_vel
        output.pred_vel = command.tar_vel
        output.alpha = False
        self._publisher.publish(output)


if __name__ == "__main__":
    rospy.init_node("matched_lrc")
    MatchedLrc()
    rospy.spin()
