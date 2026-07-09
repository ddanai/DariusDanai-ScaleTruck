# ROS 1 vs ROS 2

This document explains the main differences between ROS 1 and ROS 2, with notes on what those differences mean for the scale truck project.

## Short Version

ROS 1 is a mature robotics middleware built around a central `roscore` process, the `catkin` build system, XML launch files, and client libraries such as `rospy` and `roscpp`.

ROS 2 redesigns the ROS architecture for newer robotics systems. It removes the central master, uses DDS for discovery and communication, supports quality-of-service policies, improves multi-robot and networked deployments, and uses the `ament` / `colcon` build workflow with `rclpy` and `rclcpp`.

For this repository, ROS 2 is the target platform. The original scale truck project is a ROS 1 reference, but new packages, launch files, and hardware bridges should be written for ROS 2.

## Core Differences

| Area | ROS 1 | ROS 2 | Why It Matters |
|------|-------|-------|----------------|
| Process discovery | Requires `roscore` / ROS master | No master; nodes discover each other through DDS | ROS 2 nodes can start in any order and do not depend on one central registry. |
| Communication middleware | ROS-specific TCPROS / UDPROS | DDS-based middleware | ROS 2 gains configurable reliability, durability, and discovery behavior. |
| Build system | `catkin_make`, `catkin build` | `colcon build` with `ament_cmake` or `ament_python` | Package manifests, CMake files, and build commands must change during migration. |
| C++ client library | `roscpp` | `rclcpp` | Node classes, publishers, subscribers, parameters, and logging use different APIs. |
| Python client library | `rospy` | `rclpy` | Python nodes must be rewritten around `rclpy.node.Node`. |
| Launch files | Mostly XML `.launch` files | Python `.launch.py` files, with XML/YAML also supported in some cases | ROS 2 launch files are more programmable and explicit. |
| Parameters | Global parameter server through master | Parameters belong to individual nodes | Each ROS 2 node declares and owns its parameters. |
| Quality of Service | Limited transport tuning | Built-in QoS profiles | Sensor data, commands, and telemetry can choose different reliability and history behavior. |
| Multi-robot support | Possible but awkward | Better native support with namespaces, domains, and DDS | Useful for future multi-truck experiments or remote monitoring. |
| Real-time support | Limited | Improved design for real-time use cases | Helpful when separating high-level ROS logic from low-level Teensy PID control. |
| Security | No built-in security model | DDS-Security support through SROS 2 | Important for networked robots, though not required for the first scale truck prototype. |
| Lifecycle management | Informal node startup/shutdown patterns | Managed lifecycle nodes available | Useful for sensors, safety-critical components, and controlled startup sequences. |

## Architecture Differences

### ROS 1

ROS 1 systems depend on a central ROS master. Nodes register with the master, then use the master to find publishers, subscribers, and services. After discovery, the nodes communicate directly.

Typical ROS 1 startup:

```bash
roscore
roslaunch scale_truck_control LV.launch
```

This works well for many robots, but the master is a single required process. If it is missing or misconfigured, nodes cannot discover each other.

### ROS 2

ROS 2 removes the master. Nodes discover each other through DDS. In a simple local setup, this usually works automatically. In more complex network setups, DDS settings such as domain IDs, multicast behavior, and middleware implementation may need configuration.

Typical ROS 2 startup:

```bash
ros2 launch scale_truck_control lv.launch.py
```

No separate `roscore` command is required.

## Communication and QoS

ROS 2's biggest practical change is Quality of Service. QoS controls how messages are delivered. This is especially useful because not every topic has the same needs.

For example:

| Topic Type | Recommended ROS 2 QoS | Reason |
|------------|-----------------------|--------|
| Camera frames | Best effort, small queue | Dropping an old frame is better than blocking on stale image data. |
| LiDAR scans | Best effort or sensor-data QoS | Fresh scans matter more than guaranteed delivery of every old scan. |
| Steering/throttle commands | Reliable, small queue | Commands should arrive, but stale commands should not pile up. |
| Emergency stop | Reliable, transient local if latched behavior is needed | Safety messages should be delivered predictably. |
| Telemetry/logging | Reliable or best effort depending on bandwidth | Useful data should be captured without disrupting control. |

ROS 1 has queue sizes and transport hints, but ROS 2 makes these delivery choices part of the normal topic contract.

## Build and Package Differences

