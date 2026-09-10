# Actuator commands and sensor feedback

This is the current interface definition for the ROS 2 drivers and Teensy
bridge. A topic is a named channel; its message type defines the fields carried
on that channel. Names below assume the default empty namespace. Nodes use
relative names, so a namespace prefixes them and launch remapping can change them.

## Topic inventory

| Topic | Message type | Publisher → receiver | Rate and status |
|---|---|---|---|
| `/lrc2ocr_msg` | `scale_truck_msgs/msg/Lrc2Ocr` | `lrc_node` or command-test node → `serial_bridge_node` → Teensy | LRC default 50 Hz; enabled only in command mode; command acceptance previously reported passed |
| `/firmware/serial_status` | `std_msgs/msg/String` | Serial bridge → diagnostic/test subscribers | One per received serial line; no fixed rate |
| `/usb_cam/image_raw` | `sensor_msgs/msg/Image` | `usb_cam` → image subscribers, including control when enabled | Configured 30 Hz, observed about 28–29 Hz in combined launch |
| `/scan` | `sensor_msgs/msg/LaserScan` | `rplidar_node` → scan subscribers | Observed about 13.7 Hz; depends on scanner operation |
| `/motor_encoder/raw` | `std_msgs/msg/String` | Serial bridge → encoder subscribers | About 4 Hz with encoder-test firmware; hardware verified |
| `/motor_encoder/count` | `std_msgs/msg/Int32` | Serial bridge → numeric encoder subscribers | Same valid encoder reports; implemented, separate hardware capture pending |
| `/motor_encoder/delta` | `std_msgs/msg/Int32` | Serial bridge → numeric encoder subscribers | Same valid encoder reports; implemented, separate hardware capture pending |
| `/ocr2lrc_msg` | `scale_truck_msgs/msg/Ocr2Lrc` | Reserved firmware feedback → `lrc_node` | Message and subscription exist; current bridge does not publish it |

## Command message: Lrc2Ocr

Only `tar_vel` and `steer_angle` are sent to the Teensy by the current bridge.
The other fields retain the controller's existing message layout.

| Field | Type | Meaning and units | Used by serial bridge? |
|---|---|---|---|
| `trace_id` | `uint64` | Correlation identifier copied through the control pipeline; no units | No |
| `sensor_stamp` | `builtin_interfaces/Time` | Originating sensor timestamp (seconds and nanoseconds); not a command-expiry timestamp | No |
| `index` | `int32` | Truck identifier; no units | No |
| `steer_angle` | `float32` | Requested steering angle in degrees, as interpreted by command firmware | Yes |
| `cur_dist` | `float32` | Current separation, metres by interface convention | No |
| `tar_dist` | `float32` | Requested separation, metres by interface convention | No |
| `tar_vel` | `float32` | Requested signed speed in metres/second | Yes |
| `pred_vel` | `float32` | Predicted speed in metres/second | No |
| `alpha` | `bool` | LRC velocity-sensor discrepancy flag | No |

Positive/negative speed denotes the requested forward/reverse convention.
Physical steering left/right sign, centre and servo mapping must be established
by actuator calibration; the bridge performs no sign or unit conversion.
The retained separation fields are not used to drive the Teensy.

Example message fragment (illustrative, not a publish command):

```yaml
tar_vel: 0.2
steer_angle: 5.0
```

It becomes ASCII `CMD 0.200000 5.000000` followed by a newline at 115200 baud.
These are speed and angle setpoints, not PWM values or throttle percentages.
The command-capable firmware must be armed before accepting them. Its current
plausibility limits are finite values with absolute speed at most 15 m/s and
absolute steering angle at most 45 degrees. These are rejection limits, not
validated operating speeds or physical steering limits.

The firmware command watchdog is 250 ms. Commands must arrive with margin inside
that interval; the default LRC timer is 20 ms (50 Hz), and the acceptance test
sends approximately every 50 ms. Firmware uses command arrival time, not
`sensor_stamp`, for this watchdog. Current code does not enforce upstream sensor
freshness: repeating a stale setpoint can still refresh the firmware watchdog.

Command topic QoS: reliable, volatile, keep-last depth 1. A DDS delivery or a
successful serial write does not prove board acceptance. Observe
`OK COMMAND_ACCEPTED` or an `ERR ...` reply on `/firmware/serial_status`.

## Sensor message fields

### Camera

`sensor_msgs/msg/Image` carries `header.stamp` (timestamp), `header.frame_id`
(configured `usb_cam`), `height` and `width` (pixels), `encoding` (pixel format),
`is_bigendian`, `step` (bytes per row), and `data` (pixel bytes). Read `encoding`
from the message rather than assuming a format. Current configuration requests
640 × 480 capture. Image publication does not establish camera calibration;
the recorded run reported a missing calibration file.

### LiDAR

`sensor_msgs/msg/LaserScan` carries:

