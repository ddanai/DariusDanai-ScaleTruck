# Scripts

Utility scripts for setup, validation, latency profiling, log collection, and plotting.

Scripts:

- Environment validation.
- `validate_ros2_dds_discovery.sh`: confirms ROS 2 node/topic discovery works without `roscore`.
- `analyze_ros1_latency.py`: calculates ROS 1 bag pipeline latency, publishing
  frequency, and jitter. See
  [`docs/testing/ros1-latency-baseline.md`](../docs/testing/ros1-latency-baseline.md).
- Plot generation for jitter, frequency, and command delay.
