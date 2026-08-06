# Experiment 2 work summary: August 5–6, 2026

## Objective

Experiment 2 improved the ROS 1 versus ROS 2 timing comparison by adding exact
message tracing and Xavier resource measurements. The goal was to replace the
timing-proximity estimates used in Experiment 1 with direct matching from each
camera frame through the controller and LRC output.

## Work completed on August 5

- Added a `trace_id` and sensor acquisition timestamp to the ROS 1 and ROS 2
  controller-command and actuator-command messages.
- Updated both controllers to create a trace for each received image.
- Updated both LRC implementations to copy the trace ID and sensor timestamp
  into their output messages.
- Added exact-trace latency analyzers for ROS 1 and ROS 2.
- Added automated analyzer tests and confirmed all nine repository tests pass.
- Added `record_xavier_resources.sh` to record per-process CPU usage, resident
  memory, Xavier power mode, clock state, CPU availability, network state, and
  ROS/RMW settings.
- Added Xavier resource-recording documentation.
- Copied the tracked Experiment 2 ROS 1 changes into the active Xavier catkin
  package after first creating a backup of the replaced files.
- Rebuilt the active ROS 1 workspace and verified the generated message types.
- Fixed the ROS 2 Humble timestamp conversion and rebuilt all six ROS 2
  packages successfully.
- Verified exact trace propagation through `/xav2lrc_msg` and `/lrc2ocr_msg`
  in both ROS versions.
- Installed `sysstat` on the Xavier and confirmed `pidstat` CPU/memory capture.
- Confirmed the Xavier test conditions: `MODE_15W_DESKTOP`, CPUs `0-3`, and
  `wlan0` active.
- Confirmed ROS 2 used `rmw_fastrtps_cpp` with domain ID `0`.

## Work completed on August 6

- Selected the public `left_camera_templergraben.bag` as the repeatable camera
  input. It contains 540 real images over approximately 18 seconds at 30 Hz.
- Added matching ROS 1 and ROS 2 image-restamping relays so the historical 2019
  image timestamps are replaced with the current Xavier acquisition time.
- Added clean ROS 2 relay shutdown handling.
- Converted only the public bag's image topic from rosbag1 to rosbag2 using
  `rosbags-convert`, avoiding unrelated TF and camera-info topics.
- Verified the public bag passed through each restamping relay and produced
  matching trace IDs and timestamps at the controller and LRC outputs.
- Recorded five official ROS 1 runs and five official ROS 2 runs.
- Recorded matching CPU, memory, environment, power, network, and middleware
  information for every run.
- Detected and corrected invalid setup attempts, including duplicate ROS 2
  restamping relays, stale pre-playback traces, incomplete recording windows,
  and a rosbag2 read-ahead queue starvation warning.
- Analyzed all ten accepted runs using exact trace matching.
- Confirmed all runs used the same Xavier power mode, online CPUs, and WLAN
  interface. ROS-specific middleware settings were also consistent within each
  system.
- Committed and pushed the 40 raw Experiment 2 result files in commit
  `fdf6e42` (`Add Experiment 2 trace and Xavier resource results`).
- Generated the final comparison table, summary data, latency plots, per-run
  plot, CPU/memory plot, and written analysis.
- Organized generated comparison data and plots under
  `results/latency/experiment2-comparison/` with filenames beginning with
  `experiment2-`.

## Main results

The pooled exact-trace results contain 586 ROS 1 traces and 690 ROS 2 traces.

| End-to-end measure | ROS 1 | ROS 2 | Change |
|---|---:|---:|---:|
| Mean | 45.51 ms | 16.52 ms | 63.7% lower |
| Median | 40.00 ms | 15.59 ms | 61.0% lower |
| p95 | 93.33 ms | 27.85 ms | 70.2% lower |
| p99 | 173.30 ms | 31.52 ms | 81.8% lower |
| Maximum | 235.62 ms | 38.61 ms | 83.6% lower |
| Standard deviation | 28.01 ms | 6.64 ms | 76.3% lower |

Average combined controller and LRC resources across five runs were:

| Resource | ROS 1 | ROS 2 |
|---|---:|---:|
| CPU | 237.55% | 19.51% |
| Resident memory | 768.20 MiB | 48.71 MiB |

CPU can exceed 100% when a process uses more than one CPU core.

## Interpretation

The current ROS 2 implementation completed the traced command pipeline with
lower typical latency, lower tail latency, and less timing variation than the
current ROS 1 implementation. Exact trace IDs make this conclusion stronger
than Experiment 1 because every controller and actuator command is tied to the
sensor frame that produced it.

The comparison does not prove that ROS 2 middleware or DDS alone caused the
improvement. The two implementations do not run identical image-processing
workloads, and the ROS 1 controller performs substantially more legacy image
processing. The latency and resource results therefore describe the complete
implementations tested on the Xavier, not an isolated ROS middleware benchmark.

## Deliverables

- `docs/testing/Experiment2-ros1-vs-ros2-comparison.md`
- `results/latency/experiment2/` — ten exact-trace reports and sample files
- `results/latency/resources/` — ten environment and CPU/memory pairs
- `results/latency/experiment2-comparison/data/experiment2-comparison.csv`
- `results/latency/experiment2-comparison/data/experiment2-summary.json`
- `results/latency/experiment2-comparison/plots/experiment2-latency-distributions.png`
- `results/latency/experiment2-comparison/plots/experiment2-end-to-end-by-run.png`
- `results/latency/experiment2-comparison/plots/experiment2-cpu-memory-comparison.png`
- `scripts/analyze_experiment2_comparison.py`

## Repository state

The raw Experiment 2 run data are pushed to GitHub through commit `fdf6e42`.
The final comparison report, generated summary, plots, comparison script, and
this dated work summary are currently local and should be reviewed before they
are committed and pushed.
