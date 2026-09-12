# Firmware host tests

Run on Linux/WSL from `firmware/teensy`, after a PlatformIO build has downloaded
the PID dependency. These compile the real firmware with simulated Arduino and
Servo interfaces; no Teensy is connected or operated.

```bash
g++ -std=c++17 -DARDUINO=100 -Wall -Wextra \
  -Itest/host -Iinclude -I.pio/libdeps/teensy41/PID \
  test/host/firmware_test.cpp src/truck_hardware.cpp \
  src/pid_controllers.cpp src/safety_controller.cpp \
  .pio/libdeps/teensy41/PID/PID_v1.cpp -o /tmp/scaletruck-firmware-test
/tmp/scaletruck-firmware-test

g++ -std=c++17 -DARDUINO=100 -DTRUCK_ENCODER_METRES_PER_COUNT=0.001 \
  -Wall -Wextra -Itest/host -Iinclude -I.pio/libdeps/teensy41/PID \
  test/host/calibrated_test.cpp src/truck_hardware.cpp \
  src/pid_controllers.cpp src/safety_controller.cpp \
  .pio/libdeps/teensy41/PID/PID_v1.cpp -o /tmp/scaletruck-calibrated-test
/tmp/scaletruck-calibrated-test
```

The 0.001 calibration belongs only to the synthetic test. It is not a measured
calibration for the truck and must not be copied into its hardware settings.
