# Experiment 3 Xavier runbook: matched-workload comparison

## Research question and claim

**Question:** Under matched application workload, camera input, Xavier hardware, and operating
conditions, does the ROS 2 scale-truck implementation improve latency, publishing frequency, timing
variability, CPU usage, and memory usage relative to the equivalent ROS 1 implementation?

**Claim to evaluate:** Under matched conditions, the tested ROS 2 implementation has different
control-pipeline latency and timing variability from the equivalent ROS 1 implementation. Say that
ROS 2 is "lower" or "better" only if the new results and confidence intervals support that direction.

This benchmark uses the same `matched_controller_workload.py` computation through thin ROS 1 and
ROS 2 wrappers. It is a controlled application workload, not the production lane-detection algorithm.

## Terminal guide

- **Host/ROS 1 terminal:** prompt resembles `krg@ubuntu:~$`. Use it for Git, file permissions, ROS 1,
  Xavier configuration, and ROS 1 runs.
- **ROS 2 container terminal:** prompt resembles `root@ubuntu:/ros2_ws#`. Use it for ROS 2 builds and
  ROS 2 runs. Enter it from the host with `docker start -ai ros2-humble`.
- Do not source ROS 1 and ROS 2 in the same shell.

## Phase 1: update and identify the source code

In the host terminal:

```bash
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
git pull
git status --short
git rev-parse HEAD
```

Record the commit hash in the experiment notes.

**Check:** Did `git pull` finish without an error, and are there no unexplained files in
`git status --short`? If no, stop and resolve the repository state before testing.

## Phase 2: install the measurement dependency

In the host terminal:

```bash
sudo apt-get update
sudo apt-get install sysstat
pidstat --version
```

**Check:** Does `pidstat --version` print version information? If no, do not continue.

## Phase 3: build ROS 1 and ROS 2

Build ROS 1 in the host terminal:

```bash
source /opt/ros/noetic/setup.bash
cd ~/catkin_ws
catkin_make
source ~/catkin_ws/devel/setup.bash
```

**Check:** Did `catkin_make` finish without failed packages?

Build ROS 2 in the container. From a host terminal, enter the container:

```bash
docker start -ai ros2-humble
```

When the prompt becomes `root@ubuntu:/ros2_ws#`, run:

```bash
echo $ROS_DISTRO
cd /ros2_ws
colcon build --symlink-install
source /ros2_ws/install/setup.bash
```

**Check:** Does `echo $ROS_DISTRO` print `humble`, and did `colcon build` report zero failed
packages? If no, fix the build before testing.

## Phase 4: make the scripts executable

Run this once in the host terminal:

```bash
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
chmod +x scripts/run_matched_xavier_benchmark.sh
chmod +x scripts/record_xavier_resources.sh
chmod +x scripts/experiment2_restamp_ros1_images.py
chmod +x scripts/experiment2_restamp_ros2_images.py
```

Verify:

```bash
test -x scripts/run_matched_xavier_benchmark.sh && echo "benchmark script ready"
```

**Check:** Does the terminal print `benchmark script ready`? If no, repeat the permission command.

## Phase 5: prepare and verify the input bags

Use the original rosbag1 camera bag for ROS 1 and a rosbag2 conversion of that exact file for ROS 2.
Do not merely create a conversion and assume it is correct. Perform every check below. Keep the ROS 2
bag inside the shared repository so the container can read it:

```text
~/ros2_humble_ws/src/DariusDanai-ScaleTruck/test-data/left_camera_ros2
```

### 5.1 Inspect the ROS 1 bag

In the host/ROS 1 terminal:

```bash
rosbag info ~/left_camera_templergraben.bag
```

Record these values:

- image topic, expected to be `/sensors/camera/left/image_raw`;
- image count, expected to be 540;
- message type, expected to be `sensor_msgs/Image`;
- duration, expected to be approximately 18 seconds; and
- frequency, expected to be approximately 30 Hz.

Inspect one image header:

```bash
rostopic echo -b ~/left_camera_templergraben.bag -n 1 \
  /sensors/camera/left/image_raw/header
```

