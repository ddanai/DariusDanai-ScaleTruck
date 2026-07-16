# ROS 1 to ROS 2 File Map

This map identifies where each important part of the imported ROS 1 reference project should land in the ROS 2 workspace.

ROS 1 reference root:

```text
references/ros1_scale_truck_control
```

ROS 2 workspace root:

```text
ros2_ws/src
```

## Package Destination Summary

| ROS 2 Package / Area | Purpose |
|----------------------|---------|
| `scale_truck_msgs` | Custom message, service, and action interfaces shared by other packages. |
| `scale_truck_control` | High-level control, lane detection, object/obstacle processing, LRC behavior, and reusable control support code. |
| `scale_truck_bringup` | Launch files and runtime YAML configuration. |
| `scale_truck_firmware_bridge` | ROS 2 side of the Teensy/OpenCR serial bridge and hardware interface configuration. |
| `scale_truck_description` | Robot description, frame definitions, RViz files, and vehicle/track description assets. |
| `scale_truck_telemetry` | Digital twin, logging, monitoring, and external telemetry integration. |
| `firmware/teensy` | Project-owned low-level firmware derived from the ROS 1 OpenCR firmware concepts. |
| `maps` | Physical track drawings, map assets, and generated digital map files. |
| `docs` | Migration notes, legacy component decisions, and design records. |

## Source and Header Files

| ROS 1 Source | ROS 2 Destination | Action |
|--------------|-------------------|--------|
| `nodes/control_node.cpp` | `ros2_ws/src/scale_truck_control/src/control_node.cpp` | Port from `roscpp` executable entry point to `rclcpp`. |
| `nodes/lrc_node.cpp` | `ros2_ws/src/scale_truck_control/src/lrc_node.cpp` | Port from `roscpp` executable entry point to `rclcpp`. |
| `src/ScaleTruckController.cpp` | `ros2_ws/src/scale_truck_control/src/ScaleTruckController.cpp` | Port main high-level controller implementation. |
| `include/scale_truck_control/ScaleTruckController.hpp` | `ros2_ws/src/scale_truck_control/include/scale_truck_control/ScaleTruckController.hpp` | Port controller class declaration and ROS 2 interfaces. |
| `src/lrc.cpp` | `ros2_ws/src/scale_truck_control/src/lrc.cpp` | Port LRC command arbitration and resiliency behavior. |
| `include/lrc/lrc.hpp` | `ros2_ws/src/scale_truck_control/include/scale_truck_control/lrc.hpp` | Move under package include namespace and port ROS 2 types. |
| `src/lane_detect.cpp` | `ros2_ws/src/scale_truck_control/src/lane_detect.cpp` | Port lane detection support code; keep algorithm separate from ROS bindings where possible. |
| `include/lane_detect/lane_detect.hpp` | `ros2_ws/src/scale_truck_control/include/scale_truck_control/lane_detect.hpp` | Move under package include namespace. |
| `src/object_detect.cpp` | `ros2_ws/src/scale_truck_control/src/object_detect.cpp` | Port object/obstacle processing support code. |
| `include/object_detect/object_detect.hpp` | `ros2_ws/src/scale_truck_control/include/scale_truck_control/object_detect.hpp` | Move under package include namespace. |
| `src/sock_udp.cpp` | `ros2_ws/src/scale_truck_control/src/sock_udp.cpp` or `scale_truck_telemetry` | Decide whether UDP resiliency remains in control or moves to telemetry/coordination. |
| `include/sock_udp/sock_udp.hpp` | `ros2_ws/src/scale_truck_control/include/scale_truck_control/sock_udp.hpp` or `scale_truck_telemetry` | Keep only if raw UDP remains part of ROS 2 design. |
| `src/zmq_class.cpp` | `ros2_ws/src/scale_truck_telemetry/src/zmq_class.cpp` or legacy docs | Decide whether ZeroMQ is still required for ADDT/telemetry. |
| `include/zmq_class/zmq_class.h` | `ros2_ws/src/scale_truck_telemetry/include/scale_truck_telemetry/zmq_class.hpp` or legacy docs | Port only if ZeroMQ remains in the ROS 2 architecture. |

## Custom Messages

ROS 1 message files should move to `scale_truck_msgs/msg` and use ROS 2 interface naming conventions.

