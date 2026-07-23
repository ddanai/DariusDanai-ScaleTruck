# ROS 2 Humble Environment

This guide explains the everyday ROS 2 Humble workflow for the NVIDIA Xavier. ROS 2 runs in the persistent Docker container named `ros2-humble`, and the workspace is shared between the Xavier host and the container.

## Xavier Docker workflow

### 1. Start ROS 2

Begin at the Xavier host prompt:

```text
krg@ubuntu:~$
```

Start and attach to the persistent ROS 2 Humble container:

```bash
docker start -ai ros2-humble
```

The environment is ready when the prompt changes to:

```text
root@ubuntu:/ros2_ws#
```

### 2. Verify the environment

Run these commands inside the container:

```bash
echo $ROS_DISTRO
pwd
```

Expected output:

```text
humble
/ros2_ws
```

### 3. Put ROS packages in the workspace

Package source code belongs in this directory inside the container:

```text
/ros2_ws/src
```

The same shared directory on the Xavier host is:

```text
/home/krg/ros2_humble_ws/src
```

Files edited on the Xavier host appear immediately inside the container.

### 4. Install package dependencies

After adding or downloading a package, run these commands inside the container:

```bash
cd /ros2_ws
rosdep install --from-paths src --ignore-src -r -y
```

### 5. Build the workspace

Inside the container, run:

```bash
cd /ros2_ws
colcon build --symlink-install
```

A successful build ends with a summary showing no failed packages.

### 6. Activate the built packages

After every build, run:

```bash
source /ros2_ws/install/setup.bash
```

Repeat this command in every newly opened container terminal.

### 7. Run a ROS node

Use this general command:

```bash
ros2 run PACKAGE_NAME EXECUTABLE_NAME
```

For example, start the demo talker:

```bash
ros2 run demo_nodes_cpp talker
```

Stop a running node by pressing `Ctrl+C`.

### 8. Open a second ROS terminal

Leave the first terminal and its container session running. Open another Ubuntu terminal on the Xavier host and run:

```bash
docker exec -it ros2-humble bash
```

In the second container terminal, activate the base ROS environment and the workspace:

```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
cd /ros2_ws
```

Run a second node, such as the demo listener:

```bash
ros2 run demo_nodes_cpp listener
```

### 9. Inspect the ROS system

Useful commands inside the container include:

```bash
ros2 node list
ros2 topic list
ros2 topic echo /chatter
ros2 topic info /chatter
```

### 10. Finish working

Stop active nodes in each terminal by pressing `Ctrl+C`.

Exit each secondary container terminal:

```bash
exit
```

In the original container terminal, run:

```bash
exit
```

Exiting the original terminal stops the container but preserves the shared workspace and packages installed in the named container.

## Quick reference

Start and attach to the ROS 2 environment:

```bash
docker start -ai ros2-humble
```

Open another terminal in the running environment:

```bash
docker exec -it ros2-humble bash
```

Build and activate the workspace:

```bash
cd /ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Stop the container while preserving its state:

```bash
exit
```

> [!WARNING]
> Do not run `docker rm ros2-humble`. Removing the container deletes packages installed inside it. Files under `/home/krg/ros2_humble_ws` remain because that directory is stored on the Xavier host.
