# ROS 2 Migration Checklist

## Repository Setup

- [x] Create new repository independent of the ROS 1 reference repo.
- [x] Add ROS 2 workspace structure.
- [x] Add development environment instructions.
- [x] Add issue templates and task tracker plan.
- [x] Create GitHub repository and push initial commit.
- [x] Create Week 1 GitHub issues.

## Core ROS Migration

- [x] Set up the ROS 2 workspace and package structure.
- [x] Migrate package metadata and build configuration from ROS 1 to ROS 2.
- [x] Import the original ROS 1 reference code for migration review.
- [ ] Map ROS 1 source files, headers, launch files, config, firmware, and assets to their ROS 2 package destinations.
- [ ] Migrate custom messages, services, actions, and topic naming conventions.
- [ ] Port ROS 1 nodes and reusable C++ support libraries to ROS 2 client libraries.
- [ ] Migrate launch and runtime configuration.
- [ ] Migrate parameter handling, namespaces, and remapping behavior.
- [ ] Replace ROS 1-only bridges and middleware assumptions with ROS 2-compatible equivalents.
- [ ] Decide whether to port, replace, or drop non-ROS support components from the reference project.
- [ ] Remove ROS 1 master startup assumptions from migrated launch, config, and runtime docs.
- [ ] Review and assign QoS settings for major communication paths.
- [ ] Validate ROS 2 DDS discovery in the target development environment.
- [ ] Validate that the migrated ROS 2 graph starts, communicates, and shuts down correctly.

## Dependency Migration

- [ ] Migrate core ROS dependencies from ROS 1 packages to ROS 2 equivalents.
- [ ] Replace `usb_cam` with a ROS 2-compatible camera driver.
- [ ] Replace or port `rplidar_ros`.
- [ ] Replace or port `obstacle_detector`.
- [ ] Replace or port `laser_filters`.
- [ ] Verify ROS 2 `cv_bridge` and OpenCV compatibility.
- [ ] Verify ROS 2 `image_transport`, `sensor_msgs`, `geometry_msgs`, and `std_msgs` usage.
- [ ] Decide how to handle Boost, OpenCV, ZeroMQ, cppzmq, pthread, and raw UDP dependencies.
- [ ] Replace `rosserial` with a Teensy serial bridge or micro-ROS if appropriate.

### `rosserial` Migration Note

In the ROS 1 reference stack, `rosserial_python/serial_node.py` bridges normal ROS topics to the OpenCR microcontroller over USB serial:

```text
ROS 1 computer <-> /dev/ttyACM0 at 57600 baud <-> OpenCR firmware
```

The launch files start the bridge with:

```xml
<node pkg="rosserial_python" type="serial_node.py" name="serial_node">
  <param name="port" value="/dev/ttyACM0"/>
  <param name="baud" value="57600"/>
</node>
```

This lets the OpenCR subscribe to `/lrc2ocr_msg` and publish `/ocr2lrc_msg` as if it were a ROS node. For ROS 2, do not assume `rosserial` will be available. Prefer one of these replacements:

- Custom ROS 2 serial bridge node: simplest path for a Teensy-based controller.
- micro-ROS: useful if the microcontroller should behave like a ROS 2 node directly.

The migration should preserve the same logical command and feedback path even if the transport changes:

```text
ROS 2 control node -> low-level command topic -> serial/micro-ROS transport -> Teensy/OpenCR
Teensy/OpenCR -> feedback transport -> ROS 2 feedback topic -> control node
```

## Related Validation Docs

- [ROS 2 DDS Discovery Validation](dds_discovery_validation.md)

## Control and Hardware

- [ ] Define ROS 2 command, feedback, perception, safety, and telemetry topics.
- [ ] Port high-level scale truck control behavior.
- [ ] Port lane detection and object/obstacle processing behavior.
- [ ] Port LRC command arbitration, resiliency, and vehicle coordination behavior.
- [ ] Implement or adapt the Teensy/OpenCR serial protocol.
- [ ] Add throttle PID controller.
- [ ] Add steering PID controller.
- [ ] Add watchdog, emergency stop, saturation, and command timeout handling.
- [ ] Decide whether the Qt controller and CRC/UDP tools should be ported, replaced, or documented as legacy-only.
- [ ] Migrate useful track, map, and calibration assets into the project-owned map/description structure.
- [ ] Validate bench tests before vehicle tests.

## Testing and Demonstration

- [ ] Add build, lint, and package validation checks for the ROS 2 workspace.
- [ ] Add unit or component tests for migrated message conversions and control logic.
- [ ] Add launch smoke tests for the migrated ROS 2 stack.
- [ ] Add hardware-in-the-loop checks for serial bridge and PID feedback.
- [ ] Add latency instrumentation scripts.
- [ ] Add test logs and plotting scripts.
- [ ] Build physical map definitions.
- [ ] Create ADDT telemetry interface.
- [ ] Record final demo and results.
