# ROS 2 Migration Checklist

## Repository Setup

- [x] Create new repository independent of the ROS 1 reference repo.
- [x] Add ROS 2 workspace structure.
- [x] Add development environment instructions.
- [x] Add issue templates and task tracker plan.
- [x] Create GitHub repository and push initial commit.
- [x] Create Week 1 GitHub issues.

## Core ROS Migration

- [ ] Create ROS 2 package skeletons under `ros2_ws/src`.
- [ ] Replace `catkin` build files with `ament_cmake` or `ament_python`.
- [ ] Convert ROS 1 publishers/subscribers to ROS 2 nodes.
- [ ] Convert launch files to ROS 2 Python launch files.
- [ ] Convert parameter handling to ROS 2 parameter APIs.
- [ ] Verify topic communication with test publishers/subscribers.

## Dependency Migration

- [ ] Replace `usb_cam` with a ROS 2-compatible camera driver.
- [ ] Replace or port `rplidar_ros`.
- [ ] Replace or port `obstacle_detector`.
- [ ] Replace or port `laser_filters`.
- [ ] Verify ROS 2 `cv_bridge` and OpenCV compatibility.
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

## Control and Hardware

- [ ] Define ROS 2 command and feedback topics.
- [ ] Implement Teensy serial protocol.
- [ ] Add throttle PID controller.
- [ ] Add steering PID controller.
- [ ] Add watchdog, emergency stop, saturation, and command timeout handling.
- [ ] Validate bench tests before vehicle tests.

## Testing and Demonstration

- [ ] Add latency instrumentation scripts.
- [ ] Add test logs and plotting scripts.
- [ ] Build physical map definitions.
- [ ] Create ADDT telemetry interface.
- [ ] Record final demo and results.
