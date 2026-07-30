# ROS 1 Latency Baseline

This test establishes the Milestone 4 ROS 1 baseline from the reference
repository's bag. It reports:

- sensor-to-controller latency: `/usb_cam/image_raw` to `/xav2lrc_msg`;
- controller-to-actuator-command latency: `/xav2lrc_msg` to `/lrc2ocr_msg`;
- end-to-end command latency: `/usb_cam/image_raw` to `/lrc2ocr_msg`;
- publishing frequency, inter-message interval, and jitter for each topic.

## Important measurement limitation

The ROS 1 custom command messages do not carry a `Header`, sensor sequence ID,
or common trace ID. The analyzer uses ROS bag record timestamps. Each controller
command is associated with the latest preceding sensor frame and the first
following actuator command within a configurable limit. End-to-end latency
requires that complete chain. This is a repeatable response-time estimate, not
proof that a specific sensor frame caused a specific command.

For an exact live measurement, add a trace ID and sensor acquisition timestamp
to the controller and actuator command messages and preserve both through the
pipeline.

## Tested environment

The procedure below was validated with:

- Jetson AGX Xavier;
- Ubuntu 20.04 and ROS 1 Noetic;
- ROS 1 workspace at `~/catkin_ws`;
- this repository at
  `~/ros2_humble_ws/src/DariusDanai-ScaleTruck`;
- no camera, LiDAR, OpenCR, motors, or other truck hardware connected.

The repository location inside a ROS 2 workspace does not change the test.
The active runtime is ROS 1 because the terminals source Noetic and the catkin
workspace. Do not source the ROS 2 Humble workspace in the test terminals.

## Select and download an input bag

The original README links these Google Drive files:

- `LV-08-13.bag` (leading vehicle, approximately 3.57 GB)
- `FV-08-13.bag` (following vehicle, approximately 3.66 GB)

At the time of testing, both reference links returned Google Drive permission
errors. A public ROS 1 camera bag from the RWTH Aachen ACDC workshop was used as
a substitute. It contains 540 raw `sensor_msgs/Image` messages over 18 seconds.

Download it on the Xavier:

```bash
cd ~
wget --content-disposition \
  "https://rwth-aachen.sciebo.de/s/sbSBamXYCfQw9kM/download" \
  -O left_camera_templergraben.bag
```

Inspect and validate the download:

```bash
source /opt/ros/noetic/setup.bash
rosbag info ~/left_camera_templergraben.bag
file ~/left_camera_templergraben.bag
```

The bag should contain `/sensors/camera/left/image_raw` with message type
`sensor_msgs/Image`. Keep all `.bag` files outside Git.

## Software-only test procedure

Open five SSH terminals connected to the Xavier. Run the terminals in the order
shown below.

### Terminal 1: ROS master

```bash
source /opt/ros/noetic/setup.bash
roscore
```

Leave this terminal running.

### Terminal 2: scale-truck controller

Source ROS 1 and load the controller parameters:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash

rosparam load \
  "$(rospack find scale_truck_control)/config/config.yaml" \
  /scale_truck_control
rosparam load \
  "$(rospack find scale_truck_control)/config/LV.yaml" \
  /scale_truck_control
```

Disable OpenCV windows and console rendering because the node is running over
SSH without a display:

```bash
rosparam set /scale_truck_control/image_view/enable_opencv false
rosparam set /scale_truck_control/image_view/enable_console_output false
```

Start the controller with the name used by the reference launch file:

```bash
rosrun scale_truck_control scale_truck_control \
  __name:=scale_truck_control
```

`Waiting for image` is expected until Terminal 5 starts playback. Leave the
controller running.

### Terminal 3: Local Resiliency Coordinator

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash

rosparam load \
  "$(rospack find scale_truck_control)/config/lrc.yaml" \
  /LRC
rosparam load \
  "$(rospack find scale_truck_control)/config/LV.yaml" \
  /LRC

rosrun scale_truck_control LRC __name:=LRC
```

Leave the LRC running. OpenCR is not required: `/lrc2ocr_msg` is treated as the
actuator-command boundary even when no physical actuator consumes it.

### Terminal 4: latency recording

Check storage before recording:

