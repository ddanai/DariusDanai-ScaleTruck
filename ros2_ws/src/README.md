# ROS 2 Packages

ROS 2 packages for the scale truck control stack live in this directory.

Package layout:

- `scale_truck_bringup`: launch files and runtime configuration.
- `scale_truck_control`: high-level control and closed-loop logic.
- `scale_truck_description`: robot description and frames.
- `scale_truck_firmware_bridge`: Teensy serial bridge.
- `scale_truck_msgs`: custom messages, services, and actions.
- `scale_truck_telemetry`: ADDT telemetry bridge.

These package directories are scaffolded first so migration work has clear ownership. Package metadata, build files, and executable code are tracked as separate migration tasks.