Inspect the image dimensions and encoding:

```bash
rostopic echo -b ~/left_camera_templergraben.bag -n 1 \
  /sensors/camera/left/image_raw | grep -E "height:|width:|encoding:|step:"
```

Record the reported height, width, encoding, and step. Save a checksum identifying the source bag:

```bash
sha256sum ~/left_camera_templergraben.bag
```

Copy the checksum into the experiment notes.

**Check:** Did the ROS 1 bag report 540 images over approximately 18 seconds at approximately 30 Hz?
Did the image inspection print valid dimensions and encoding? If no, stop and investigate the bag.

### 5.2 Create the ROS 2 conversion

If a conversion already exists and its source is documented as this exact ROS 1 bag checksum, it can
be reused. Otherwise, recreate it to eliminate uncertainty.

Check for the converter in the host terminal:

```bash
rosbags-convert --help
```

If the command exists, create the conversion in the shared repository. In the installed converter,
the source path is positional; there is no `--src` option. Convert only the image topic required by
the benchmark:


```bash
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
mkdir -p test-data
rosbags-convert \
  ~/left_camera_templergraben.bag \
  --dst test-data/left_camera_ros2 \
  --include-topic /sensors/camera/left/image_raw
```

Confirm that the destination contains `metadata.yaml` and at least one `.db3` file:

```bash
ls -l test-data/left_camera_ros2
```

**Check:** Are `metadata.yaml` and a `.db3` file present? If no, the conversion did not complete. If
the command reports `unrecognized arguments: --src`, remove `--src` and pass the source path exactly
as shown above.

### 5.3 Inspect the ROS 2 bag

Open the ROS 2 container from the host:

```bash
docker start -ai ros2-humble
```

Inside the container:

```bash
source /opt/ros/humble/setup.bash
ros2 bag info /ros2_ws/src/DariusDanai-ScaleTruck/test-data/left_camera_ros2
```

Record the ROS 2 image topic, count, message type, duration, and approximate frequency. ROS 2 may show
the type as `sensor_msgs/msg/Image`; this is the ROS 2 form of `sensor_msgs/Image`.

### 5.4 Compare ROS 1 and ROS 2 bag information

Confirm all of the following:

- both contain the same image topic;
- both contain 540 image messages;
- both use the Image message type;
- both last approximately 18 seconds;
- both represent approximately 30 images per second;
- the recorded height, width, encoding, and step are unchanged; and
- the ROS 2 bag was converted directly from the ROS 1 bag whose checksum was recorded.

**Check:** Are all seven statements true? If any answer is no, do not use the bags for the official
comparison.

### 5.5 Use the same playback rate

The automated runner uses the default playback rate of 1.0 for both systems. Do not add a different
rate to either system. The equivalent manual commands are:

```bash
rosbag play --rate 1.0 ~/left_camera_templergraben.bag
```

and, inside the ROS 2 container:

```bash
ros2 bag play /ros2_ws/src/DariusDanai-ScaleTruck/test-data/left_camera_ros2 --rate 1.0
```

These manual playback commands are examples only; do not run them at the same time as the automated
benchmark.

### 5.6 Confirm contents through the pilot runs

During Phases 7 through 9, confirm:

- similar input duration;
- the same image dimensions and encoding;
- the same matched-workload version and pass count;
- similar processed-frame counts; and
- identical controller command values for corresponding input frames.

The experiment record should state:

> The ROS 2 bag was generated directly from the recorded ROS 1 bag without modifying the image
> messages, and both bags were replayed at rate 1.0.

Do not commit either test bag to Git because the files are large. Keep them under `test-data/`, which
should remain untracked or ignored.

## Phase 6: prepare the Xavier before each test session

Disconnect the physical OpenCR and close unrelated applications. In the host terminal:

```bash
sudo nvpmodel -m 7
sudo jetson_clocks
sudo nvpmodel -q
sudo jetson_clocks --show
sudo -v
```

Use the same power mode and clock settings for every run. Do not run `top`, plotting programs, builds,
or other workloads during measurement.

**Check:** Is the reported power mode the planned mode, are the intended CPUs online, and are clocks
configured consistently? If no, fix the configuration before starting a run.

