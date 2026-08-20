#!/usr/bin/env python3
"""ROS-independent deterministic image/control workload used by both benchmarks."""


WORKLOAD_VERSION = "fnv1a-strided-v1"


def process_image(data, width, height, passes=8):
    """Return deterministic steering and velocity values from an image payload.

    The integer-only loop is deliberately shared by ROS 1 and ROS 2. Sampling keeps
    the benchmark affordable on Xavier while still scaling with image size.
    """
    if passes < 1:
        raise ValueError("passes must be at least 1")
    view = memoryview(data)
    if not view:
        return 0.0, 0.0, 0
    stride = max(1, len(view) // 4096)
    value = 2166136261
    for pass_index in range(passes):
        salt = (pass_index + 1) * 16777619
        for index in range(pass_index % stride, len(view), stride):
            value ^= (view[index] + salt + index) & 0xFF
            value = (value * 16777619) & 0xFFFFFFFF
    steer = ((value % 6001) - 3000) / 100.0
    target_velocity = 0.30 + ((value >> 16) % 21) / 100.0
    return steer, target_velocity, value
