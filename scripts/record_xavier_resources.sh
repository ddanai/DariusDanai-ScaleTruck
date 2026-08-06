#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 SYSTEM RUN_NUMBER DURATION_SECONDS" >&2
  echo "Example: $0 ros2 01 35" >&2
  exit 2
fi

system="$1"
run="$2"
duration="$3"
output_dir="results/latency/resources"
prefix="$output_dir/${system}-run-${run}"
mkdir -p "$output_dir"

{
  echo "system=$system"
  echo "run=$run"
  echo "utc_start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "duration_s=$duration"
  echo "hostname=$(hostname)"
  echo "kernel=$(uname -srmo)"
  echo "ros_distro=${ROS_DISTRO:-unset}"
  echo "ros_domain_id=${ROS_DOMAIN_ID:-0}"
  echo "rmw_implementation=${RMW_IMPLEMENTATION:-default}"
  echo "network_interfaces:"
  ip -brief link 2>&1 || true
  echo "xavier_power_mode:"
  if command -v nvpmodel >/dev/null 2>&1; then
    if sudo -n true 2>/dev/null; then
      sudo -n nvpmodel -q 2>&1 || true
    else
      echo "sudo credentials unavailable; run 'sudo -v' before this script"
    fi
  else
    echo "nvpmodel unavailable"
  fi
  echo "xavier_clocks:"
  if command -v jetson_clocks >/dev/null 2>&1; then
    if sudo -n true 2>/dev/null; then
      sudo -n jetson_clocks --show 2>&1 || true
    else
      echo "sudo credentials unavailable; run 'sudo -v' before this script"
    fi
  else
    echo "jetson_clocks unavailable"
  fi
} > "${prefix}-environment.txt"

if ! command -v pidstat >/dev/null 2>&1; then
  echo "pidstat is missing. Install it with: sudo apt-get install sysstat" >&2
  exit 2
fi

pidstat -h -u -r -p ALL 1 "$duration" > "${prefix}-cpu-memory.txt"
echo "utc_end=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "${prefix}-environment.txt"
echo "Wrote ${prefix}-environment.txt"
echo "Wrote ${prefix}-cpu-memory.txt"