## Phase 7: run an uncounted ROS 1 pilot

Open a fresh host terminal:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
sudo -v
./scripts/run_matched_xavier_benchmark.sh ros1 90 ~/left_camera_templergraben.bag
```

**Check:** Did the command finish with `Completed ros1 run 90`? If no, inspect:

```bash
grep -RiE "error|failed|exception" results/latency/experiment3/logs
```

Correct the cause before continuing.

## Phase 8: run an uncounted ROS 2 pilot

From the host, enter the container:

```bash
docker start -ai ros2-humble
```

Inside the container:

```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
cd /ros2_ws/src/DariusDanai-ScaleTruck
./scripts/run_matched_xavier_benchmark.sh ros2 90 test-data/left_camera_ros2
```

**Check:** Did the command finish with `Completed ros2 run 90`? If no, inspect the logs and fix the
cause. Run ID 90 is a pilot and must not be included in the official analysis.

## Phase 9: validate the pilots

In either environment, from the repository, inspect the outputs:

```bash
ls results/latency/experiment3/reports
ls results/latency/experiment3/samples
ls results/latency/experiment3/resources
grep -Rh "matched workload=" results/latency/experiment3/logs
```

**Check all of the following:**

- Do both controller logs show `fnv1a-strided-v1` and `passes=8`?
- Do both reports contain nonzero matched-trace counts?
- Are ROS 1 and ROS 2 processed-frame counts reasonably close?
- Are all latencies nonnegative?
- Do controller and actuator frequencies match the bag rate reasonably closely?
- Did both resource files capture the controller and LRC processes?
- Do equivalent input frames produce equivalent controller command values?

If any answer is no, stop and fix it before collecting official data.

## Phase 10: collect 10 official runs per system

Use this interleaved order to reduce temperature and time-order bias:

```text
R1-01, R2-01, R2-02, R1-02, R1-03, R2-03, R2-04, R1-04, R1-05, R2-05,
R2-06, R1-06, R1-07, R2-07, R2-08, R1-08, R1-09, R2-09, R2-10, R1-10
```

For each ROS 1 entry, use a fresh host terminal:

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
./scripts/run_matched_xavier_benchmark.sh ros1 01 ~/left_camera_templergraben.bag
```

For each ROS 2 entry, use the container:

```bash
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
cd /ros2_ws/src/DariusDanai-ScaleTruck
./scripts/run_matched_xavier_benchmark.sh ros2 01 test-data/left_camera_ros2
```

Change only the system and run number according to the sequence.

**After every run ask:** Did it print `Completed`? Are the expected report, sample, resource, and log
files present? If no, record the failure reason and investigate it. Preserve failed-run evidence and
use a new run ID; never reject a run merely because its measured performance is slow.

## Phase 11: generate and validate the final comparison

After ROS 1 and ROS 2 both have accepted run IDs 01 through 10, run from the repository:

```bash
python3 scripts/analyze_experiment3_comparison.py
python3 -m unittest discover -s tests -v
```

The analyzer intentionally stops if run IDs differ, sample files are missing, a run contains no
matched traces, resource samples are missing, timing data are absent, or latency is negative.

**Check:** Did the analyzer write
`results/latency/experiment3/comparison/experiment3-summary.json`, and did every automated test pass?
If no, do not prepare the final table until the error is resolved.

## Phase 12: prepare the deliverables

Create the ROS 1 versus ROS 2 table from the generated summary. Report:

- mean per-run sensor-to-controller, controller-to-actuator, and end-to-end median latency;
- mean per-run end-to-end p95 latency;
- ROS 2 minus ROS 1 absolute differences and run-level bootstrap 95% confidence intervals;
- controller and actuator publishing frequency and inter-arrival jitter;
- controller, LRC, and combined CPU and RSS memory;
- matched traces per run; and
- every rejected run and its documented reason.

**Final question:** Do the confidence intervals and practical differences support saying ROS 2 is
better, or do they support only saying the implementations differ? Use the answer shown by the data.
The run—not each camera frame—is the independent experimental unit.