ROS 1 packages commonly use:

```bash
catkin_make
source devel/setup.bash
```

ROS 2 packages commonly use:

```bash
colcon build --symlink-install
source install/setup.bash
```

Package dependencies also change:

| ROS 1 Dependency | ROS 2 Equivalent |
|------------------|------------------|
| `catkin` | `ament_cmake` or `ament_python` |
| `roscpp` | `rclcpp` |
| `rospy` | `rclpy` |
| `message_generation` | `rosidl_default_generators` |
| `message_runtime` | `rosidl_default_runtime` |

## Node API Differences

### Python

ROS 1:

```python
import rospy

rospy.init_node("example_node")
pub = rospy.Publisher("/example", String, queue_size=10)
rospy.spin()
```

ROS 2:

```python
import rclpy
from rclpy.node import Node

class ExampleNode(Node):
    def __init__(self):
        super().__init__("example_node")
        self.pub = self.create_publisher(String, "/example", 10)

rclpy.init()
node = ExampleNode()
rclpy.spin(node)
rclpy.shutdown()
```

### C++

ROS 1:

```cpp
ros::init(argc, argv, "example_node");
ros::NodeHandle nh;
auto pub = nh.advertise<std_msgs::String>("/example", 10);
ros::spin();
```

ROS 2:

```cpp
rclcpp::init(argc, argv);
auto node = std::make_shared<rclcpp::Node>("example_node");
auto pub = node->create_publisher<std_msgs::msg::String>("/example", 10);
rclcpp::spin(node);
rclcpp::shutdown();
```

## Launch Differences

ROS 1 launch files are usually XML:

```xml
<launch>
  <node pkg="scale_truck_control" type="LRC" name="LRC" />
</launch>
```

ROS 2 launch files are commonly Python:

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="scale_truck_control",
            executable="lrc_node",
            name="lrc",
        )
    ])
```

Python launch files make conditional startup, parameter composition, substitutions, and reusable launch descriptions easier to express.

## Parameters

In ROS 1, parameters are stored on the parameter server and are often loaded globally:

```bash
rosparam load config/LV.yaml
```

In ROS 2, parameters are attached to nodes. Nodes normally declare the parameters they expect before reading them:

```python
self.declare_parameter("steering_gain", 0.5)
gain = self.get_parameter("steering_gain").value
```

This makes parameter ownership clearer, but it also means migration must identify which node owns each setting.

## Hardware Integration Differences

The original scale truck ROS 1 stack used `rosserial_python` to communicate with low-level controller hardware. ROS 2 does not use the same `rosserial` workflow as the default path.

For this project, the preferred ROS 2 approach is:

1. Keep low-level PID control on the Teensy firmware.
2. Use a ROS 2 serial bridge node on the main computer.
3. Publish and subscribe to ROS 2 messages on one side of the bridge.
4. Send compact serial packets to the Teensy on the other side.

This keeps hard real-time motor behavior off the main ROS graph while still exposing commands and feedback to ROS 2.

## Migration Impact for This Repository

The scale truck project should treat ROS 1 as the reference design and ROS 2 as the implementation target.

Important migration tasks:

- Replace `roscore` and ROS 1 launch assumptions with ROS 2 launch files.
- Convert `catkin` packages to `ament_cmake` or `ament_python`.
- Rewrite `rospy` nodes using `rclpy`.
- Rewrite `roscpp` nodes using `rclcpp`.
- Rename and regenerate custom messages using ROS 2 conventions.
- Replace `rosserial_python` with a ROS 2 serial bridge or micro-ROS integration.
- Choose QoS settings for camera, LiDAR, command, safety, and telemetry topics.
- Validate DDS discovery on the target computer and any remote monitoring machines.

## When ROS 1 May Still Be Useful

ROS 1 is still useful as a reference when:

- Reading the original scale truck implementation.
- Understanding the existing topic graph and message flow.
- Comparing expected behavior during migration.
- Porting algorithms that do not depend heavily on ROS APIs.

However, new code in this repository should avoid adding ROS 1-only dependencies unless the team explicitly decides to preserve a compatibility layer.

## Related Documentation

- [ROS 1 Inventory](ros1_inventory.md)
- [ROS 2 Migration Checklist](ros2_migration_checklist.md)
- [ROS 1 to ROS 2 Migration Guide](ros2_migration_guide.md)
- [System Architecture](architecture.md)
