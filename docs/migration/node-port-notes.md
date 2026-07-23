# ROS 2 Node-Port Notes

This note records the first ROS 2 client-library port of the ROS 1 runtime nodes and support code.

## Ported Files

| ROS 1 Reference | ROS 2 File |
|-----------------|------------|
| `nodes/control_node.cpp` | `ros2_ws/src/scale_truck_control/src/control_node.cpp` |
| `nodes/lrc_node.cpp` | `ros2_ws/src/scale_truck_control/src/lrc_node.cpp` |
| `include/lrc/lrc.hpp` | `ros2_ws/src/scale_truck_control/include/scale_truck_control/lrc.hpp` |
| `src/lrc.cpp` | `ros2_ws/src/scale_truck_control/src/lrc.cpp` |
| `include/sock_udp/sock_udp.hpp` | `ros2_ws/src/scale_truck_control/include/scale_truck_control/sock_udp.hpp` |
| `src/sock_udp.cpp` | `ros2_ws/src/scale_truck_control/src/sock_udp.cpp` |
| `include/scale_truck_control/ScaleTruckController.hpp` | `ros2_ws/src/scale_truck_control/include/scale_truck_control/ScaleTruckController.hpp` |
| `src/ScaleTruckController.cpp` | `ros2_ws/src/scale_truck_control/src/ScaleTruckController.cpp` |

## Scope

- `roscpp` node entry points are now `rclcpp` executables.
- ROS 1 custom message usage now targets `scale_truck_msgs`.
- LRC subscriptions, publishers, timer loop, velocity observer, mode logic, and UDP send/receive helper are ported into ROS 2 structure.
- The high-level controller has ROS 2 publishers/subscribers and preserves the `/xav2lrc_msg`, `/lrc2xav_msg`, and `/lane_msg` interface contract.

## Remaining Behavior Work

The original high-level controller depended on ROS 1 `obstacle_detector`, `cv_bridge`, OpenCV CUDA lane processing, and ZeroMQ coordination. Those pieces remain covered by later checklist items:

- Dependency migration.
- Lane detection and object/obstacle processing behavior.
- LRC/vehicle coordination behavior validation.
- Launch/config/parameter migration.
- QoS review and runtime graph validation.