| ROS 1 Message | ROS 2 Destination | Action |
|---------------|-------------------|--------|
| `msg/lane.msg` | `ros2_ws/src/scale_truck_msgs/msg/Lane.msg` | Rename to CamelCase and update package references. |
| `msg/lane_coef.msg` | `ros2_ws/src/scale_truck_msgs/msg/LaneCoef.msg` | Rename to CamelCase and update nested `Lane` references. |
| `msg/xav2lrc.msg` | `ros2_ws/src/scale_truck_msgs/msg/Xav2Lrc.msg` | Rename to CamelCase; review field names for readability. |
| `msg/lrc2xav.msg` | `ros2_ws/src/scale_truck_msgs/msg/Lrc2Xav.msg` | Rename to CamelCase; review field names for readability. |
| `msg/lrc2ocr.msg` | `ros2_ws/src/scale_truck_msgs/msg/Lrc2Ocr.msg` | Rename to CamelCase; keep serial bridge compatibility in mind. |
| `msg/ocr2lrc.msg` | `ros2_ws/src/scale_truck_msgs/msg/Ocr2Lrc.msg` | Rename to CamelCase; keep serial bridge compatibility in mind. |
| `msg/scale_truck_control_msgs.zip` | `docs/` or omit | Legacy generated/message archive; do not use as a ROS 2 source interface. |

See [ROS 2 Interfaces and Topic Naming](ros2_interfaces_and_topics.md) for the migrated interface and topic mapping.

## Launch Files

ROS 1 XML launch files should become ROS 2 Python launch files in `scale_truck_bringup`.

| ROS 1 Launch | ROS 2 Destination | Action |
|--------------|-------------------|--------|
| `launch/LV.launch` | `ros2_ws/src/scale_truck_bringup/launch/lv.launch.py` | Convert leader vehicle bringup to ROS 2 launch. |
| `launch/FV1.launch` | `ros2_ws/src/scale_truck_bringup/launch/fv1.launch.py` | Convert follower 1 bringup to ROS 2 launch. |
| `launch/FV2.launch` | `ros2_ws/src/scale_truck_bringup/launch/fv2.launch.py` | Convert follower 2 bringup to ROS 2 launch. |
| `launch/laneCam_LV.launch` | `ros2_ws/src/scale_truck_bringup/launch/lane_cam_lv.launch.py` | Convert lane-camera variant if still needed. |
| `launch/laneCam_FV1.launch` | `ros2_ws/src/scale_truck_bringup/launch/lane_cam_fv1.launch.py` | Convert lane-camera variant if still needed. |
| `launch/laneCam_FV2.launch` | `ros2_ws/src/scale_truck_bringup/launch/lane_cam_fv2.launch.py` | Convert lane-camera variant if still needed. |
| `launch/lane_cam.launch` | `ros2_ws/src/scale_truck_bringup/launch/lane_cam.launch.py` | Convert reusable camera launch or replace with included node actions. |
| `launch/jpeg.launch` | `ros2_ws/src/scale_truck_bringup/launch/jpeg.launch.py` | Convert only if JPEG/image transport path is still used. |

## Configuration Files

Runtime configuration should move to `scale_truck_bringup/config` unless it is clearly owned by one package.

| ROS 1 Config | ROS 2 Destination | Action |
|--------------|-------------------|--------|
| `config/LV.yaml` | `ros2_ws/src/scale_truck_bringup/config/lv.yaml` | Convert to ROS 2 node parameter structure. |
| `config/FV1.yaml` | `ros2_ws/src/scale_truck_bringup/config/fv1.yaml` | Convert to ROS 2 node parameter structure. |
| `config/FV2.yaml` | `ros2_ws/src/scale_truck_bringup/config/fv2.yaml` | Convert to ROS 2 node parameter structure. |
| `config/config.yaml` | `ros2_ws/src/scale_truck_bringup/config/perception.yaml` or `scale_truck_control/config/control.yaml` | Split if it contains mixed perception/control settings. |
| `config/lrc.yaml` | `ros2_ws/src/scale_truck_bringup/config/lrc.yaml` or `scale_truck_control/config/lrc.yaml` | Convert LRC parameters and remaps. |
| `config/laser_filter.yaml` | `ros2_ws/src/scale_truck_bringup/config/laser_filter.yaml` | Reuse if ROS 2 `laser_filters` accepts the same structure; otherwise update. |

See [ROS 2 Launch and Runtime Configuration](ros2_launch_config_notes.md) for the converted bringup files.

## Firmware and Hardware Bridge

