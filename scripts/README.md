# Scripts

Utility scripts for setup, validation, latency profiling, log collection, and plotting.

Scripts:

- Environment validation.
- `validate_ros2_dds_discovery.sh`: confirms ROS 2 node/topic discovery works without `roscore`.
- `analyze_ros1_latency.py`: calculates ROS 1 bag pipeline latency, publishing
  frequency, and jitter. See
  [`docs/testing/ros1-latency-baseline.md`](../docs/testing/ros1-latency-baseline.md).
- `analyze_ros2_latency.py`: calculates the equivalent metrics directly from a
  rosbag2 SQLite directory or `.db3` file. See
  [`docs/testing/ros2-latency-test.md`](../docs/testing/ros2-latency-test.md).
- `record_xavier_resources.sh`: records per-process CPU and memory plus Xavier
  power, ROS/RMW, and network conditions for a labeled test run.
- `analyze_ros2_trace_latency.py`: matches controller and actuator commands by
  exact trace ID and calculates latency from the sensor acquisition timestamp.
- `compare_ros1_ros2_latency.py`: pools saved latency samples, summarizes topic
  timing across runs, and generates the Milestone 4 comparison data and plots.
- Plot generation for jitter, frequency, and command delay.
