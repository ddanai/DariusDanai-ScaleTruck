# DDS Discovery Validation

ROS 2 does not use `roscore` or a ROS master. Nodes discover each other through DDS, so validation should confirm that ROS 2 nodes can be discovered without starting any ROS 1 master process.

## What This Confirms

- No `roscore` process is required.
- ROS 2 command-line tools can see active ROS 2 nodes.
- Basic publish/subscribe communication works through DDS discovery.
- The configured `ROS_DOMAIN_ID` is visible before testing.

## Validation on Ubuntu 22.04

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

## Validation on the Xavier Target

To validate DDS discovery on the actual Xavier hardware, connect to the Xavier over SSH and run the check in a bash shell. This does not require the repository to be present on the Xavier; it only requires a working ROS 2 installation and access to the ROS 2 environment setup script.

If ROS 2 is already installed, the simplest validation is to use the built-in demo nodes:

```bash
ssh <user>@<xavier-hostname> 'bash -lc "source /opt/ros/humble/setup.bash; ros2 run demo_nodes_cpp talker"'
```

In a second shell, run:

```bash
ssh <user>@<xavier-hostname> 'bash -lc "source /opt/ros/humble/setup.bash; ros2 node list; ros2 topic list"'
```

Expected result:

- `ros2 node list` shows `/talker`.
- `ros2 topic list` shows `/chatter`.
- DDS discovery works without starting `roscore`.

If the Xavier returns `ros2: command not found`, ROS 2 is not installed or the setup script is not available at `/opt/ros/humble/setup.bash`.

If you want to run the repository validation script instead, it can be executed from any machine that has the repository available, but it is not required for a basic Xavier DDS check.

Run this validation from the Xavier's Ubuntu environment before marking the migration checklist item as complete.

## Current Validation Status

Status: validated in the Docker ROS 2 environment.

Verified on 2026-07-23 in a ROS 2 Docker shell:

```bash
source /opt/ros/humble/setup.bash
which ros2
ros2 topic list
ros2 node list
```

Observed results:

- `which ros2` returned `/opt/ros/humble/bin/ros2`.
- `ros2 topic list` showed `/chatter`, `/parameter_events`, and `/rosout`.
- `ros2 node list` showed `/talker`.
- The demo talker was stopped with Ctrl-C to confirm the process could be shut down cleanly.

This confirms basic ROS 2 DDS discovery and pub/sub behavior for the validated environment.

Attempted from the current repository shell on 2026-07-15:

```text
Get-Command ros2
Get-Command bash
```

Result:

- `ros2` was not available in the current shell.
- `bash` was not available in the current shell.
- DDS discovery could not be validated from this Windows shell.

Attempted over SSH on the Xavier target on 2026-07-16:

```text
ls /opt/ros
```

Result:

- The Xavier currently only reported `noetic`.
- `ros2` was not available in the SSH session.
- ROS 2 must be installed on the Xavier before DDS discovery can be validated there.

Run the local validation command above from the target Ubuntu + ROS 2 development
environment before checking off the migration checklist item.

