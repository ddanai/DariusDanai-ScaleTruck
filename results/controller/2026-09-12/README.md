# Xavier controller verification — September 12, 2026

## Outcome and evidence

Both software test layers passed on the user's Xavier in the `ros2-humble`
Docker container. This record summarizes terminal output supplied by the user;
the tests were not rerun from the Windows development workspace. The tested
Git commit was not captured, so this is evidence of that run rather than a
commit-specific certification.

| Check | Reported result |
|---|---|
| Build | `scale_truck_msgs` and `scale_truck_control` built successfully; 2 packages finished in 2 min 43 s |
| C++ / CTest | `distance_control_test` passed in 0.03 s; 1 test, 0 errors, 0 failures, 0 skipped |
| ROS integration | `RESULT: 12 passed; no hardware actuation tested` |

The user then reran the C++ test separately against the existing build in the
same container. CTest tag `20260912-0914` reported `distance_control_test`
passing again in 0.03 s (total CTest time 0.05 s). The package test command
finished in 1.63 s with **1 test, 0 errors, 0 failures, 0 skipped**. This
confirms a second successful execution of the C++ test; the Python integration
result above comes from the earlier run, not this C++-only rerun.

The integration script reported PASS for all of these checks:

1. No scan stops.
2. Far target capped.
3. Approaching target slows.
4. Desired gap stops.
5. Close obstacle stops.
6. Invalid scan stops.
7. Old acquisition timestamp stops.
8. Future acquisition timestamp stops.
9. Fresh scan recovers.
10. Scan loss stops.
11. Moving before controller loss.
12. Controller loss stops LRC output.

An initial `cd ros2_ws` failed because the shell was already in the correct
workspace. Subsequent build and test commands ran successfully there. An earlier
run before updating the Xavier checkout found zero tests and no Python test
file; that earlier output was not a passing verification.

## Scope

The C++ executable checks calculation functions directly, including sector
selection, wrapped angles, invalid ranges, speed limits, and age-based stopping.
Its multiple assertions are counted as one CTest test. It does not start ROS
nodes or exercise actual timer/message behavior.

The Python harness starts the actual C++ controller and LRC in `/distance_test`,
publishes synthetic LaserScan messages, and checks forwarded commands. This
adds evidence for ROS integration, freshness handling, recovery, and stopping
after loss of scans or the controller process. It is a separate manual test,
not part of the `colcon test` count.

Run both after controller/LRC changes and before hardware commissioning: direct
function checks and running-node checks cover different failure modes. Neither
test validates physical sensor alignment, serial transport, Teensy behavior,
motor/steering actuation, or calibrated vehicle speed. No serial bridge was
started by the integration test.

## Reproduce on the Xavier

With the repository updated and the existing container running, enter it:

```bash
docker exec -it ros2-humble bash
```

Inside the container, use the nested repository workspace used for this run:

```bash
cd /ros2_ws/src/DariusDanai-ScaleTruck/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-up-to scale_truck_control --cmake-args -DBUILD_TESTING=ON
source install/setup.bash
colcon test --packages-select scale_truck_control --event-handlers console_direct+
colcon test-result --verbose
python3 src/scale_truck_control/test/ros_distance_test.py
```

For future evidence, also record `git rev-parse HEAD` and `git status --short`
from the repository so the tested revision and any local modifications are known.
