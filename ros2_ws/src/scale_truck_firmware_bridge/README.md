# scale_truck_firmware_bridge

The serial bridge reads Teensy replies and publishes encoder measurements.
It accepts the tested format `ENCODER count=277 delta=-18 direction=REVERSE`.

| Topic | Type | Meaning |
|---|---|---|
| `/motor_encoder/raw` | `std_msgs/msg/String` | Complete valid encoder line |
| `/motor_encoder/count` | `std_msgs/msg/Int32` | Signed cumulative count since firmware startup |
| `/motor_encoder/delta` | `std_msgs/msg/Int32` | Count change during the firmware report interval |
| `/firmware/serial_status` | `std_msgs/msg/String` | Serial replies, including command acknowledgments |
| `/lrc2ocr_msg` | `scale_truck_msgs/msg/Lrc2Ocr` | Commands, when commands_enabled is true |

Encoder test firmware reports every 250 ms (about 4 Hz). Count and delta are
counts, not speed. Encoder topics use reliable, volatile QoS with depth 5.
Malformed and inconsistent lines remain visible on serial_status but are not
published as encoder measurements.

The existing command path sends `CMD <tar_vel> <steer_angle>`. Services send
ARM, DISARM, CLEAR and STATUS; service success means the write succeeded, not
that the firmware accepted it. Check serial_status for acceptance.

Main firmware 0.2.0 now combines real encoder counts with ESC/servo command
outputs, using these same protocols. Its default OPEN_LOOP mode maps the speed
field to restricted throttle because encoder calibration is unknown. The old
encoder-only test firmware still cannot accept actuator commands. No
`/ocr2lrc_msg` publisher is advertised: calibrated speed and the legacy observer
input scaling are not established. See [firmware commissioning](../../../firmware/teensy/README.md).

## Build on Ubuntu

Transfer these updated repository files to the Ubuntu checkout first. Windows
workspace edits do not automatically update the Ubuntu machine.

```bash
docker exec -it ros2-humble bash -lc "apt-get update && apt-get install -y python3-serial ros-humble-usb-cam ros-humble-rplidar-ros"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; cd /ros2_ws; colcon build --packages-select scale_truck_firmware_bridge scale_truck_bringup"
```

## Launch all three sensors

Close the temporary encoder script, serial monitor and previous sensor launches.
Only one process should own the Teensy serial port. Use the tested encoder
firmware (A pin 2, B pin 3), with motor drive power disconnected for hand testing.

```bash
docker exec ros2-humble ls -l /dev/video0 /dev/ttyUSB0 /dev/ttyACM0
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; source /ros2_ws/install/setup.bash; ros2 launch scale_truck_bringup sensors.launch.py"
```

This starts camera, LiDAR and the encoder bridge with control nodes and command
writes disabled. The bridge sends no startup/shutdown commands in this mode.
Command services return failure. Device settings live in bringup/config.
If Docker cannot see a connected device, restart the container with devices
attached; that stops all processes in it.

In a second terminal, run each separately, pressing Ctrl+C between checks:

```bash
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic hz /usb_cam/image_raw"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic hz /scan"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic echo /motor_encoder/raw"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic hz /motor_encoder/count"
```

Integrated launch acceptance checklist (still requires Ubuntu hardware testing):

- [ ] Camera publishes continuously (previous individual test: 29–30 Hz).
- [ ] LiDAR publishes finite distances (previous individual test: 13.2 Hz).
- [ ] Encoder publishes at about 4 Hz and responds to both rotation directions.
- [ ] Stopped encoder has steady count and zero delta.
- [ ] No repeated serial errors; stop and restart the launch successfully.

The user previously passed the separate ROS command acceptance test. Repeating
it requires command-capable firmware and commands_enabled=true. This sensor
launch does not establish calibrated closed-loop speed control.

## Local verification

`python -m unittest discover -s tests -p test_encoder_bridge.py` exercises
publication, malformed input rejection and command suppression using mocked ROS
dependencies. A real ROS build and hardware run are still required on Ubuntu.

