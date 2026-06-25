# Teensy Firmware

This folder will contain low-level control firmware for throttle, steering, watchdog, and emergency stop behavior.

## Planned Interfaces

- Serial transport between ROS 2 host and Teensy.
- Throttle PID controller with configurable gains and saturation.
- Steering PID controller with configurable gains and saturation.
- Watchdog timeout that returns the truck to a safe stopped state.
- Bench-test mode for fixed input commands before vehicle integration.

## First Tasks

- Confirm Teensy model and Arduino/PlatformIO toolchain.
- Define command frame format and checksum policy.
- Define feedback frame format for speed, steering, heartbeat, and faults.
- Create bench-test procedure.

