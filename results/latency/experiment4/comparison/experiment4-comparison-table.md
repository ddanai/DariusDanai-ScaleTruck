# Experiment 4 — ROS 1 vs. ROS 2 comparison

Matched-workload whole-system test on the Xavier; 30 runs per system. Values are means of run-level statistics. Negative ROS 2 − ROS 1 latency differences favor ROS 2.

| Metric | Statistic | ROS 1 (ms) | ROS 2 (ms) | ROS 2 − ROS 1 (ms) | 95% CI (ms) | CI excludes zero? |
|---|---:|---:|---:|---:|---:|:---:|
| Sensor to controller | Median | 26.52 | 20.47 | -6.06 | [-10.92, -0.92] | Yes |
| Sensor to controller | P95 | 30.14 | 39.93 | 9.79 | [-6.75, 28.92] | No |
| Controller to actuator | Median | 10.41 | 10.76 | 0.35 | [-0.34, 1.05] | No |
| Controller to actuator | P95 | 19.37 | 19.26 | -0.11 | [-0.69, 0.47] | No |
| End to end | Median | 36.51 | 31.69 | -4.82 | [-9.84, 0.51] | No |
| End to end | P95 | 46.87 | 56.68 | 9.81 | [-6.36, 28.41] | No |

## Topic timing

| Topic | System | Mean frequency (Hz) | Mean interarrival jitter (ms) |
|---|---:|---:|---:|
| Controller | ROS1 | 29.91 | 4.65 |
| Controller | ROS2 | 22.91 | 22.02 |
| Actuator | ROS1 | 29.95 | 10.71 |
| Actuator | ROS2 | 22.90 | 23.84 |

## Measurement-window resources

CPU and RSS were measured during the same five-second post-warm-up window used for latency. Both systems used standardized 50 Hz matched LRC adapters with equivalent logging behavior.

| System | Combined mean CPU (%) | Combined mean RSS (MiB) |
|---|---:|---:|
| ROS1 | 66.91 | 93.22 |
| ROS2 | 54.52 | 110.28 |
