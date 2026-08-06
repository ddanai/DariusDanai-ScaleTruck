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
- `analyze_experiment2_ros2_trace_latency.py`: analyzes Experiment 2 ROS 2 bags
  by exact trace ID and sensor acquisition timestamp.
- `analyze_experiment2_ros1_trace_latency.py`: performs the equivalent exact
  trace analysis for Experiment 2 ROS 1 bags in a sourced catkin workspace.
- `experiment2_restamp_ros1_images.py` and
  `experiment2_restamp_ros2_images.py`: relay replayed camera frames to
  `/usb_cam/image_raw` with current timestamps so historical bag stamps are not
  misinterpreted as latency.
- `compare_ros1_ros2_latency.py`: pools saved latency samples, summarizes topic
  timing across runs, and generates the Milestone 4 comparison data and plots.
- Plot generation for jitter, frequency, and command delay.
