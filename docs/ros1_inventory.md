# ROS 1 Inventory

This inventory starts from the public reference repository `HyeonGyu-Lee/scale_truck_control`.

## Known Package Metadata

- Package name: `scale_truck_control`
- Build tool: `catkin`
- Version: `0.1.0`
- Core dependencies:
  - `roscpp`
  - `rospy`
  - `std_msgs`
  - `message_generation`
  - `message_runtime`
  - `obstacle_detector`
  - `geometry_msgs`

## Reference Runtime Dependencies

- ROS 1 Melodic
- OpenCV 4.4.0 with CUDA options
- ZeroMQ / cppzmq
- `usb_cam`
- `rplidar_ros`
- `obstacle_detector`
- `laser_filters`
- `vision_opencv` / `cv_bridge`
- `rosserial_arduino`

## Week 1 Inventory Tasks

- Identify every ROS 1 node and launch file in the reference implementation.
- Record publishers, subscribers, services, actions, parameters, and custom messages.
- Map each hardware interface to the corresponding ROS topic or serial protocol.
- Document command flow from high-level control to steering and throttle actuation.
- Mark each dependency as `keep`, `replace`, `port`, or `remove`.

## Open Questions

- Which ROS 2 distribution will run on the final vehicle hardware?
- Will the low-level controller be Teensy-only, or does OpenCR compatibility matter?
- Which sensors are physically available for the capstone vehicle?

