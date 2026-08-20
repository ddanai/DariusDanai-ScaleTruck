#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 5 ]]; then
  echo "Usage: $0 ros1|ros2 RUN_ID INPUT_BAG [START_S=1] [DURATION_S=5]" >&2
  echo "Run from a terminal where the selected ROS and workspace are already sourced." >&2
  exit 2
fi

system="$1"
run_id=$(printf "%02d" "$((10#$2))")
input_bag="$3"
start_s="${4:-1}"
duration_s="${5:-5}"
root="results/latency/experiment3"
bag_root="$root/bags"
report_root="$root/reports"
sample_root="$root/samples"
resource_root="$root/resources"
log_root="$root/logs"
mkdir -p "$bag_root" "$report_root" "$sample_root" "$resource_root" "$log_root"

if [[ "$system" != "ros1" && "$system" != "ros2" ]]; then
  echo "SYSTEM must be ros1 or ros2" >&2
  exit 2
fi
if [[ ! -e "$input_bag" ]]; then
  echo "Input bag does not exist: $input_bag" >&2
  exit 2
fi
if [[ -e "$report_root/${system}-trace-report-run-${run_id}.json" ]]; then
  echo "Run $system-$run_id already exists; choose a new ID" >&2
  exit 2
fi
command -v pidstat >/dev/null || { echo "Install sysstat first" >&2; exit 2; }
available_kib=$(df -Pk . | awk 'NR==2 {print $4}')
if [[ "$available_kib" -lt 204800 ]]; then
  echo "Less than 200 MiB free in the results filesystem; free space before testing" >&2
  exit 2
fi

pids=()
cleanup() {
  for pid in "${pids[@]:-}"; do
    kill -INT -- "-$pid" 2>/dev/null || kill -INT "$pid" 2>/dev/null || true
  done
  sleep 2
  for pid in "${pids[@]:-}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT INT TERM

if [[ "$system" == "ros1" ]]; then
  command -v roscore >/dev/null || { echo "ROS 1 is not sourced" >&2; exit 2; }
  if ! rosnode list >/dev/null 2>&1; then
    setsid roscore > "$log_root/${system}-${run_id}-roscore.log" 2>&1 & pids+=("$!")
    sleep 3
  fi
  setsid python3 scripts/experiment2_restamp_ros1_images.py > "$log_root/${system}-${run_id}-relay.log" 2>&1 & relay_pid="$!"; pids+=("$relay_pid")
  setsid python3 scripts/matched_controller_ros1.py > "$log_root/${system}-${run_id}-controller.log" 2>&1 & controller_pid="$!"; pids+=("$controller_pid")
  setsid rosrun scale_truck_control LRC > "$log_root/${system}-${run_id}-lrc.log" 2>&1 & lrc_launcher_pid="$!"; pids+=("$lrc_launcher_pid")
  sleep 4
  lrc_pid=$(pgrep -P "$lrc_launcher_pid" | head -1 || true); lrc_pid="${lrc_pid:-$lrc_launcher_pid}"
  setsid rosbag record --min-space=100M -O "$bag_root/${system}-run-${run_id}.bag" /xav2lrc_msg /lrc2ocr_msg > "$log_root/${system}-${run_id}-record.log" 2>&1 & recorder_pid="$!"; pids+=("$recorder_pid")
  RESOURCE_OUTPUT_DIR="$resource_root" RESOURCE_PIDS="$controller_pid,$lrc_pid" CONTROLLER_PID="$controller_pid" LRC_PID="$lrc_pid" \
    scripts/record_xavier_resources.sh "$system" "$run_id" "$((duration_s + start_s + 15))" > "$log_root/${system}-${run_id}-resources.log" 2>&1 & resource_pid="$!"; pids+=("$resource_pid")
  sleep 2
  kill -0 "$recorder_pid" 2>/dev/null || { echo "Recorder exited before playback; inspect the record log" >&2; exit 1; }
  rosbag play --delay=10 "$input_bag" /sensors/camera/left/image_raw:=/experiment2/input_image
  sleep 2
  kill -INT "$recorder_pid" 2>/dev/null || true
  wait "$recorder_pid" 2>/dev/null || true
  python3 scripts/analyze_experiment2_ros1_trace_latency.py \
    "$bag_root/${system}-run-${run_id}.bag" --start "$start_s" --duration "$duration_s" \
    --output "$report_root/${system}-trace-report-run-${run_id}.json" \
    --csv "$sample_root/${system}-trace-samples-run-${run_id}.csv"
else
  command -v ros2 >/dev/null || { echo "ROS 2 is not sourced" >&2; exit 2; }
  setsid python3 scripts/experiment2_restamp_ros2_images.py > "$log_root/${system}-${run_id}-relay.log" 2>&1 & relay_pid="$!"; pids+=("$relay_pid")
  setsid python3 scripts/matched_controller_ros2.py > "$log_root/${system}-${run_id}-controller.log" 2>&1 & controller_pid="$!"; pids+=("$controller_pid")
  setsid ros2 run scale_truck_control lrc_node > "$log_root/${system}-${run_id}-lrc.log" 2>&1 & lrc_launcher_pid="$!"; pids+=("$lrc_launcher_pid")
  sleep 4
  lrc_pid=$(pgrep -P "$lrc_launcher_pid" | head -1 || true); lrc_pid="${lrc_pid:-$lrc_launcher_pid}"
  setsid ros2 bag record -o "$bag_root/${system}-run-${run_id}" /xav2lrc_msg /lrc2ocr_msg > "$log_root/${system}-${run_id}-record.log" 2>&1 & recorder_pid="$!"; pids+=("$recorder_pid")
  RESOURCE_OUTPUT_DIR="$resource_root" RESOURCE_PIDS="$controller_pid,$lrc_pid" CONTROLLER_PID="$controller_pid" LRC_PID="$lrc_pid" \
    scripts/record_xavier_resources.sh "$system" "$run_id" "$((duration_s + start_s + 15))" > "$log_root/${system}-${run_id}-resources.log" 2>&1 & resource_pid="$!"; pids+=("$resource_pid")
  sleep 2
  kill -0 "$recorder_pid" 2>/dev/null || { echo "Recorder exited before playback; inspect the record log" >&2; exit 1; }
  ros2 bag play "$input_bag" --delay 10 --remap /sensors/camera/left/image_raw:=/experiment2/input_image
  sleep 2
  kill -INT "$recorder_pid" 2>/dev/null || true
  wait "$recorder_pid" 2>/dev/null || true
  python3 scripts/analyze_experiment2_ros2_trace_latency.py \
    "$bag_root/${system}-run-${run_id}" --start "$start_s" --duration "$duration_s" \
    --output "$report_root/${system}-trace-report-run-${run_id}.json" \
    --csv "$sample_root/${system}-trace-samples-run-${run_id}.csv"
fi

echo "Completed $system run $run_id"
