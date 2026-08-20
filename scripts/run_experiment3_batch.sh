#!/usr/bin/env bash
set -euo pipefail

# Run this orchestrator on the Xavier host as the normal user, never inside Docker.
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ros1_bag="${ROS1_INPUT_BAG:-$HOME/left_camera_templergraben.bag}"
ros2_bag="${ROS2_INPUT_BAG:-/ros2_ws/bags/left_camera_templergraben_ros2}"
container="${ROS2_CONTAINER:-ros2-humble}"
results="$repo_dir/results/latency/experiment3/reports"

sequence=(
  ros1:01 ros2:01 ros2:02 ros1:02 ros1:03 ros2:03 ros2:04 ros1:04 ros1:05 ros2:05
  ros2:06 ros1:06 ros1:07 ros2:07 ros2:08 ros1:08 ros1:09 ros2:09 ros2:10 ros1:10
)

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run this script from the Xavier host as user krg, not as root or inside Docker" >&2
  exit 2
fi
command -v docker >/dev/null || { echo "docker is unavailable on the host" >&2; exit 2; }
command -v roscore >/dev/null || { echo "Source ROS 1 before running this script" >&2; exit 2; }
[[ -f "$ros1_bag" ]] || { echo "Missing ROS 1 bag: $ros1_bag" >&2; exit 2; }

stop_container() {
  docker stop "$container" >/dev/null 2>&1 || true
}
trap stop_container EXIT INT TERM

for item in "${sequence[@]}"; do
  system="${item%%:*}"
  run_id="${item##*:}"
  report="$results/${system}-trace-report-run-${run_id}.json"
  if [[ -f "$report" ]]; then
    echo "SKIP completed $system run $run_id"
    continue
  fi

  echo "START $system run $run_id"
  if [[ "$system" == "ros1" ]]; then
    stop_container
    bash -lc "source /opt/ros/noetic/setup.bash && source '$HOME/catkin_ws/devel/setup.bash' && cd '$repo_dir' && ./scripts/run_matched_xavier_benchmark.sh ros1 '$run_id' '$ros1_bag'"
  else
    docker start "$container" >/dev/null
    docker exec "$container" bash -lc \
      "source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_DOMAIN_ID=0 && cd /ros2_ws/src/DariusDanai-ScaleTruck && ./scripts/run_matched_xavier_benchmark.sh ros2 '$run_id' '$ros2_bag'"
  fi
  echo "ACCEPTED $system run $run_id"
done

stop_container
echo "All official Experiment 3 runs are complete."
echo "Next: python3 scripts/analyze_experiment3_comparison.py"
