# Experiment 2: ROS 1 vs. ROS 2 exact-trace comparison

## Test design

Five ROS 1 and five ROS 2 runs replayed the same public camera bag on the same Xavier. Messages carried a trace ID and sensor acquisition timestamp. Power mode, online CPUs, and WLAN state matched across all runs; ROS 2 used `rmw_fastrtps_cpp`.

## Latency comparison (pooled exact traces)

| Metric | System | Samples | Mean (ms) | Median (ms) | p95 (ms) | p99 (ms) | Max (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sensor to controller | ROS1 | 586 | 35.43 | 28.22 | 80.02 | 159.99 | 220.96 |
| Sensor to controller | ROS2 | 690 | 14.37 | 13.57 | 25.03 | 28.23 | 32.16 |
| Controller to actuator | ROS1 | 586 | 10.08 | 5.99 | 32.32 | 65.15 | 107.24 |
| Controller to actuator | ROS2 | 690 | 2.16 | 2.00 | 2.49 | 6.70 | 21.16 |
| End to end | ROS1 | 586 | 45.51 | 40.00 | 93.33 | 173.30 | 235.62 |
| End to end | ROS2 | 690 | 16.52 | 15.59 | 27.85 | 31.52 | 38.61 |

## Xavier resource comparison

Values are means across five runs. CPU can exceed 100% when a process uses more than one core.

| Process | System | CPU mean (%) | CPU run SD | RSS mean (MiB) | RSS run SD |
|---|---:|---:|---:|---:|---:|
| Controller | ROS1 | 144.64 | 7.32 | 656.70 | 78.89 |
| Controller | ROS2 | 9.85 | 0.33 | 27.55 | 0.76 |
| LRC | ROS1 | 92.90 | 1.22 | 111.50 | 1.20 |
| LRC | ROS2 | 9.66 | 0.57 | 21.16 | 0.33 |
| Combined | ROS1 | 237.55 | 8.49 | 768.20 | 79.40 |
| Combined | ROS2 | 19.51 | 0.83 | 48.71 | 0.97 |

## Final analysis

- ROS 2 reduced pooled median end-to-end latency from 40.00 ms to 15.59 ms (61.0% lower).
- ROS 2 reduced pooled p95 end-to-end latency from 93.33 ms to 27.85 ms (70.2% lower).
- End-to-end standard deviation fell from 28.01 ms to 6.64 ms, indicating more consistent timing in this implementation.
- Using runs as the experimental units, the ROS 2 minus ROS 1 difference in the mean per-run median was -23.97 ms (run-cluster bootstrap 95% CI -25.99 to -22.03 ms).
- The corresponding difference in the mean per-run p95 was -70.09 ms (95% CI -81.06 to -58.84 ms).
- Pooled frame counts are descriptive only; frames within one replay are correlated and must not be treated as independent replicates.
- The exact trace fields remove the main Experiment 1 uncertainty: controller and actuator commands are matched to the sensor frame that actually produced them.
- This experiment compares the current ROS 1 and ROS 2 implementations, not middleware alone. The image-processing workloads are not identical, so lower ROS 2 latency and resource use cannot be attributed only to ROS 2 or DDS.

## Plots

- `plots/experiment2-latency-distributions.png`: pooled exact-trace ECDFs.
- `plots/experiment2-end-to-end-by-run.png`: per-run median and p95 latency.
- `plots/experiment2-cpu-memory-comparison.png`: controller/LRC CPU and memory.
