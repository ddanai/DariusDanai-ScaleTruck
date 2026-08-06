# Xavier CPU and Memory Recording

Use this procedure alongside each latency bag. It records one-second CPU and
memory samples plus the conditions needed to check that ROS 1 and ROS 2 runs
were comparable.

## One-time preparation

On the Xavier host:

```bash
sudo apt-get install sysstat
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
chmod +x scripts/record_xavier_resources.sh
```

## Before both ROS 1 and ROS 2 tests

Use the same Xavier power mode and clocks. Record the chosen settings rather
than changing them between systems:

```bash
sudo nvpmodel -q
sudo jetson_clocks --show
```

Keep the following unchanged:

- Xavier and power supply;
- wired/wireless interface and network topology;
- input publisher/bag and test duration;
- unrelated background applications;
- ROS 2 `ROS_DOMAIN_ID` and `RMW_IMPLEMENTATION`;
- node parameters and console-output settings.

## Record one run

Start the nodes and input publisher first. From the repository on the Xavier
host, cache sudo authorization so power and clock details can be read without
pausing the measurement, then start resource capture immediately before the
latency bag:

```bash
sudo -v
./scripts/record_xavier_resources.sh ros2 01 35
```

At the same time, record the latency bag for 35 seconds. Repeat with run numbers
`02` through `05`. For ROS 1 use labels such as:

```bash
./scripts/record_xavier_resources.sh ros1 01 35
```

The tracked ROS 1 changes live under
`references/ros1_scale_truck_control`. Before rebuilding the Xavier's active
catkin workspace, synchronize the changed message, controller, and LRC files
into `~/catkin_ws/src/scale_truck_control`, then run `catkin_make`. Keep the
physical OpenCR disconnected because changing `lrc2ocr.msg` changes its
rosserial wire format.

Do not run `top`, `ros2 topic hz`, plotting programs, or other extra workloads
during a measured run.

## Output

Each run produces:

```text
results/latency/resources/ros2-run-01-environment.txt
results/latency/resources/ros2-run-01-cpu-memory.txt
```

The environment file records power, clocks, ROS/RMW, and network conditions.
The `pidstat` file records per-process CPU percentage and resident memory.
Compare runs only when the environment files show matching conditions.

## Experiment 2 trace analyzers

Analyze newly recorded ROS 1 bags from a sourced ROS 1/catkin terminal:

```bash
python3 scripts/analyze_experiment2_ros1_trace_latency.py \
  ~/ros1-experiment2-run-01.bag --start 1 --duration 30 \
  --output results/latency/experiment2/ros1-trace-report-run-01.json \
  --csv results/latency/experiment2/ros1-trace-samples-run-01.csv
```

Analyze newly recorded ROS 2 bags from a sourced ROS 2 terminal:

```bash
python3 scripts/analyze_experiment2_ros2_trace_latency.py \
  /tmp/ros2-experiment2-run-01 --start 1 --duration 30 \
  --output results/latency/experiment2/ros2-trace-report-run-01.json \
  --csv results/latency/experiment2/ros2-trace-samples-run-01.csv
```

Experiment 1 bags must continue using the original analyzers because they were
recorded before the trace fields existed.

## Replaying the public camera bag

The public bag's image timestamps are from 2019. Replay images on an intermediate
topic and use the matching relay to replace only the timestamp while preserving
the image data.

ROS 1 relay:

```bash
python3 scripts/experiment2_restamp_ros1_images.py
```

ROS 1 playback:

```bash
rosbag play --duration=10 ~/left_camera_templergraben.bag \
  /sensors/camera/left/image_raw:=/experiment2/input_image
```

ROS 2 relay, from a sourced ROS 2 container terminal:

```bash
python3 scripts/experiment2_restamp_ros2_images.py
```

ROS 2 playback uses a rosbag2 conversion of the same source bag and the same
remapping. Analyze the same ten-second playback interval in both systems.