| Field | Meaning / units |
|---|---|
| `header.stamp`, `header.frame_id` | Scan timestamp and coordinate frame; configured frame is `laser` |
| `angle_min`, `angle_max`, `angle_increment` | Scan angles and angular spacing, radians |
| `time_increment`, `scan_time` | Time between measurements and scan duration, seconds |
| `range_min`, `range_max` | Reported valid distance limits, metres |
| `ranges` | Distances in metres, indexed by scan angle |
| `intensities` | Device-dependent return strength; not distance |

The recorded scan reported limits of 0.15–25 m. Treat finite ranges inside the
reported limits as usable. Infinity is not a measured obstacle distance; reject
NaN and out-of-range values too. The earlier test confirmed finite ranges.
The standard scan convention is zero angle along +X and positive angles around
+Z. This does not establish the sensor's mounting transform relative to the truck.

Camera/LiDAR publisher QoS belongs to their installed drivers. Inspect actual
endpoints with `ros2 topic info <topic> -v`; do not infer driver queue depth from
this document. Sensor-data subscribers using best-effort, volatile QoS can
receive either reliable or best-effort sensor publishers. The earlier camera
endpoint was reliable. The custom bridge feedback topics use reliable,
volatile, keep-last depth 5.

### Encoder

The bridge accepts complete lines such as:

```text
ENCODER count=277 delta=-18 direction=REVERSE
```

- `/motor_encoder/raw`: `String.data` contains that line.
- `/motor_encoder/count`: `Int32.data` contains signed cumulative quadrature
  counts since firmware startup. A negative total is valid. Resetting firmware
  resets this reference; it is not an absolute wheel position.
- `/motor_encoder/delta`: `Int32.data` contains the signed change since the
  previous firmware report, nominally every 250 ms. This is not counts/second.
- `FORWARD` means positive delta, `REVERSE` negative, and `STOP` zero, according
  to the A/B wiring. These labels do not independently establish vehicle direction.

The bridge rejects malformed lines, integers outside signed 32-bit range, and
direction labels inconsistent with delta. All received lines remain visible on
serial_status for diagnosis. These messages have no acquisition timestamp or
frame field; they are not a synchronized odometry interface. Report timing is
nominal, so delta alone is insufficient for precise calibrated speed.

Encoder counts per revolution, gearing and wheel circumference must be known
before converting to m/s. No conversion is currently performed. If serial data
stops, encoder topics stop; the last count must not be treated as fresh feedback.
No automatic serial reconnect or stale-data alarm is currently provided.

## Reserved feedback: Ocr2Lrc

| Field | Type | Current interpretation |
|---|---|---|
| `cur_vel` | `float32` | Intended measured signed velocity, m/s; no real encoder producer yet |
| `u_k` | `float32` | Legacy saturated control input used by the LRC velocity observer; physical scaling is not yet defined for the Teensy |

Do not publish raw counts as `cur_vel` or normalized throttle as `u_k` without
defining the calibration/observer mapping. This reserved interface is documented
but is not part of the demonstrated live feedback path. Its intended LRC
subscription QoS is reliable, volatile, depth 5; no live rate is established.

## Teensy services and operating modes

All four services use `std_srvs/srv/Trigger` (empty request; response `success`
boolean and `message` text):

| Service | Serial command |
|---|---|
| `/firmware/arm` | `ARM` |
| `/firmware/disarm` | `DISARM` |
| `/firmware/clear_faults` | `CLEAR` |
| `/firmware/status` | `STATUS` |

Success means the serial command was written. Firmware acceptance/state must be
read from serial_status. Current CLEAR/ESTOP handling in command-test firmware
is software bring-up behavior, not validation of a physical emergency stop.

`sensors.launch.py` disables control nodes and sets `commands_enabled=false`:
there is no command subscription, services return failure, and the bridge sends
no startup/shutdown commands. It supports the currently installed encoder-test
firmware. In command mode the bridge sends `HEARTBEAT OFF` at startup and tries
`DISARM` at shutdown. Loss of the process requires the firmware watchdog rather
than relying on the shutdown write.

Encoder-test firmware and command-capable firmware are separate programs.
The bridge implements their respective interfaces, but combined firmware and
physical ROS-controlled actuation have not been validated by these sensor tests.

## Evidence and definition status

The active topic names, types, fields, units, producers/consumers, rate
expectations, QoS and operating modes are defined here. This completes the
**actuator command and sensor-feedback topic definitions** deliverable for the
current implementation. Reserved legacy feedback is explicitly identified;
defining an interface does not claim that its hardware integration is complete.

See [saved hardware results](../../results/hardware/2026-09-09/README.md) and
[bridge setup](../../ros2_ws/src/scale_truck_firmware_bridge/README.md).
Source definitions: [Lrc2Ocr](../../ros2_ws/src/scale_truck_msgs/msg/Lrc2Ocr.msg),
[Ocr2Lrc](../../ros2_ws/src/scale_truck_msgs/msg/Ocr2Lrc.msg),
[serial bridge](../../ros2_ws/src/scale_truck_firmware_bridge/src/serial_bridge_node.py),
and [firmware limits](../../firmware/teensy/include/firmware_config.h).
