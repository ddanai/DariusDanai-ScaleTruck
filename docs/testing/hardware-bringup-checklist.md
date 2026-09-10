# Hardware bring-up checklist

Use this checklist when connecting the truck or repeating its hardware tests.
Check boxes only for the current run. Earlier evidence is recorded separately
in [September 9 results](../../results/hardware/2026-09-09/README.md).

## Run record

| Item | Fill in |
|---|---|
| Date and operator | |
| Ubuntu/Xavier computer | |
| Repository commit (`git rev-parse HEAD`) | |
| Container/image | `ros2-humble` / `ros2-humble-usb-image` |
| Teensy model and installed firmware | |
| Camera and LiDAR model | Record exact LiDAR variant if known; not yet confirmed |
| Evidence folder / log filenames | |
| Overall result and unresolved issues | |

## 1. Prepare hardware

- [ ] Disconnect motor drive power for sensor and command-processing tests.
- [ ] Verify power and signal connections against the actual hardware pinout.
      Encoder A is configured on Teensy pin 2 and B on pin 3; also verify ground
      and compatible supply/signal voltage. Do not infer wiring from wire colour.
- [ ] Connect camera, LiDAR adapter and Teensy USB before starting the container.
- [ ] Keep the LiDAR scan plane unobstructed and camera lens clear.
- [ ] Close serial monitors and temporary encoder scripts. Only one program
      should read the Teensy port.
- [ ] Record which Teensy firmware is installed. Encoder-test firmware reads
      counts; command-test firmware accepts commands. They are separate programs.

## 2. Check device access

Run on Ubuntu, one command at a time:

```bash
ls -l /dev/serial/by-id/
ls -l /dev/video0
docker start ros2-humble
docker exec ros2-humble ls -l /dev/video0 /dev/ttyUSB0 /dev/ttyACM0
```

- [ ] Camera is visible inside Docker (configured `/dev/video0`).
- [ ] LiDAR adapter is visible inside Docker (previously CP2102 at `/dev/ttyUSB0`).
- [ ] Teensy is visible inside Docker (previously Teensyduino at `/dev/ttyACM0`).

Port numbers can change; confirm device identity using the host's by-id links.
Update sensor/serial configuration when necessary. If a device exists on Ubuntu
but not inside this privileged container, keep it connected and run
`docker restart ros2-humble`, then check again. Restarting stops running nodes.

## 3. Prepare ROS 2

After transferring/pulling the required code changes onto Ubuntu, install
dependencies if needed and build. Run each command separately:

```bash
docker exec -it ros2-humble bash -lc "apt-get update && apt-get install -y python3-serial ros-humble-usb-cam ros-humble-rplidar-ros"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; source /ros2_ws/install/setup.bash; cd /ros2_ws; colcon build --packages-select scale_truck_firmware_bridge scale_truck_bringup"
```

- [ ] Installation succeeds.
- [ ] Build reports `2 packages finished`, with no failed packages.

This build assumes the existing workspace dependencies are already built, as in
the tested container. A fresh workspace requires its full dependency/build setup.

## 4. Start all sensors

Use encoder-test firmware. Stop previous launches before running this in terminal A:

```bash
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; source /ros2_ws/install/setup.bash; ros2 launch scale_truck_bringup sensors.launch.py"
```

- [ ] Camera starts capture.
- [ ] LiDAR reports health OK and starts scanning.
- [ ] Serial bridge reports it opened the Teensy port at 115200 baud.
- [ ] No node exits or repeatedly reports device errors.

Leave terminal A running. This launch disables control nodes and Teensy command
writes. A missing camera calibration file was present in the earlier passing
publication test; record it separately if calibration is required for your work.

## 5. Verify sensor messages

Run the following in terminal B, one at a time. Use Ctrl+C between checks.
Observe frequency for about 30 seconds; save output, not just topic names.

### Camera

```bash
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic hz /usb_cam/image_raw"
```

- [ ] Continuous images received; previous combined result was about 28–29 Hz
      with a configured 30 Hz capture rate. Investigate sustained large drops.
- [ ] If validating image content, view the image and confirm it responds when
      an object moves. Topic frequency alone does not verify image quality.

### LiDAR

```bash
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic hz /scan"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic echo /scan --once --qos-reliability best_effort --full-length"
```

- [ ] Continuous scans received; previous combined result was about 13.7 Hz.
- [ ] Scan contains finite distances within its reported range limits.
- [ ] Move a cardboard target in the scan plane and confirm corresponding
      distances change. Measure from the scanner centre to the target surface.

