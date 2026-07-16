# ROS 2 Interfaces and Topic Naming

This document records the initial ROS 2 interface migration from the ROS 1 reference project. The first port keeps the original message fields and topic names so behavior can be compared directly during migration.

## Interface Package

Custom interfaces live in:

```text
ros2_ws/src/scale_truck_msgs
```

The ROS 1 reference package was `scale_truck_control`. In ROS 2, shared interfaces move to `scale_truck_msgs` so control, firmware bridge, telemetry, and bringup packages can depend on the same message definitions without depending on the control package implementation.

## Message Type Mapping

| ROS 1 Type | ROS 2 Type | Notes |
|------------|------------|-------|
| `scale_truck_control/lane` | `scale_truck_msgs/msg/Lane` | Same fields, renamed to ROS 2 CamelCase file/type convention. |
| `scale_truck_control/lane_coef` | `scale_truck_msgs/msg/LaneCoef` | Same fields, nested type updated from `lane` to `Lane`. |
| `scale_truck_control/xav2lrc` | `scale_truck_msgs/msg/Xav2Lrc` | Same fields for Xavier-to-LRC command compatibility. |
| `scale_truck_control/lrc2xav` | `scale_truck_msgs/msg/Lrc2Xav` | Same velocity feedback field. |
| `scale_truck_control/lrc2ocr` | `scale_truck_msgs/msg/Lrc2Ocr` | Same low-level command fields for bridge/firmware compatibility. |
| `scale_truck_control/ocr2lrc` | `scale_truck_msgs/msg/Ocr2Lrc` | Same low-level feedback fields. |

## Services and Actions

The imported ROS 1 reference project does not define custom services or actions. The ROS 2 packages keep `srv/` and `action/` directories available for future safety, calibration, or mission-control interfaces.

## Initial Topic Mapping

The first ROS 2 port should preserve these topic names to reduce migration risk and make side-by-side behavior comparison easier.

| ROS 1 Topic | ROS 1 Type | ROS 2 Topic | ROS 2 Type | Role |
|-------------|------------|-------------|------------|------|
| `/lane_msg` | `scale_truck_control/lane_coef` | `/lane_msg` | `scale_truck_msgs/msg/LaneCoef` | Lane polynomial output. |
| `/xav2lrc_msg` | `scale_truck_control/xav2lrc` | `/xav2lrc_msg` | `scale_truck_msgs/msg/Xav2Lrc` | High-level command from scale truck controller to LRC. |
| `/lrc2xav_msg` | `scale_truck_control/lrc2xav` | `/lrc2xav_msg` | `scale_truck_msgs/msg/Lrc2Xav` | LRC feedback to high-level controller. |
| `/lrc2ocr_msg` | `scale_truck_control/lrc2ocr` | `/lrc2ocr_msg` | `scale_truck_msgs/msg/Lrc2Ocr` | Low-level command from LRC to firmware bridge. |
| `/ocr2lrc_msg` | `scale_truck_control/ocr2lrc` | `/ocr2lrc_msg` | `scale_truck_msgs/msg/Ocr2Lrc` | Low-level feedback from firmware bridge to LRC. |
| `/usb_cam/image_raw` | `sensor_msgs/Image` | `/usb_cam/image_raw` | `sensor_msgs/msg/Image` | Camera input; driver may remap this later. |
| `/scan` | `sensor_msgs/LaserScan` | `/scan` | `sensor_msgs/msg/LaserScan` | LiDAR input. |
| `/raw_obstacles` | `obstacle_detector/Obstacles` | `/raw_obstacles` | Replacement TBD | Raw obstacle input if `obstacle_detector` is ported/replaced. |
| `/tracked_obstacles` | `obstacle_detector/Obstacles` | `/tracked_obstacles` | Replacement TBD | Tracked obstacle input used by runtime config. |

## Naming Rules for the Port

- Message files use ROS 2 CamelCase names: `LaneCoef.msg`, not `lane_coef.msg`.
- Generated C++ includes use snake_case: `scale_truck_msgs/msg/lane_coef.hpp`.
- Generated C++ types use the `scale_truck_msgs::msg` namespace.
- Generated Python imports use `from scale_truck_msgs.msg import LaneCoef`.
- Topic names stay compatible with the ROS 1 reference during the first migration pass.
- Cleaner topic names, such as `/control/xavier_to_lrc` or `/firmware/feedback`, can be introduced later through remapping once behavior is validated.

