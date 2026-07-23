# ROS 2 Quality-of-Service Profiles

This document records the first QoS assignment for the scale truck ROS 2 migration.

## QoS Rules

| Path | Topics | QoS | Reason |
|------|--------|-----|--------|
| High-level command | `xav2lrc_msg`, `lrc2ocr_msg` | Reliable, volatile, keep last 1 | Commands should arrive, but stale commands should not queue up behind newer commands. |
| Feedback | `lrc2xav_msg`, `ocr2lrc_msg` | Reliable, volatile, keep last 5 | Feedback should usually be delivered, with a small buffer for scheduling jitter. |
| Camera image | `usb_cam/image_raw` | Sensor data QoS | Fresh images matter more than reliable delivery of old frames. |
| LiDAR scan | `scan`, `scan_filtered` | Sensor data QoS | Fresh scans matter more than replaying old scans. |
| Lane output | `lane_msg` | Best effort, volatile, keep last 1 | Lane coefficients are continuously refreshed; consumers should use the newest value. |
| Obstacle topics | `raw_obstacles`, `tracked_obstacles` | Sensor data or best effort, keep last 1 | Final profile depends on the ROS 2 obstacle detector replacement. |
| Telemetry/logging | Future telemetry topics | Reliable, volatile, keep last 10 | Telemetry should tolerate small bursts without disturbing command paths. |

## Implemented Profiles

C++ helper profiles live in:

```text
ros2_ws/src/scale_truck_control/include/scale_truck_control/qos.hpp
```

The firmware bridge mirrors the command and feedback profiles in:

```text
ros2_ws/src/scale_truck_firmware_bridge/src/serial_bridge_node.py
```

## Future Review

Revisit QoS after hardware testing. In particular:

- Emergency stop may need its own reliable profile and a separate topic.
- If command loss is observed, add heartbeat/watchdog behavior rather than increasing queue depth.
- If camera/LiDAR subscribers are incompatible with sensor-data QoS, adjust only that edge rather than changing command QoS.
