# Xavier Fixed-Command Test

Run this after the current firmware has been uploaded using
[Xavier–Teensy Basic Bring-Up](XAVIER_TEENSY_BRINGUP.md). It tests the Teensy
controller from the Xavier without ROS or connected actuators.

## Repeatable test

1. Close miniterm, PlatformIO Monitor, and any other program using the Teensy
   serial port.

2. Open the firmware directory and identify the device:

   ```bash
   cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck/firmware/teensy
   ls /dev/ttyACM*
   ```

3. Run the test:

   ```bash
   python3 test/pc_fixed_command_test.py --port /dev/ttyACM0
   ```

   Substitute the correct device path if it is not `/dev/ttyACM0`.

4. Confirm the final result:

   ```text
   RESULT: 11 passed, 0 failed
   ```

## What passes

- Neutral, forward, and reverse commands
- Left, right, and combined steering commands
- Active-state command repetition inside the 250 ms watchdog period
- Invalid-command rejection and neutral fault outputs
- Watchdog timeout and neutral fault outputs
- Disarm, emergency stop, and fault clearing

## Quick troubleshooting

- `Permission denied`: run `sudo usermod -aG dialout "$USER"`, then log out and
  back in.
- `Device or resource busy`: close every serial monitor and rerun the test.
- `/dev/ttyACM0` missing: reconnect the Teensy and run `ls /dev/ttyACM*` again.
- First command returns `ERR UNKNOWN_COMMAND`: reset the Teensy and rerun the
  test; a previous terminal may have left a partial command in its input buffer.
- Any test reports `FAIL`: save the complete output before resetting or
  uploading again.
