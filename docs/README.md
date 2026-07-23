# Scale Truck Documentation

Start here instead of browsing individual files. Documentation is grouped by purpose so setup instructions, design records, migration history, and project planning are easy to find.

## Start here

1. [Set up and use ROS 2 Humble on the Xavier](setup/environment.md).
2. [Understand the target system architecture](design/architecture.md).
3. [Follow the command-to-actuator path](design/control-pipeline.md).
4. [Check the ROS 2 migration status](migration/checklist.md).
5. [Use the detailed migration guide](migration/guide.md) when porting code.

## Setup and operations

| Document | Use it for |
|---|---|
| [ROS 2 environment](setup/environment.md) | Daily Xavier Docker workflow, builds, terminals, and troubleshooting. |
| [Development options](setup/development-options.md) | Native Ubuntu, development-container, and hardware environment choices. |
| [DDS validation](setup/dds-validation.md) | Confirming ROS 2 discovery and publish/subscribe communication. |

## System design

| Document | Use it for |
|---|---|
| [Architecture](design/architecture.md) | Target and legacy component-level architecture. |
| [Control pipeline](design/control-pipeline.md) | Detailed command flow from high-level control to actuator PWM. |
| [Interfaces and topics](design/interfaces-and-topics.md) | Message mappings, topic names, and interface conventions. |
| [QoS profiles](design/qos-profiles.md) | Reliability and queue-depth decisions by communication path. |
| [Launch and configuration](design/launch-and-configuration.md) | Launch files, YAML, namespaces, and remapping. |
| [Runtime decisions](design/runtime-decisions.md) | ROS 1 replacements and decisions about non-ROS components. |

## Migration reference

| Document | Use it for |
|---|---|
| [Migration checklist](migration/checklist.md) | Current completion status and remaining work. |
| [Migration guide](migration/guide.md) | Detailed ROS 1-to-ROS 2 implementation guidance. |
| [ROS 1 versus ROS 2](migration/ros1-vs-ros2.md) | Conceptual and API differences. |
| [ROS 1 inventory](migration/ros1-inventory.md) | Legacy nodes, topics, messages, dependencies, and hardware behavior. |
| [File map](migration/file-map.md) | Mapping legacy files to their ROS 2 destinations. |
| [Node-port notes](migration/node-port-notes.md) | Scope and status of the initial client-library port. |

## Planning

- [Task tracker](planning/task-tracker.md): milestones, labels, and the initial issue plan.

## Other repository documentation

- [Repository overview](../README.md)
- [ROS 2 workspace](../ros2_ws/README.md)
- [ROS 2 packages](../ros2_ws/src/README.md)
- [Firmware](../firmware/teensy/README.md)
- [Maps](../maps/README.md)
- [Reference material](../references/README.md)
- [Scripts](../scripts/README.md)
- [Tests](../tests/README.md)
