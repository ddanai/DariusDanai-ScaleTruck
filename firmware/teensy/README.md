# Main Teensy firmware: hardware commissioning

Version 0.2.0 accepts commands from the ROS serial bridge, drives the ESC and
steering servo, and reports real quadrature encoder counts in the same program.

**Default mode is OPEN_LOOP. Encoder calibration is unknown, so the firmware
cannot measure or regulate speed in m/s yet.** It maps the bridge's speed field
into a limited throttle request. The numeric request is not an achieved speed.
There is no physical E-stop installed; `ESTOP` is a software serial latch.

## Wiring and initial limits

| Connection | Teensy pin / setting |
|---|---|
| ESC signal | 9 |
| Steering servo signal | 6 |
| Encoder A / B | 2 / 3, INPUT_PULLUP, both edges |
| ESC neutral | 1500 microseconds |
| ESC commissioning range | 1500 to 1600 microseconds, forward only |
| Steering center | 1480 microseconds |
| Steering commissioning range | 1360 to 1600 microseconds (requested -10 to +10 degrees) |

These signal pins follow the existing standalone tests. Keep the tested power
wiring: signal grounds shared, and the ESC's 6 V BEC red wire disconnected and
insulated from the USB-powered Teensy. Use the existing external servo supply.
For initial actuation tests, raise the driven wheels and keep steering unloaded.
The reduced throttle range may be below the ESC/motor's start threshold; it is
not a calibrated vehicle response and is not automatically increased.

## Commands

All commands are newline-terminated ASCII at 115200 baud.

| Command | Result |
|---|---|
| `PING`, `INFO`, `STATUS` | Diagnostics, mode, counts and actual commanded pulses |
| `ARM` | Arms after at least 3 seconds of startup neutral; does not move by itself |
| `CMD 0.1 5` | In OPEN_LOOP: 1550 us ESC, 1540 us servo |
| `CMD 0 0` | ESC neutral and steering center |
| `DISARM` | Neutral/center; existing faults remain latched |
| `ESTOP` | Immediately requests neutral/center and latches software E-stop |
| `CLEAR` | Releases software E-stop/faults and returns to DISARMED |
| `HEARTBEAT ON/OFF` | Enable/disable periodic heartbeat text |

`CMD` accepts speed values from 0 to 0.2 and steering from -10 to +10 degrees.
Reverse, larger values, NaN, infinity and malformed CMD packets are rejected;
invalid CMD packets fault an armed controller. Send commands at 20 Hz or faster
than the 250 ms watchdog. Zero speed always produces neutral, including in the
future calibrated PID mode. Steering uses the RC servo's internal position loop;
there is no external steering-angle sensor or steering PID feedback.

Watchdog expiry, USB host disconnect and DISARM request neutral/center. An
oversized or NUL-containing packet disarms and is discarded through its newline.
Serial diagnostics are dropped under backpressure instead of blocking the
control loop. A successful serial write alone does not prove command acceptance.
Neutral is a signal request, not a power cut or a guarantee of mechanical braking.

## Encoder feedback

Every 250 ms the firmware sends the existing bridge-compatible format:

```text
ENCODER count=277 delta=-18 direction=REVERSE
```

Counts continue while disarmed and while driving. Positive/negative refers to
the configured encoder direction, not a verified physical forward direction.
`STATUS` includes `actuators=ENABLED mode=OPEN_LOOP`, pulse widths, encoder count,
and `speed_mps=nan` until calibrated. No fake speed is published. The ROS bridge
continues to publish `/motor_encoder/raw`, `/motor_encoder/count` and
`/motor_encoder/delta`; the legacy `/ocr2lrc_msg` feedback interface is not added.

To calibrate later, measure travelled distance and signed count change, verify
forward sign, and set `kEncoderSign` and `TRUCK_ENCODER_METRES_PER_COUNT` in
`include/firmware_config.h`. This does not require knowing wheel diameter if
travel distance can be measured directly. A positive calibration selects
SPEED_PID mode, sampled every 20 ms, using the initial untuned speed gains.
No-motion counts cannot distinguish a stopped shaft from a disconnected encoder;
calibration alone does not validate sensor fault detection or vehicle dynamics.

## Build and upload

From `firmware/teensy`:

```bash
pio run -e teensy41
pio run -e teensy41 --target upload
```

The older Xavier toolchain configuration remains available as `teensy41_xavier`.
This firmware replaces the separate encoder/motor/servo sketches on the board.
It has been built for Teensy 4.1 but has not been uploaded or physically tested
by this change. It does not print the old simulator BOOT/READY sequence; use PING,
INFO or STATUS after opening the port.

## Run through the ROS bridge

Stop other launches/serial monitors owning the Teensy port. For manual commands:

```bash
ros2 launch scale_truck_bringup teensy_commands.launch.py use_control:=false
```

In another sourced terminal, start a low request at 20 Hz:

```bash
ros2 topic pub --rate 20 /lrc2ocr_msg scale_truck_msgs/msg/Lrc2Ocr "{tar_vel: 0.02, steer_angle: 0.0}"
```

Then explicitly arm from another sourced terminal:

```bash
ros2 service call /firmware/arm std_srvs/srv/Trigger '{}'
ros2 service call /firmware/status std_srvs/srv/Trigger '{}'
ros2 topic echo /firmware/serial_status
```

Observe acceptance replies and pulse widths. Disarm with:

```bash
ros2 service call /firmware/disarm std_srvs/srv/Trigger '{}'
```

Stopping the command publisher also triggers neutral after 250 ms. Clear faults
with `/firmware/clear_faults` before rearming. For the LiDAR-controller launch,
stop the manual publisher and restart without `use_control:=false`; its speed
limit defaults to zero in `closed_loop_test.yaml`. Sensor-driven speed requests
then map to throttle in OPEN_LOOP mode; this is not calibrated speed regulation.

## Tests

The historical `pc_fixed_command_test.py` and ROS `ros_command_path_test.py`
assume simulated feedback. They now refuse hardware-capable firmware before
arming. Do not use their previous pass results as physical-actuator validation.

`test/host/firmware_test.cpp` runs the real main firmware with fake serial,
clock, pins and Servo outputs, and the real PID library. It checks command
mapping, watchdog, disarm, E-stop, USB loss, malformed input, backpressure,
encoder interrupts and rollover. `calibrated_test.cpp` checks a synthetic known
calibration and sensor-fault neutral. Neither test touches physical hardware.
See `test/host/README.md` for host commands.
