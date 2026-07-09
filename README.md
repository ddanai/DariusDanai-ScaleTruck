# Scale Truck ROS 2 Control

ROS 2-based control stack for a physical scale truck capstone project. This repository is a new implementation that references the original ROS 1 project at https://github.com/HyeonGyu-Lee/scale_truck_control while targeting ROS 2, Teensy low-level PID control, physical test maps, and Autonomous Driving Digital Twin integration.

## Goals

- Migrate the ROS 1 scale-truck architecture to ROS 2.
- Implement low-level Teensy PID control for throttle and steering.
- Integrate sensors, actuators, safety constraints, and telemetry.
- Build repeatable physical test maps and matching digital representations.
- Stream physical truck state into the ADDT framework for physical-twin demos.

## Repository Layout

```text
.
├── .devcontainer/          # Containerized ROS 2 development environment
├── .github/                # Issue templates and project tracking helpers
├── docs/                   # Architecture, setup, migration, and tracker docs
├── firmware/teensy/        # Teensy low-level controller firmware
├── maps/                   # Physical map specs and digital map assets
├── ros2_ws/src/            # ROS 2 packages for truck control
├── scripts/                # Setup, validation, and experiment scripts
└── tests/                  # Test assets and integration test notes
```

## Quick Start

1. Install Docker Desktop or a native Ubuntu 22.04 + ROS 2 Humble environment.
2. Open this folder in VS Code and reopen in the dev container, or follow [Development Environment](docs/development_environment.md).
3. Build the ROS 2 workspace:

```bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

4. Review the Week 1 documents:

- [ROS 1 Inventory](docs/ros1_inventory.md)
- [ROS 1 vs ROS 2](docs/ros1_vs_ros2.md)
- [ROS 2 Migration Checklist](docs/ros2_migration_checklist.md)
- [Task Tracker](docs/task_tracker.md)

## Reference Project

The original ROS 1 project documents this hardware and software baseline:

- Jetson AGX Xavier with JetPack 4.5.1 / Ubuntu 18.04
- ROS 1 Melodic
- OpenCV 4.4.0 with CUDA
- ZeroMQ / cppzmq
- OpenCR low-level controller
- USB camera and RPLidar A3

This repository should preserve useful concepts from that project, but new code should be written and documented for the selected ROS 2 platform.
