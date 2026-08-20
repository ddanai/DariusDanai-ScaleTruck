# Experiment 3 — ROS 1 vs. ROS 2 comparison

Matched-workload whole-system test on the Xavier; 10 runs per system. Values are means of run-level statistics. Negative ROS 2 − ROS 1 latency differences favor ROS 2.

| Metric | Statistic | ROS 1 (ms) | ROS 2 (ms) | ROS 2 − ROS 1 (ms) | 95% CI (ms) | CI excludes zero? |
|---|---:|---:|---:|---:|---:|:---:|
| Sensor to controller | Median | 36.30 | 22.40 | -13.90 | [-22.59, -3.77] | Yes |
| Sensor to controller | P95 | 67.04 | 32.63 | -34.40 | [-53.98, -8.55] | Yes |
| Controller to actuator | Median | 1.73 | 10.76 | 9.03 | [7.96, 9.98] | Yes |
| Controller to actuator | P95 | 10.39 | 19.06 | 8.67 | [7.27, 10.01] | Yes |
| End to end | Median | 39.21 | 33.23 | -5.98 | [-14.35, 3.75] | No |
| End to end | P95 | 71.46 | 50.45 | -21.01 | [-39.69, 4.62] | No |

## Topic timing

| Topic | System | Mean frequency (Hz) | Mean interarrival jitter (ms) |
|---|---:|---:|---:|
| Controller | ROS1 | 26.19 | 19.42 |
| Controller | ROS2 | 25.46 | 13.14 |
| Actuator | ROS1 | 26.19 | 20.43 |
| Actuator | ROS2 | 25.49 | 15.70 |

## Session-level resources

Resource samples cover the benchmark session, including startup/discovery, rather than only the 5-second measurement window. ROS 1 and ROS 2 LRC nodes are not identical source implementations, so these values must not be interpreted as middleware-only costs.

| System | Combined mean CPU (%) | Combined mean RSS (MiB) |
|---|---:|---:|
| ROS1 | 138.36 | 158.01 |
| ROS2 | 3.36 | 73.92 |
