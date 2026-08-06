# ROS 2 Latency Test

This procedure completes the ROS 2 half of Milestone 4 using the same boundaries
and correlation rules as the ROS 1 baseline:

- sensor-to-controller: `/usb_cam/image_raw` to `/xav2lrc_msg`;
- controller-to-actuator command: `/xav2lrc_msg` to `/lrc2ocr_msg`;
- end-to-end command: `/usb_cam/image_raw` to `/lrc2ocr_msg`;
- frequency, inter-message interval, and jitter for all three topics.

## Measurement limitation

The current custom ROS 2 messages do not carry a common trace ID. The analyzer
uses rosbag2 receive timestamps, pairing each controller command with the latest
preceding sensor frame and the first following actuator command. This is a
repeatable response-time estimate, not proof of causality. Use the identical
input bag, duration, Xavier power mode, and idle system conditions for ROS 1 and
ROS 2 comparisons.

## Build and launch on the Xavier

Inside the running `ros2-humble` container:

```bash
cd /ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch scale_truck_bringup lv.launch.py
```

The controller and LRC intentionally publish at 50 Hz (`update_period_s: 0.02`),
fixing the unbounded approximately 1800 Hz ROS 1 LRC loop.

## Check and record the measurement boundaries

In a second sourced container terminal:

```bash
ros2 topic list
ros2 topic hz /xav2lrc_msg
ros2 topic hz /lrc2ocr_msg
ros2 bag record --storage sqlite3 --output /tmp/ros2-latency-run-01 \
  /usb_cam/image_raw /xav2lrc_msg /lrc2ocr_msg
```

Play the same camera input used for the ROS 1 run, remapped to
`/usb_cam/image_raw`. If the source is a ROS 1 `.bag`, convert it to rosbag2
first or publish it through a ROS 1 bridge. Do not compare different inputs.
Record at least 30 seconds after all topics become active, stop with `Ctrl+C`,
and repeat at least five times (`run-01` through `run-05`).

Validate every recording:

```bash
ros2 bag info /tmp/ros2-latency-run-01
```

All three topics must have nonzero message counts.

## Analyze each run

From the repository root (only Python 3 is required):

```bash
mkdir -p results/latency/ros2
python3 scripts/analyze_ros2_latency.py /tmp/ros2-latency-run-01 \
  --max-latency-ms 500 \
  --output results/latency/ros2/ros2_latency_report_run_01.json \
  --csv results/latency/ros2/ros2_latency_samples_run_01.csv
```

Repeat for each bag. Every latency metric must have a nonzero `count`, and the
two output topics should be near 50 Hz. A zero count means a boundary is absent,
the test windows do not overlap, or the correlation interval is too small.

For bags recorded after the trace fields were added, use exact correlation
inside the sourced ROS 2 workspace:

```bash
python3 scripts/analyze_experiment2_ros2_trace_latency.py /tmp/ros2-latency-run-01 \
  --start 1 --duration 30 \
  --output results/latency/ros2/ros2_trace_report_run_01.json \
  --csv results/latency/ros2/ros2_trace_samples_run_01.csv
```

The report's `trace_count` must be greater than zero. Old bags cannot be used
for exact correlation because their recorded message schema has no trace fields.

## Record CPU utilization

While playback is active, sample the launched processes on the Xavier:

```bash
pidstat -h -u -r -p ALL 1 30 > /tmp/ros2-latency-run-01-pidstat.txt
```

Use the same command and duration for ROS 1. Report mean CPU percentage and
resident memory for the controller and LRC alongside the bag-derived metrics.
The recommended repeatable resource procedure is documented in
[`xavier-resource-recording.md`](xavier-resource-recording.md).

## Acceptance checklist

- Five comparable ROS 2 runs are recorded and analyzed.
- All three topics and latency metrics have nonzero samples.
- Median, p95, p99, standard deviation, frequency, and jitter are retained.
- CPU sampling duration is identical for ROS 1 and ROS 2.
- Large bag directories stay out of Git; commit only JSON, CSV, and small logs.