```bash
df -h /
```

Start a compressed recording containing only the three measurement boundaries:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash

rosbag record --lz4 -O ~/ros1-latency-run.bag \
  /usb_cam/image_raw \
  /xav2lrc_msg \
  /lrc2ocr_msg
```

Wait until the terminal confirms it is recording, then immediately start
Terminal 5. Avoid leaving the recorder idle because idle periods distort the
observed topic durations and frequencies.

### Terminal 5: virtual camera playback

Play ten seconds of camera data and remap it to the controller's expected
camera topic:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash

rosbag play --duration=10 ~/left_camera_templergraben.bag \
  /sensors/camera/left/image_raw:=/usb_cam/image_raw
```

When playback returns to the prompt, immediately press `Ctrl+C` in Terminal 4.
Wait for `rosbag record` to finish closing the output bag.

## Validate the recorded test

```bash
rosbag info ~/ros1-latency-run.bag
ls -lh ~/ros1-latency-run.bag
df -h /
```

The bag must show nonzero message counts for:

```text
/usb_cam/image_raw
/xav2lrc_msg
/lrc2ocr_msg
```

For a quick live check before recording, loop the input bag in one terminal:

```bash
rosbag play --loop ~/left_camera_templergraben.bag \
  /sensors/camera/left/image_raw:=/usb_cam/image_raw
```

Then check each boundary from another sourced terminal:

```bash
rostopic hz /usb_cam/image_raw
rostopic hz /xav2lrc_msg
rostopic hz /lrc2ocr_msg
```

Stop looping playback before making the final recording.

## Generate the latency report

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash

python3 \
  ~/ros2_humble_ws/src/DariusDanai-ScaleTruck/scripts/analyze_ros1_latency.py \
  ~/ros1-latency-run.bag \
  --max-latency-ms 500 \
  --output ~/ros1_latency_report.json \
  --csv ~/ros1_latency_samples.csv
```

Running the command again replaces the existing JSON and CSV output files.
Verify that the corrected correlation method was used:

```bash
grep -A3 '"method"' ~/ros1_latency_report.json
```

The method should say:

```text
latest sensor before each controller command;
first actuator command after each controller command
```

## Save the result files in Git

Copy only the small report files into the repository:

```bash
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
mkdir -p results/latency/ros1

cp ~/ros1_latency_report.json results/latency/ros1/
cp ~/ros1_latency_samples.csv results/latency/ros1/
```

Commit and push:

```bash
git add results/latency/ros1/
git commit -m "Add ROS1 latency results"
git push origin main
```

Never add `ros1-latency-run.bag` to Git. The test bag is large and GitHub rejects
individual files larger than 100 MB.

## Interpreting the report

Each latency section contains sample count, minimum, mean, median, p95, p99,
maximum, and population standard deviation in milliseconds. Topic timing
contains observed frequency, interval statistics, and jitter (the population
standard deviation of intervals around the median interval).

A zero sample count usually means the topic is absent, its name is different,
the measurement windows did not overlap, or `--max-latency-ms` is too small.
Investigate before comparing runs.

The validated test exposed an additional ROS 1 baseline issue:
`/lrc2ocr_msg` published at approximately 1800 Hz because the LRC loop appears
to have no rate limiter. Preserve this as a ROS 1 observation and add an
intentional publication rate to the ROS 2 implementation.

The substitute camera bag is useful for repeatable software processing tests,
but its scene and camera calibration differ from the unavailable reference
truck bag. Record this distinction when comparing results.

## Common problems

### Cannot contact ROS master

If playback reports `Failed to contact master at [localhost:11311]`, start
`roscore` in Terminal 1 and leave it running.

### Custom message class cannot be loaded

If `rostopic` reports that it cannot load
`scale_truck_control/xav2lrc`, source both environments:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
```

If the message is still unavailable, rebuild:

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

### GTK cannot open a display

Ensure the private controller parameters are set before starting the node:

```bash
rosparam set /scale_truck_control/image_view/enable_opencv false
rosparam set /scale_truck_control/image_view/enable_console_output false
```

Start the controller with `__name:=scale_truck_control` so it reads parameters
from the same namespace used by the reference launch configuration.
