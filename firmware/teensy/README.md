# Scale Truck Teensy Firmware

This directory is the firmware repository for the scale-truck low-level controller. It currently provides the Milestone 5 project foundation and a serial/LED bring-up program. PID control, actuator drivers, and the production command protocol are intentionally reserved for later deliverables.

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
|-- src/
|   `-- main.cpp            # Bring-up firmware
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

For the complete Jetson Xavier connection, build, upload, and serial test
procedure, see [Xavier-Teensy Bring-Up](XAVIER_TEENSY_BRINGUP.md).

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
| `STATUS` | uptime and a `bringup_only=1` marker |
| anything else | `ERR UNKNOWN_COMMAND` |

Successful `PING`/`PONG`, periodic heartbeats, and LED blinking verify the development environment, firmware upload, and bidirectional USB serial communication.

## Configuration

Project-wide constants are in `include/firmware_config.h`. Pin assignments for throttle, steering, encoders, and emergency stop should be added only after the exact Teensy model and wiring are confirmed.

## Safety note

This bring-up firmware does not drive actuator pins. Keep the motor controller and steering actuator disconnected or mechanically safe until saturation, emergency-stop, and watchdog behavior have been implemented and bench-tested.
