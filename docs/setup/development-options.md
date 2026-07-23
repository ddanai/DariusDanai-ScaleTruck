# Development Environment Options

## Recommended Baseline

Use ROS 2 Humble on Ubuntu 22.04 for development unless hardware constraints require a Jetson-specific ROS 2 distribution. Humble is a stable long-term support target and gives the project a modern ROS 2 API surface for migration work.

The original reference repository used ROS 1 Melodic on Ubuntu 18.04 with JetPack 4.5.1. Treat that setup as a reference baseline for hardware assumptions, not the target environment for new code.

## ROS 2 Humble Installation Notes

- ROS 2 Humble is now the baseline environment for the migration work. If the install is on a Windows host, use WSL2 with Ubuntu 22.04 so the Linux-based ROS 2 tooling behaves the same way as the target development environment.
- After installation, confirm the shell can find the distribution before building anything:

```bash
source /opt/ros/humble/setup.bash
ros2 --version
colcon --version
```

- If the workspace is being validated on the Xavier/Jetson target, repeat the same source step there and verify `ros2 node list` and `ros2 topic list` after the first bring-up test.

## Option A: Dev Container

Prerequisites:

- Docker Desktop
- VS Code with Dev Containers extension

Steps:

```bash
git clone <new-repo-url>
cd scaletruck
code .
```

Then choose "Reopen in Container" from VS Code.

Build the workspace:

```bash
cd /workspace/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Validate ROS 2 DDS discovery:

```bash
../scripts/validate_ros2_dds_discovery.sh
```

## Option B: Native Ubuntu 22.04

Install ROS 2 Humble:

```bash
sudo apt update
sudo apt install locales software-properties-common
sudo add-apt-repository universe
sudo apt update
sudo apt install ros-humble-desktop python3-colcon-common-extensions python3-rosdep
sudo rosdep init
rosdep update
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Build the workspace:

```bash
cd ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Validate ROS 2 DDS discovery:

```bash
../scripts/validate_ros2_dds_discovery.sh
```

## Hardware Notes

- Teensy firmware development should be documented under `firmware/teensy`.
- Serial defaults are listed in `.env.example`.
- Jetson-specific deployment notes should be added once the final JetPack and ROS 2 distro target are confirmed.
