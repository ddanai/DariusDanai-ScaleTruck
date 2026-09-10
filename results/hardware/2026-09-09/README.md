# ROS 2 sensor and Teensy communication results

Test date: September 9, 2026 (America/Los_Angeles). The integrated launch log
uses September 10, 2026 UTC. Tests were run by the user on Ubuntu in the
`ros2-humble` Docker container. This report reviews their supplied terminal
output; the hardware was not operated from the Windows workspace.

## Outcome

**PASS for the tested driver/bridge scope:** the permanent sensor launch starts
the USB camera, LiDAR and Teensy serial bridge, and ROS 2 subscribers receive
data from all three. Encoder counts respond to hand rotation and stop changing
when the shaft stops.

Together with the user's previously reported successful ROS command-path test,
this supports completion of the deliverable **“ROS 2 drivers or bridge nodes
for sensors and Teensy communication.”** Command acceptance was tested
separately with different Teensy firmware, not during this sensor launch.

## Recorded results

| Check | Observed result | What it shows |
|---|---|---|
| Build | `2 packages finished [5.35s]` for firmware_bridge and bringup, pasted in conversation | Both updated packages built on Ubuntu |
| Integrated launch | Camera, rplidar_node and serial_bridge_node started | The permanent launch starts all three processes |
| Camera `/usb_cam/image_raw` | Final reported average 28.356 Hz; displayed averages 26.915–29.391 Hz | Images are continuously received by ROS 2 |
| LiDAR `/scan` | Final reported average 13.671 Hz; displayed averages 13.603–13.673 Hz | Scans are continuously received by ROS 2 |
| Teensy connection | Bridge opened `/dev/ttyACM0` at 115200 baud | The permanent bridge opens the board's serial connection |
| Encoder `/motor_encoder/raw` | Count 19 stayed steady with delta 0; rose through 29, 73, 137 and 183 during forward rotation; later fell from 337 to 335 with delta -2 and REVERSE | Real encoder changes reach ROS 2 through the permanent bridge |
| Encoder stopped | Count 335, delta 0, STOP | The bridge reports the stationary state |

The `hz` values are receiver-side measurements during these samples, not
guaranteed rates or a latency benchmark. Topics were checked sequentially while
the combined launch remained running.

## Earlier sensor and command checks

- Camera publication was independently observed around 29–30 Hz.
- LiDAR reported health OK and started Stability mode. Earlier full-array
  summary scripts found finite distances, confirming scans were not all infinity.
- With a target approximately 20 inches away, five scans contained 9–14 readings
  between 0.41 and 0.61 m. This is consistent with the target distance, but the
  script counted all directions and did not uniquely identify the target.
- The nearest reported distance remained 0.30 m; its physical source was not
  identified.
- Standalone encoder firmware showed forward, reverse and stopped counts.
- The user reports successfully running `ros_command_path_test.py` previously
  in the August 28 milestone work. That supports ROS 2-to-Teensy command
  acceptance. Its original output is not included in this evidence folder.
- Motor and steering were validated separately using Teensy tests, as reported
  by the user. These were not ROS 2 physical-actuation tests.

## Warnings and limits

- Initial topic discovery warnings cleared on subsequent reception/retry.
- Camera calibration was missing and a focus control was unsupported. The
  camera continued running and published images. Camera calibration is not
  established by this test.
- Encoder values are raw counts, not calibrated speed. `/ocr2lrc_msg` speed
  feedback is not established.
- The encoder test firmware and command-capable test firmware are separate.
  Simultaneous encoder feedback and actuator-command handling in one firmware
  image have not been validated.
- Numeric `/motor_encoder/count` and `/motor_encoder/delta` topics were added
  in code, but their hardware outputs were not separately captured here.
- Stop/restart repeatability and long-duration reliability were not tested in
  the supplied integrated results.

## Reproduce

Close other sensor launches and programs reading the Teensy serial port. With
the encoder test firmware installed, devices connected, and motor drive power
disconnected for hand rotation, start:

```bash
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; source /ros2_ws/install/setup.bash; ros2 launch scale_truck_bringup sensors.launch.py"
```

Leave that terminal running. In a second Ubuntu terminal, run each separately
and use Ctrl+C between checks:

```bash
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic hz /usb_cam/image_raw"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic hz /scan"
docker exec -it ros2-humble bash -lc "source /opt/ros/humble/setup.bash; ros2 topic echo /motor_encoder/raw"
```

Turn the encoder-connected shaft in both directions and stop it while observing
the final command. Stop the main launch with Ctrl+C when finished.

## Saved evidence

- [Integrated startup log](sensor-launch.txt)
- [Camera, LiDAR and encoder subscriber output](sensor-topics.txt)
- [Earlier LiDAR frequency and scan output](lidar-initial-check.txt)

These files are preserved copies of user attachments, including terminal paste
artifacts. Earlier count-summary and build results above were transcribed from
the conversation. No missing test output has been reconstructed.
