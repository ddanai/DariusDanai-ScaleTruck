# ROS-to-Teensy Command Test

`ros_command_path_test.py` checks ROS 2-to-Teensy command acceptance,
calculated controller outputs, and watchdog behavior.

**This test did not test physical motor or steering actuator movement.**

With the command-capable Teensy firmware installed, start the bridge:

```bash
ros2 launch scale_truck_bringup teensy_commands.launch.py use_control:=false
```

Then run the test in another terminal with the ROS workspace sourced:

```bash
python3 /ros2_ws/src/ros_to_teensy_test/ros_command_path_test.py
```

This is a standalone workspace test, not a package executable. Replace
`/ros2_ws` with your workspace path if different. Source the built workspace's
`install/setup.bash` before running it so its custom ROS messages are available.

`use_control:=false` prevents the control/LRC nodes from publishing competing
commands or refreshing the watchdog during this test.
