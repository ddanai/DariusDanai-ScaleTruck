# scale_truck_control

## LiDAR distance closed-loop test

The controller consumes `/scan` and selects the nearest finite, in-range return
within a configurable forward sector. It publishes commands through
`/xav2lrc_msg` -> LRC -> `/lrc2ocr_msg` -> serial bridge.

```text
speed = clamp(distance_gain * (measured_distance - target_dist), 0, target_vel)
steering = 0 degrees
```

With gain 0.5, desired gap 0.8 m, and speed limit 0.2 m/s:

| Measured distance | Requested speed |
|---|---|
| 1.2 m or farther | 0.2 m/s |
| 1.0 m | 0.1 m/s |
| 0.8 m or closer | 0 m/s |
| Missing, invalid, or stale scan | 0 m/s |

At/below the hard stop distance (default 0.5 m), speed is always zero. No reverse
is requested. Fresh usable scans automatically resume the distance command;
data loss stops output but does not latch a fault.

Scans expire after 0.3 s using acquisition age plus monotonic time since receipt.
Zero timestamps use receipt time. Future/old timestamps, malformed metadata,
and sectors without finite in-range returns stop the command. Camera messages
cannot refresh scan freshness. LRC zeros speed/steering when the controller
stops publishing for 250 ms.

## Configure and run

Edit `scale_truck_bringup/config/closed_loop_test.yaml`. `params.target_vel`
defaults to zero; set it to a value in `(0, 0.2]` for nonzero test commands.
Invalid settings are rejected at startup. Parameters are startup settings;
restart after changing them.

`closed_loop.front_center_rad` must match the forward direction in the LiDAR's
own frame. Default center is zero radians and half-width is 15 degrees. Verify
the sector with a stationary target. Distances are from the sensor, not the
bumper. This selects the nearest return, not a tracked vehicle; it does not
implement obstacle avoidance or lane steering.

```bash
cd /ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-up-to scale_truck_bringup
source install/setup.bash
ros2 launch scale_truck_bringup teensy_commands.launch.py
```

Observe `/scan`, `/xav2lrc_msg`, and `/lrc2ocr_msg` while moving a target nearer
and farther away. The launch does not arm the Teensy. Its main firmware still
uses simulated feedback and lacks actuator drivers, so physical distance
regulation requires integrated actuator/encoder firmware. Raw encoder counts
are not calibrated m/s; this is not an encoder speed controller. Camera
callbacks only record image arrival.

## Verification without actuators

```bash
colcon test --packages-select scale_truck_control
colcon test-result --verbose
python3 src/scale_truck_control/test/ros_distance_test.py
```

Native tests check sector selection, angle wrap, invalid data, speed limits,
and timeout behavior. The Python test starts controller/LRC nodes in
`/distance_test`, publishes synthetic scans, and checks forwarded ROS commands,
including scan loss and controller loss. It starts no serial bridge and does
not operate actuators. The existing `ros_to_teensy_test` remains a separate
command acceptance test; disable control publishers when running it.
