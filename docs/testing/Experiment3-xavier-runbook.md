# Experiment 3 Xavier runbook: matched-workload comparison

## Claim

Under matched application workloads, input data, hardware, and test conditions, the tested ROS 2
implementation has different control-pipeline latency and timing variability from the equivalent
ROS 1 implementation. Directional claims such as "lower" are made only after the results are analyzed.

This benchmark uses the same `matched_controller_workload.py` computation in thin ROS 1 and ROS 2
wrappers. It is a controlled benchmark workload, not the production lane-detection algorithm.

## One-time Xavier setup

1. Pull/copy this repository revision to the Xavier.
2. Install `sysstat`: `sudo apt-get install sysstat`.
3. Build both workspaces after confirming the trace fields exist in both message definitions.
4. Make the scripts executable:

   ```bash
   chmod +x scripts/run_matched_xavier_benchmark.sh scripts/record_xavier_resources.sh
   ```

5. Keep one ROS 1 version and one ROS 2 conversion of the same camera bag. Verify both contain the
   same image count, dimensions, encoding, and payloads.

## Before every test session

1. Disconnect the physical OpenCR and stop unrelated applications.
2. Set the selected Xavier power mode, then lock clocks for repeatability:

   ```bash
   sudo nvpmodel -m 7
   sudo jetson_clocks
   sudo nvpmodel -q
   sudo jetson_clocks --show
   sudo -v
   ```

3. Confirm the repository revision with `git rev-parse HEAD` and confirm there are no unintended edits
   with `git status --short`.
4. Run one uncounted pilot per system. Inspect `results/latency/experiment3/logs/` and correct every
   error before official collection.

## Official collection

Use ten run IDs and this interleaved order:

`R1-01, R2-01, R2-02, R1-02, R1-03, R2-03, R2-04, R1-04, R1-05, R2-05,
R2-06, R1-06, R1-07, R2-07, R2-08, R1-08, R1-09, R2-09, R2-10, R1-10`.

For each ROS 1 entry, open a fresh terminal and source ROS 1 plus the catkin workspace:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
./scripts/run_matched_xavier_benchmark.sh ros1 01 ~/left_camera_templergraben.bag
```

For each ROS 2 entry, open a fresh terminal and source ROS 2 plus the colcon workspace:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_humble_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
./scripts/run_matched_xavier_benchmark.sh ros2 01 /path/to/converted_ros2_bag
```

Change only the run ID. The wrapper starts the relay, matched controller, LRC, trace recorder, and
PID-specific resource recorder; plays the bag; stops recording; and analyzes the run. It refuses to
overwrite an existing report.

After each run, check that the command says `Completed`, inspect its logs, and compare matched-trace
counts. Preserve failed runs and write the rejection reason; rerun with a new ID rather than deleting
evidence. Never reject a run simply because it is slow.

## Final validation and analysis

After all runs, execute from any Python 3 environment containing matplotlib:

```bash
python3 scripts/analyze_experiment3_comparison.py
python3 -m unittest discover -s tests -v
```

The aggregator fails if ROS 1 and ROS 2 run IDs differ, sample files are missing, a run contains no
matched traces, or a latency is negative. Review the generated
`results/latency/experiment3/comparison/experiment3-summary.json`.

Report the mean per-run median and p95, ROS 2 minus ROS 1 absolute differences, run-level bootstrap
95% confidence intervals, matched trace counts, CPU, RSS, and all rejected runs. The run—not each
camera frame—is the independent experimental unit.
