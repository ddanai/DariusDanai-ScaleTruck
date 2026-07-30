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

## Get the reference bag

The original README links these Google Drive files:

- `LV-08-13.bag` (leading vehicle, approximately 3.57 GB)
- `FV-08-13.bag` (following vehicle, approximately 3.66 GB)

Use the download commands under **4.1 rosbag test** in
`references/ros1_scale_truck_control/README.md`. Keep the bags outside Git.

## Inspect the bag first

Run in Ubuntu with ROS 1 Melodic/Noetic installed and sourced:

```bash
rosbag info /data/LV-08-13.bag
```

Confirm the three default topics exist. If the recorded camera or command names
differ, pass the actual names to the analyzer.

## Analyze a recorded full-pipeline bag

```bash
source /opt/ros/noetic/setup.bash
python3 scripts/analyze_ros1_latency.py /data/LV-08-13.bag \
  --start 30 \
  --duration 120 \
  --max-latency-ms 500 \
  --output results/ros1_lv_latency.json \
  --csv results/ros1_lv_latency_samples.csv
```

Add other topics to the frequency/jitter report with repeated options:

```bash
--frequency-topic /scan --frequency-topic /raw_obstacles
```

Use topic overrides when necessary:

```bash
--sensor-topic /camera/image_raw \
--controller-topic /xav2lrc_msg \
--actuator-topic /lrc2ocr_msg
```

Use the same steady-state window and maximum pairing delay for ROS 1 and ROS 2
comparisons. Save the JSON report and raw CSV with the test date and vehicle
name.

## If the reference bag contains sensor data only

Playing a sensor-only bag does not itself contain output timestamps. Start the
ROS 1 stack without physical camera/LiDAR nodes, replay only recorded sensor
topics, and record the inputs plus generated commands:

```bash
rosparam set use_sim_time true
rosbag play /data/LV-08-13.bag --clock \
  --topics /usb_cam/image_raw /scan
```

In another terminal:

```bash
rosbag record -O /data/LV-latency-run.bag \
  /usb_cam/image_raw /xav2lrc_msg /lrc2ocr_msg
```

Do not replay recorded `/xav2lrc_msg` or `/lrc2ocr_msg` while the controller is
also publishing them, because that mixes old and newly generated commands.
Without OpenCR/rosserial hardware, `/lrc2ocr_msg` is still the actuator-command
boundary; `/ocr2lrc_msg` is feedback and is not required for this measurement.

## Interpreting the report

Each latency section contains sample count, minimum, mean, median, p95, p99,
maximum, and population standard deviation in milliseconds. Topic timing
contains observed frequency, interval statistics, and jitter (the population
standard deviation of intervals around the median interval).

A zero sample count usually means the topic is absent, its name is different,
or `--max-latency-ms` is too small. Investigate before comparing runs.
