#!/usr/bin/env bash
set -euo pipefail

# Preregistered stopping rule: complete all 30 accepted runs per system.
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ros1_bag="${ROS1_INPUT_BAG:-$HOME/left_camera_templergraben.bag}"
ros2_bag="${ROS2_INPUT_BAG:-/ros2_ws/bags/left_camera_templergraben_ros2}"
container="${ROS2_CONTAINER:-ros2-humble}"
results="$repo_dir/results/latency/experiment4/reports"

if [[ "$(id -u)" -eq 0 ]]; then echo "Run on the Xavier host as the normal user" >&2; exit 2; fi
command -v docker >/dev/null || { echo "docker is unavailable" >&2; exit 2; }
command -v roscore >/dev/null || { echo "Source ROS 1 first" >&2; exit 2; }
[[ -f "$ros1_bag" ]] || { echo "Missing ROS 1 bag: $ros1_bag" >&2; exit 2; }
sudo -n true 2>/dev/null || { echo "Run sudo -v before starting Experiment 4" >&2; exit 2; }
# Freeze the Xavier at the same mode observed in Experiment 3 and lock clocks for every run.
sudo -n nvpmodel -m 7
sudo -n jetson_clocks

stop_container() { docker stop "$container" >/dev/null 2>&1 || true; }
trap stop_container EXIT INT TERM

for run_id in $(seq -w 1 30); do
  # Alternating order balances drift while retaining paired run IDs.
  if (( 10#$run_id % 2 )); then systems=(ros1 ros2); else systems=(ros2 ros1); fi
  for system in "${systems[@]}"; do
    report="$results/${system}-trace-report-run-${run_id}.json"
    [[ -f "$report" ]] && { echo "SKIP completed $system run $run_id"; continue; }
    sudo -n nvpmodel -q 2>&1 | grep -q "MODE_15W_DESKTOP" || {
      echo "Xavier is not in frozen MODE_15W_DESKTOP (mode 7)" >&2; exit 2; }
    echo "START $system run $run_id of preregistered 30"
    if [[ "$system" == ros1 ]]; then
      stop_container
      bash -lc "source /opt/ros/noetic/setup.bash && source '$HOME/catkin_ws/devel/setup.bash' && cd '$repo_dir' && EXPERIMENT_ROOT=results/latency/experiment4 ./scripts/run_matched_xavier_benchmark.sh ros1 '$run_id' '$ros1_bag'"
    else
      docker start "$container" >/dev/null
      docker exec "$container" bash -lc "source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_DOMAIN_ID=0 && cd /ros2_ws/src/DariusDanai-ScaleTruck && EXPERIMENT_ROOT=results/latency/experiment4 ./scripts/run_matched_xavier_benchmark.sh ros2 '$run_id' '$ros2_bag'"
    fi
  done
done
echo "All 30 runs per system are complete; analysis is now permitted."
