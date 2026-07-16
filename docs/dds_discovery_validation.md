# ROS 2 DDS Discovery Validation

ROS 2 does not use `roscore` or a ROS master. Nodes discover each other through DDS, so validation should confirm that ROS 2 nodes can be discovered without starting any ROS 1 master process.

## What This Confirms

- No `roscore` process is required.
- ROS 2 command-line tools can see active ROS 2 nodes.
- Basic publish/subscribe communication works through DDS discovery.
- The configured `ROS_DOMAIN_ID` is visible before testing.

## Local Validation

From an Ubuntu 22.04 + ROS 2 Humble environment:

```bash
source /opt/ros/humble/setup.bash
cd ros2_ws
../scripts/validate_ros2_dds_discovery.sh
```

Expected result:

- The script starts a ROS 2 demo talker.
- `ros2 node list` discovers `/talker`.
- `ros2 topic list` discovers `/chatter`.
- The script exits successfully without starting `roscore`.

## Current Validation Status

Status: pending target ROS 2 environment.

Attempted from the current repository shell on 2026-07-15:

```text
Get-Command ros2
Get-Command bash
```

Result:

- `ros2` was not available in the current shell.
- `bash` was not available in the current shell.
- DDS discovery could not be validated from this Windows shell.

Run the local validation command above from the target Ubuntu + ROS 2 development
environment before checking off the migration checklist item.

## Manual Equivalent

Terminal 1:

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp talker
```

Terminal 2:

```bash
source /opt/ros/humble/setup.bash
ros2 node list
ros2 topic list
```

You should see `/talker` in the node list and `/chatter` in the topic list.

## Network Notes

For same-machine development, DDS discovery should work with the default settings.

For multiple machines:

- Use the same `ROS_DOMAIN_ID` on each machine.
- Confirm multicast is allowed on the network.
- Use `ROS_LOCALHOST_ONLY=1` only for local-only tests.
- Add DDS vendor-specific configuration later only if remote discovery is unreliable.
