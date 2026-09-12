# scale_truck_bringup

ROS 2 launch files and runtime configuration for starting the scale truck stack.

Expected contents:

- `launch/`: ROS 2 launch descriptions.
- `config/`: shared runtime configuration files.

## Teensy command launch

`teensy_commands.launch.py` reuses `vehicle.launch.py` to start the serial
bridge with command sending enabled, the camera and LiDAR drivers, and the
control and LRC nodes. The control node publishes to the LRC, which publishes
`/lrc2ocr_msg`; the bridge forwards speed and steering setpoints over USB.
The launch does not arm the Teensy. Its default `closed_loop_test.yaml` target
speed is zero; set it to at most 0.2 m/s for nonzero distance commands.

This is an integration launch, not completed physical closed-loop control:

- The camera callback currently records image arrival, not lane steering.
- The control node consumes LiDAR scans for straight-line distance control,
  stopping on invalid/stale data. It does not consume raw encoder counts.
- The bridge publishes raw encoder counts, not calibrated `/ocr2lrc_msg` speed.
- Main Teensy firmware 0.2.0 drives ESC/servo outputs and reads real counts.
  Unknown encoder calibration selects limited OPEN_LOOP throttle, not m/s regulation.

LiDAR distance now changes requested speed; steering stays centered. Physical
sensor-to-actuator testing requires uploading and commissioning firmware 0.2.0.
See [controller testing](../scale_truck_control/README.md) for parameters,
sector alignment, and synthetic ROS tests. Laser filtering and obstacle
processing remain disabled; the controller consumes raw scans directly.

Copy the changes to the Xavier checkout, then build in its ROS 2 environment
(inside the `ros2-humble` container if using Docker):

```bash
cd /ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-up-to scale_truck_bringup
source install/setup.bash
ros2 launch scale_truck_bringup teensy_commands.launch.py
```

Close the sensor launch and any serial monitor first; only one process should
use the Teensy port. The default port is `/dev/ttyACM0` at 115200 baud, configured
in `config/serial_bridge.yaml`. Install the main command-capable Teensy firmware;
the separate encoder-test firmware does not accept these commands.

For the existing fixed-command test or manual publications, stop the default
launch and restart with the control/LRC publishers disabled. Otherwise they
compete with test commands and keep refreshing the watchdog:

```bash
ros2 launch scale_truck_bringup teensy_commands.launch.py use_control:=false
```

In another terminal in the same ROS environment, run the existing test:

```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
python3 /ros2_ws/src/ros_to_teensy_test/ros_command_path_test.py
```

The test clears faults, arms, publishes a 0.2 m/s target with zero steering,
checks calculated outputs, checks the watchdog, and disarms on historical
simulation-only firmware. It now refuses to arm hardware-capable firmware 0.2.0.
For physical commands, follow [firmware commissioning](../../../firmware/teensy/README.md).

In this manual mode, to publish your own speed and steering targets instead of running the test,
start this publisher in a separate sourced terminal:

```bash
ros2 topic pub --rate 20 /lrc2ocr_msg scale_truck_msgs/msg/Lrc2Ocr "{tar_vel: 0.02, steer_angle: 0.0}"
```

Then arm from another sourced terminal:

```bash
ros2 service call /firmware/arm std_srvs/srv/Trigger '{}'
ros2 topic echo /firmware/serial_status
```

Service success confirms the serial write; check `OK ARMED` and
`OK COMMAND_ACCEPTED` replies for firmware acceptance. The speed field is intended
as m/s but uncalibrated firmware maps it to limited throttle; steering is in
degrees. Commands before arming are rejected. Stopping the
publisher triggers the 250 ms watchdog; use `/firmware/clear_faults` before
rearming after a fault. To disarm explicitly:

```bash
ros2 service call /firmware/disarm std_srvs/srv/Trigger '{}'
```
