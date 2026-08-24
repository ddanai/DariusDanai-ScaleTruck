# Experiment 4: preregistered 30-run matched benchmark

## Purpose and stopping rule

Experiment 4 repeats the matched ROS 1 versus ROS 2 Xavier benchmark with narrower run-level
confidence intervals and removes the implementation differences identified after Experiment 3.
The sample size is fixed **before data collection** at 30 accepted runs for ROS 1 and 30 accepted
runs for ROS 2. Do not calculate inferential results, inspect significance, or stop early. The
analysis script remains locked until run IDs 01 through 30 exist for both systems.

A run may be rejected only for a protocol failure (missing topic, incomplete five-second window,
wrong configuration, recorder failure, or corrupted output), never because its result is slow or
unfavorable. Repeat a rejected run with the same ID and record the reason.

## Frozen conditions

These conditions are identical for both systems and all 60 accepted runs:

| Condition | Frozen value |
|---|---|
| Camera data | `left_camera_templergraben`, 540 images; ROS 1 source SHA-256 `cce3dfa34d42a7e0278638ce9557e83fb66c6784c383e37c58892a511d01812b` |
| Playback rate | 1.0 (default; never pass a rate override) |
| Controller workload | `fnv1a-strided-v1`, 4 passes |
| LRC | matched benchmark adapter, 50 Hz timer, queue depth 1 |
| LRC logging | one startup configuration line; no per-cycle logging |
| Xavier power mode/clocks | `MODE_15W_DESKTOP` (mode 7), with `jetson_clocks` enabled |
| Warm-up | 1 second after the first `/xav2lrc_msg` |
| Measurement | the following 5 seconds |
| Middleware | ROS 2 `rmw_fastrtps_cpp`, domain 0; existing ROS 1 configuration |

The batch runner sets mode 7 and enables `jetson_clocks` before collection, then verifies the power
mode before every run. Run `sudo -v` first so those checks can remain noninteractive.

## Standardized LRC behavior

Official Experiment 4 runs use `matched_lrc_ros1.py` and `matched_lrc_ros2.py`. Both retain only the
latest controller command, publish the same output fields at 50 Hz, use a queue depth of one, and
emit no per-cycle logs. These adapters isolate ROS communication/runtime overhead; they do not claim
to compare the full production resiliency algorithms.

## Synchronized measurement window

The runner waits for the first nonzero controller trace, applies the one-second warm-up, and then
runs `pidstat` for exactly five one-second samples. The latency analyzer uses the same one-second
start and five-second duration. CPU and RSS summaries therefore describe the same interval as the
latency result, not process startup, playback delay, or teardown.

## Run and analyze

On the Xavier host, with ROS 1 sourced and the ROS 2 container installed:

```bash
chmod +x scripts/run_experiment4_batch.sh scripts/run_matched_xavier_benchmark.sh
./scripts/run_experiment4_batch.sh
python3 scripts/analyze_experiment4_comparison.py
```

The batch alternates which system runs first for each paired run ID. It resumes completed IDs but
does not change the fixed stopping point. The final command must fail until all 60 reports and their
sample/resource files are present.

## Acceptance checklist

- [ ] Exactly 30 accepted ROS 1 and 30 accepted ROS 2 runs.
- [ ] Same bag identity, playback rate, workload version, and workload passes in every run.
- [ ] Same recorded Xavier power mode and clock state in every environment file.
- [ ] Controller and actuator timing are consistent with the standardized 50 Hz LRC.
- [ ] Exactly five resource samples per process fall in each measured window.
- [ ] No negative latency, missing traces, protocol errors, or result-based exclusions.
- [ ] Analysis started only after collection reached the preregistered stopping point.
