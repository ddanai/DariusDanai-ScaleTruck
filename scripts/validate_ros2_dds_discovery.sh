#!/usr/bin/env bash
set -euo pipefail

if ! command -v ros2 >/dev/null 2>&1; then
  echo "ERROR: ros2 command not found. Source your ROS 2 setup first, for example:"
  echo "  source /opt/ros/humble/setup.bash"
  exit 1
fi

if ! ros2 pkg executables demo_nodes_cpp >/dev/null 2>&1; then
  echo "ERROR: demo_nodes_cpp is not available. Install ROS 2 demo nodes or run an equivalent talker node manually."
  exit 1
fi

echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-unset}"
echo "ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY:-unset}"
echo "Starting ROS 2 demo talker without roscore..."

ros2 run demo_nodes_cpp talker >/tmp/scale_truck_ros2_talker.log 2>&1 &
talker_pid=$!

cleanup() {
  if kill -0 "$talker_pid" >/dev/null 2>&1; then
    kill "$talker_pid" >/dev/null 2>&1 || true
    wait "$talker_pid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

for attempt in 1 2 3 4 5; do
  sleep 1

  if ros2 node list | grep -q '^/talker$' && ros2 topic list | grep -q '^/chatter$'; then
    echo "DDS discovery validation passed."
    echo "Discovered node: /talker"
    echo "Discovered topic: /chatter"
    exit 0
  fi

  echo "Waiting for DDS discovery... attempt ${attempt}/5"
done

echo "ERROR: DDS discovery validation failed."
echo "Talker log:"
cat /tmp/scale_truck_ros2_talker.log
exit 1

