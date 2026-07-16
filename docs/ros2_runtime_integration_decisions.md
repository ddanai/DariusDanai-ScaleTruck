# ROS 2 Runtime Integration Decisions

This document records the migration decisions for ROS 1 runtime assumptions and non-ROS support components.

## Parameter, Namespace, and Remapping Rules

- Runtime YAML uses ROS 2 `ros__parameters`.
- Node names are explicit: `scale_truck_control_node`, `lrc_node`, and `serial_bridge_node`.
- Topic parameters use relative topic names, such as `xav2lrc_msg`, so launch namespaces and remappings work.
- `vehicle.launch.py` exposes a `namespace` launch argument for multi-truck graphs.
- `vehicle.launch.py` exposes common topic remapping launch arguments:
  - `xav2lrc_topic`
  - `lrc2xav_topic`
  - `lrc2ocr_topic`
  - `ocr2lrc_topic`
  - `lane_topic`
  - `camera_topic`
  - `tracked_obstacles_topic`
  - `scan_topic`
  - `scan_filtered_topic`

Example:

```bash
ros2 launch scale_truck_bringup lv.launch.py namespace:=lv
```

Example with legacy global topic compatibility:

```bash
ros2 launch scale_truck_bringup lv.launch.py \
  xav2lrc_topic:=/xav2lrc_msg \
  lrc2xav_topic:=/lrc2xav_msg
```

## ROS 1 Bridge and Middleware Replacements

| ROS 1 Component | ROS 2 Decision |
|-----------------|----------------|
| `roscore` / ROS master | Removed. ROS 2 DDS discovery is used. |
| `<rosparam>` launch loading | Replaced by ROS 2 `parameters=[...]` launch entries and `ros__parameters` YAML. |
| `rosserial_python/serial_node.py` | Replaced by `scale_truck_firmware_bridge/serial_bridge_node`. |
| ROS 1 package-local custom messages | Replaced by shared `scale_truck_msgs` interfaces. |
| ZeroMQ command coordination | Not ported into core control. Re-evaluate under telemetry/ADDT integration. |
| raw UDP resiliency helper | Ported into `scale_truck_control` for LRC compatibility. |

## Non-ROS Support Component Decisions

| Reference Component | Decision |
|---------------------|----------|
| Qt desktop controller under `etc/Controller/Controller` | Legacy-only for now. Do not port into `ros2_ws` until a new UI requirement exists. |
| CRC/UDP helper under `etc/Controller/crc` | Legacy-only for now. LRC UDP compatibility is handled in `scale_truck_control`; future CRC behavior should be redesigned as telemetry or coordination work. |
| Generated Qt build directory and object files | Drop. These are build artifacts. |
| ZeroMQ helper class | Hold. Do not port until ADDT telemetry requirements prove it is still needed. |
| OpenCR firmware sketches | Use as firmware reference only. Project-owned firmware belongs under `firmware/teensy`. |
| Track/CAD assets | Keep as source assets under `maps` when the map/description migration step starts. |

## ROS Master Startup Assumptions

Migrated launch files do not start `roscore`, do not call ROS 1 `roslaunch`, and do not load ROS 1 `<rosparam>` blocks. Startup is through ROS 2 launch:

```bash
ros2 launch scale_truck_bringup lv.launch.py
```

