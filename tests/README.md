# Tests

Test plans, fixtures, and integration notes.

Planned coverage:

- ROS 2 package build checks.
- Topic communication smoke tests.
- Serial protocol parser tests.
- PID bench-test logs.
- Hardware bring-up checklist validation.
- `test_ros1_latency.py`: unit tests for ROS 1 bag latency correlation and
  timing statistics (does not require ROS).
- `test_ros2_latency.py`: unit tests for rosbag2 SQLite reading, analysis
  windows, pipeline latency correlation, frequency, and error reporting.
