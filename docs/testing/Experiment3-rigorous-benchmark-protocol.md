# Experiment 3: rigorous and efficient ROS 1 versus ROS 2 benchmark

## What this experiment can answer

Choose one primary question before collecting data:

1. **Whole-system comparison:** compare the current ROS 1 and ROS 2 applications. Keep the
   hardware, input, run duration, and operating conditions fixed. Conclusions apply to these
   implementations, not to middleware alone.
2. **Middleware comparison:** port exactly the same computation and parameters to both systems,
   validate identical outputs, then vary only ROS/middleware. Do not use the existing Experiment 2
   resource numbers for this claim because the image-processing workloads differ.

The primary endpoint is per-run median end-to-end latency. Secondary endpoints are per-run p95,
trace completion rate, CPU, and RSS. Label p99 and maximum as exploratory unless runs are much longer.

## Design

- Use at least 10 independent runs per system for a defensible initial comparison; use a pilot-based
  power analysis to set the final count. More frames in one run do not replace more runs.
- Randomize or alternate execution order (for example, R1, R2, R2, R1) to reduce thermal and
  time-of-day bias. Record the planned order before testing.
- Restart the ROS graph between runs. Use a fixed warm-up period and exclude it symmetrically.
- Replay the exact same bag segment at the same rate. Use identical topic payloads and parameters.
- Lock Xavier power mode and clocks when scientifically appropriate; log CPU/GPU/EMC frequencies,
  temperature, throttling state, background processes, ROS/RMW versions, git commit, and command line.
- Synchronize clocks only if measurements cross machines. On one Xavier, use a monotonic clock for
  intervals; do not mix wall-clock and monotonic timestamps.
- Define rejection rules before collection: incomplete bag, duplicate relay, recorder failure,
  throttling, mismatched configuration, or trace completion below a chosen threshold. Preserve and
  report rejected runs; never discard a slow run merely because it is slow.

## Efficient run procedure

1. Generate a randomized run manifest with system, run ID, bag checksum, commit, warm-up, measured
   duration, and expected configuration.
2. Run one preflight check that verifies power/clocks, free disk, topic uniqueness, process list,
   and output paths before starting playback.
3. Start resource and trace recording from one wrapper command. Give every output a unique run ID and
   write to a temporary location, then mark it accepted only after validation succeeds.
4. Automatically validate trace IDs, nonnegative component latencies, sample count, completion rate,
   measurement duration, and environment consistency.
5. Regenerate tables and figures from raw files with one analysis command. Never copy values manually.

## Analysis and reporting

- Plot every run. Report pooled frame distributions only as descriptive visualizations.
- Treat the run as the experimental unit. Report the mean of per-run medians and p95 values, their
  between-run spread, and a run-cluster bootstrap 95% confidence interval for ROS 2 minus ROS 1.
- Report trace completion as `matched actuator traces / input traces`; unequal counts in Experiment 2
  (586 versus 690) make this essential in the next collection.
- Report absolute differences alongside percent changes. A confidence interval and practical latency
  threshold are more informative than a p-value alone.
- Keep CPU normalization explicit: process CPU may exceed 100%; also report utilization divided by the
  number of online cores when comparing machines.

## Current Experiment 2 limitations

- There are only five independent runs per system.
- ROS 1 and ROS 2 run different image-processing workloads.
- Systems were collected in blocks rather than a documented randomized/interleaved order.
- Input-frame totals and trace completion rates were not captured, so the unequal matched trace counts
  cannot be interpreted as drops versus different effective windows.
- Frequency/thermal data were recorded as snapshots, not continuously, and clocks were not locked.

These results remain useful as a pilot and whole-implementation comparison, but they are not an
isolated ROS 1 versus ROS 2 middleware benchmark.
