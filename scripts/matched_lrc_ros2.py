#!/usr/bin/env python3
"""Minimal 50 Hz, quiet ROS 2 LRC used only by the matched benchmark."""

import threading
import rclpy
from rclpy.node import Node
from scale_truck_msgs.msg import Lrc2Ocr, Xav2Lrc


class MatchedLrc(Node):
    def __init__(self):
        super().__init__("matched_lrc")
        self._lock = threading.Lock()
        self._latest = None
        self._publisher = self.create_publisher(Lrc2Ocr, "/lrc2ocr_msg", 1)
        self._subscriber = self.create_subscription(
            Xav2Lrc, "/xav2lrc_msg", self._on_command, 1)
        self._timer = self.create_timer(0.02, self._publish)
        self.get_logger().info("matched LRC rate_hz=50 logging=state-changes-only")

    def _on_command(self, command):
        with self._lock:
            self._latest = command

    def _publish(self):
        with self._lock:
            command = self._latest
        if command is None:
            return
        output = Lrc2Ocr()
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


def main():
    rclpy.init()
    node = MatchedLrc()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