The ROS 1 OpenCR firmware should not be copied directly into `ros2_ws`. Use it to implement the project-owned Teensy/OpenCR firmware and ROS 2 bridge.

| ROS 1 Firmware / Hardware File | ROS 2 Destination | Action |
|--------------------------------|-------------------|--------|
| `etc/OpenCR/LV/LV.ino` | `firmware/teensy/lv_controller/` or `firmware/teensy/src/` | Port PID, actuator, encoder, and feedback behavior to selected Teensy/OpenCR firmware layout. |
| `etc/OpenCR/FV1/FV1.ino` | `firmware/teensy/fv1_controller/` or `firmware/teensy/src/` | Port follower-specific behavior if separate firmware remains necessary. |
| `etc/OpenCR/FV1/FV1_LRT.ino` | `firmware/teensy/fv1_lrt_controller/` or legacy docs | Evaluate whether this variant is still needed. |
| `etc/OpenCR/FV2/FV2.ino` | `firmware/teensy/fv2_controller/` or `firmware/teensy/src/` | Port follower-specific behavior if separate firmware remains necessary. |
| `etc/OpenCR/scale_truck_control_msgs.zip` | `docs/` or omit | Legacy ROS 1 generated message archive; do not use as ROS 2 source. |
| ROS 1 `rosserial_python` launch usage | `ros2_ws/src/scale_truck_firmware_bridge/src/serial_bridge_node.py` | Replace with ROS 2 serial bridge or micro-ROS. |
| Serial bridge config | `ros2_ws/src/scale_truck_firmware_bridge/config/serial.yaml` | Define port, baud rate, timeouts, packet format, and watchdog behavior. |

## Track, Map, and Description Assets

| ROS 1 Asset | ROS 2 Destination | Action |
|-------------|-------------------|--------|
| `etc/Track/Virtual_Track_1.0.png` | `maps/reference/Virtual_Track_1.0.png` | Copy as source map/reference asset. |
| `etc/Track/drawing.png` | `maps/reference/drawing.png` | Copy as source map/reference asset. |
| `etc/Track/*.pdf` | `maps/reference/` | Copy useful track drawings for documentation and map reconstruction. |
| `etc/Track/*.SLDPRT`, `etc/Track/*.SLDDRW` | `maps/cad/` | Keep CAD source assets if project needs mechanical/map reference files. |
| Vehicle geometry inferred from code/config | `ros2_ws/src/scale_truck_description/urdf/` | Create URDF/Xacro rather than copying from ROS 1, since no URDF exists in the reference repo. |
| Visualization configs | `ros2_ws/src/scale_truck_description/rviz/` | Create new ROS 2 RViz configs as needed. |

## Non-ROS Support Components

These files are part of the ROS 1 reference project but should not automatically be ported into the ROS 2 workspace.

| ROS 1 Component | ROS 2 Destination | Action |
|-----------------|-------------------|--------|
| `etc/Controller/Controller/` | `docs/legacy_controller.md`, external tool, or future app package | Decide whether the Qt controller is still needed. |
| `etc/Controller/build-Controller-Desktop-Debug/` | Omit | Generated build output; do not migrate. |
| `etc/Controller/crc/` | `docs/legacy_crc_udp.md`, `scale_truck_telemetry`, or omit | Evaluate CRC/UDP tool behavior before porting. |
| Generated binaries and object files under `etc/Controller/` | Omit | Build artifacts; do not migrate. |
| `README.md`, `TREE.md` from reference repo | `docs/ros1_inventory.md` and migration docs | Keep as reference only; do not move into ROS 2 packages. |

## Build Metadata

| ROS 1 File | ROS 2 Destination | Action |
|------------|-------------------|--------|
| `package.xml` | Existing ROS 2 package manifests | Use as dependency reference only; do not copy. |
| `CMakeLists.txt` | Existing ROS 2 package CMake files | Use as build dependency/reference only; do not copy. |

## Migration Order From This Map

1. Migrate `msg/` files into `scale_truck_msgs`.
2. Update package dependencies based on the actual ported interfaces and libraries.
3. Port `scale_truck_control` nodes and support libraries.
4. Convert launch/config files into `scale_truck_bringup`.
5. Implement the firmware bridge and firmware protocol changes.
6. Decide the fate of UDP/ZMQ, Qt controller, CRC tools, and track assets.
7. Add build, launch, and hardware validation around each migrated slice.

See [ROS 2 Node Port Notes](ros2_node_port_notes.md) for the first ROS 2 client-library port status.