Some infinity readings are normal; they do not represent measured obstacle
distances. A truncated range array cannot establish that the whole scan is invalid.

### Encoder

```bash
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic echo /motor_encoder/raw"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic hz /motor_encoder/count"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic echo /motor_encoder/delta"
```

- [ ] Turn the shaft by hand: cumulative count changes.
- [ ] Reverse rotation: delta changes sign and direction label changes.
- [ ] Stop rotation: delta becomes zero and cumulative count stays steady.
- [ ] Numeric count publishes at about 4 Hz with the current test firmware.
- [ ] Numeric delta agrees with changes shown in the raw text.

Negative counts are valid. Counts are not calibrated speed; these checks do not
validate metres/second feedback or `/ocr2lrc_msg`.

## 6. Optional evidence recording and restart check

From a terminal inside the container, with ROS sourced, record the active topics
to a new, unused folder under the mounted workspace:

```bash
docker exec -it ros2-humble bash
```

Then, after the container prompt appears, run:

```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
cd /ros2_ws
ros2 bag record -o hardware_sensor_check /usb_cam/image_raw /scan /motor_encoder/raw /motor_encoder/count /motor_encoder/delta
```

Record briefly (images can consume substantial disk space), stop with Ctrl+C,
and inspect with `ros2 bag info hardware_sensor_check`. Choose a new output name
for each run. The folder is saved on the mounted Ubuntu workspace.

- [ ] Save terminal logs or a bag containing each required sensor topic.
- [ ] Stop terminal A with Ctrl+C; restart the same sensor launch.
- [ ] Confirm messages resume and the serial port is released/reopened cleanly.

## 7. Separate ROS 2-to-Teensy command test

This checks command processing, not physical motor/steering motion. It requires
the command-capable firmware, not encoder-only firmware. Do not switch firmware
as an incidental step: record the uploaded version and follow the existing
[Teensy upload guide](../../firmware/teensy/TEENSY_UPLOAD_GUIDE.md).

- [ ] Stop the sensor launch and all serial monitors.
- [ ] Confirm motor and steering actuators are disconnected for this test.
- [ ] Confirm command-capable firmware is installed.

Terminal A, start only the bridge with commands enabled:

```bash
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; source /ros2_ws/install/setup.bash; ros2 run scale_truck_firmware_bridge serial_bridge_node --ros-args -p commands_enabled:=true -p port:=/dev/ttyACM0"
```

Terminal B:

```bash
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; source /ros2_ws/install/setup.bash; ros2 run scale_truck_firmware_bridge ros_command_path_test"
```

- [ ] Test finishes successfully with no failures; save its full summary.
- [ ] Command acceptance and watchdog neutral behavior pass.
- [ ] Disarm behavior passes; stop the bridge after the test.

A service write succeeding is not proof of acceptance; the test checks board
replies. The user previously reported this test passed in milestone work.
The direct [Xavier fixed-command test](../../firmware/teensy/XAVIER_FIXED_COMMAND_TEST.md)
bypasses ROS and is a separate serial-path check.

## 8. Separate actuator checks and shutdown

- [ ] Record the firmware and procedure used for standalone motor validation.
- [ ] Record the firmware and procedure used for standalone steering validation.
- [ ] For powered actuator tests, support the truck with wheels clear, keep the
      steering linkage clear, and have a means to remove actuator power.
- [ ] Verify the relevant test's neutral/stop behavior before ending the test.
- [ ] Stop nodes and monitors; disconnect actuator power before rewiring.
- [ ] Save results and unresolved issues in the run record.

Standalone actuator passes do not prove ROS-controlled physical actuation.
Software watchdog/ESTOP tests do not establish a working physical emergency stop.

## Completion record

| Item | PASS / FAIL / NOT RUN | Evidence |
|---|---|---|
| Device access and build | | |
| Camera publication | | |
| LiDAR publication and finite ranges | | |
| Encoder forward/reverse/stop feedback | | |
| Numeric encoder topics | | |
| Restart repeatability | | |
| Separate ROS command acceptance | | |
| Standalone motor / steering | | |

Mark only the scope actually tested. September 9 evidence confirms combined
sensor publication and changing raw encoder counts; numeric topic capture and
restart repeatability were not recorded. Combined encoder-and-command firmware,
calibrated speed feedback and ROS-driven physical actuation remain separate work.

See [topic definitions](../design/actuator-and-sensor-topics.md) for names,
message fields, units and operating modes.
