# Scale Truck Teensy Firmware

This directory is the firmware repository for the scale-truck low-level controller. It provides the Milestone 5 project foundation, serial/LED bring-up, and separate speed and steering PID controllers. Actuator drivers and the production command protocol are intentionally reserved for later deliverables.

## Hardware and toolchain

- Default board: Teensy 4.1 (`teensy41`)
- Framework: Arduino for Teensy
- Build system: PlatformIO Core or the PlatformIO VS Code extension
- USB interface: USB serial at 115200 baud

If the truck uses another Teensy model, change `board` in `platformio.ini` to the matching PlatformIO Teensy board ID.

## Repository layout

```text
firmware/teensy/
|-- include/
|   `-- firmware_config.h   # Firmware constants and hardware selection
|   `-- pid_controllers.h   # Independent speed and steering PID interface
|-- src/
|   `-- main.cpp            # Bring-up firmware
|   `-- pid_controllers.cpp # PID_v1-backed controller implementation
|-- test/                   # Future native/unit tests
|-- .gitignore
|-- platformio.ini          # Reproducible build and upload configuration
`-- README.md
```

## Install PlatformIO

Choose either the PlatformIO IDE extension in VS Code or install PlatformIO Core:

```bash
python -m pip install --user platformio
pio --version
```

## Build and upload

For the short Jetson Xavier build, upload, and serial checklist, see
[Xavier-Teensy Bring-Up](XAVIER_TEENSY_BRINGUP.md). Then run the
[Xavier Fixed-Command Test](XAVIER_FIXED_COMMAND_TEST.md) before connecting ROS.

For the Windows PC procedure used to upload and verify the Teensy directly, see
[Teensy Upload Guide](TEENSY_UPLOAD_GUIDE.md).

Run these commands from this directory:

```bash
pio run
pio run --target upload
pio device monitor
```

The monitor uses 115200 baud. If automatic upload does not find the board, connect the Teensy by USB and press its Program button once when PlatformIO requests it.

## Bring-up verification

After reset, the onboard LED blinks at 1 Hz and the serial monitor prints:

```text
BOOT scale-truck-teensy 0.1.0
READY
HEARTBEAT <milliseconds>
```

Type one of these newline-terminated diagnostic commands:

| Command | Expected reply |
|---|---|
| `PING` | `PONG` |
| `INFO` | firmware name, version, and build timestamp |
| `STATUS` | uptime, PID enable state, and normalized PID outputs |
| `HEARTBEAT ON` | enable periodic heartbeat messages |
| `HEARTBEAT OFF` | stop periodic heartbeat messages |
| `DISARM` | disable both PIDs and force both safe outputs to zero |
| `ESTOP` | simulate and latch an emergency stop (reset required) |
| anything else | `ERR UNKNOWN_COMMAND` |

Successful `PING`/`PONG`, periodic heartbeats, and LED blinking verify the development environment, firmware upload, and bidirectional USB serial communication.

## Configuration

Project-wide constants are in `include/firmware_config.h`. Pin assignments for throttle, steering, encoders, and emergency stop should be added only after the exact Teensy model and wiring are confirmed.

## PID controllers

`PidControllers` contains two independent instances of Brett Beauregard's
MIT-licensed Arduino PID library: one maps speed error to normalized throttle
and one maps steering-angle error to a normalized steering command. Both
outputs are limited to `[-1, 1]`, use a 20 ms sample period, and remain disabled
by default. The initial gains are safe placeholders, not tuned vehicle values.

Call `enable()` only after the emergency stop, command watchdog, sensors, and
actuator drivers are operational. Feed current speed and steering angle to
`update()` on every pass through `loop()`, then map `throttleCommand()` and
`steeringCommand()` to the verified hardware ranges. `disable()` immediately
returns both computed commands to zero.

## Safety supervisor

`SafetyController` is the only approved source of actuator commands. It boots
`DISARMED`, requires an explicit arm followed by a valid command before entering
`ACTIVE`, limits initial throttle authority to `[-0.20, 0.20]`, and limits
steering authority to `[-0.25, 0.25]`. Invalid/non-finite feedback, implausible
commands, or a command gap longer than 250 ms disable both PIDs, force neutral
outputs, and latch a fault. An emergency stop does the same immediately and
cannot be cleared while its physical input remains asserted.

The current bring-up program intentionally exposes no `ARM` command and does
not call the control cycle, because sensor inputs, the physical E-stop pin, and
actuator-neutral signals are not defined yet. Hardware integration must call
`setEmergencyStop()` and `update()` every loop, send only the supervisor's
clamped outputs to drivers, and provide an explicit operator-controlled path to
`clearFaults()` and `arm()`.

## Safety note

This bring-up firmware does not drive actuator pins. Keep the motor controller and steering actuator disconnected or mechanically safe until saturation, emergency-stop, and watchdog behavior have been implemented and bench-tested.
