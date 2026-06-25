# ROS 2 Migration Checklist

## Repository Setup

- [x] Create new repository independent of the ROS 1 reference repo.
- [x] Add ROS 2 workspace structure.
- [x] Add development environment instructions.
- [x] Add issue templates and task tracker plan.
- [ ] Create GitHub repository and push initial commit.
- [ ] Create Week 1 GitHub issues.

## Core ROS Migration

- [ ] Create ROS 2 package skeletons under `ros2_ws/src`.
- [ ] Replace `catkin` build files with `ament_cmake` or `ament_python`.
- [ ] Convert ROS 1 publishers/subscribers to ROS 2 nodes.
- [ ] Convert launch files to ROS 2 Python launch files.
- [ ] Convert parameter handling to ROS 2 parameter APIs.
- [ ] Verify topic communication with test publishers/subscribers.

## Dependency Migration

- [ ] Replace `usb_cam` with a ROS 2-compatible camera driver.
- [ ] Replace or port `rplidar_ros`.
- [ ] Replace or port `obstacle_detector`.
- [ ] Replace or port `laser_filters`.
- [ ] Verify ROS 2 `cv_bridge` and OpenCV compatibility.
- [ ] Replace `rosserial` with a Teensy serial bridge or micro-ROS if appropriate.

## Control and Hardware

- [ ] Define ROS 2 command and feedback topics.
- [ ] Implement Teensy serial protocol.
- [ ] Add throttle PID controller.
- [ ] Add steering PID controller.
- [ ] Add watchdog, emergency stop, saturation, and command timeout handling.
- [ ] Validate bench tests before vehicle tests.

## Testing and Demonstration

- [ ] Add latency instrumentation scripts.
- [ ] Add test logs and plotting scripts.
- [ ] Build physical map definitions.
- [ ] Create ADDT telemetry interface.
- [ ] Record final demo and results.

