#!/usr/bin/env python3
"""Validate and aggregate matched-workload Xavier benchmark runs."""

import csv
import importlib.util
import json
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results" / "latency" / "experiment3"
REPORTS = BASE / "reports"
SAMPLES = BASE / "samples"
OUTPUT = BASE / "comparison"
RESOURCES = BASE / "resources"
METRICS = {
    "sensor_to_controller": "sensor_to_controller_ms",
    "controller_to_actuator_command": "controller_to_actuator_ms",
    "end_to_end_command": "end_to_end_ms",
}

spec = importlib.util.spec_from_file_location(
    "comparison_common", Path(__file__).with_name("analyze_experiment2_comparison.py"))
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)


def discover(system):
    prefix = f"{system}-trace-report-run-"
    runs = {}
    for report in REPORTS.glob(f"{prefix}*.json"):
        run_id = int(report.stem.rsplit("-", 1)[1])
        sample = SAMPLES / report.name.replace("report", "samples").replace(".json", ".csv")
        if not sample.exists():
            raise RuntimeError(f"Missing samples for {report}")
        values = {metric: [] for metric in METRICS}
        with sample.open(newline="") as handle:
            for row in csv.DictReader(handle):
                for metric, column in METRICS.items():
                    value = float(row[column])
                    if value < 0:
                        raise RuntimeError(f"Negative latency in {sample}")
                    values[metric].append(value)
        if not values["end_to_end_command"]:
            raise RuntimeError(f"No matched traces in {sample}")
        runs[run_id] = values
    return runs


def resource_run(system, run_id):
    environment = RESOURCES / f"{system}-run-{run_id:02d}-environment.txt"
    samples = RESOURCES / f"{system}-run-{run_id:02d}-cpu-memory.txt"
    settings = {}
    for line in environment.read_text(errors="replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            settings[key] = value
    expected = {
        "controller": int(settings["controller_pid"]),
        "lrc": int(settings["lrc_pid"]),
    }
    rows = {role: [] for role in expected}
    by_pid = {pid: role for role, pid in expected.items()}
    for line in samples.read_text(errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 16 or parts[1] not in {"AM", "PM"}:
            continue
        try:
            pid = int(parts[3])
            if pid in by_pid:
                rows[by_pid[pid]].append((float(parts[8]), float(parts[13]) / 1024.0))
        except ValueError:
            continue
    result = {}
    for role, values in rows.items():
        if not values:
            raise RuntimeError(f"No resource samples for {role} in {samples}")
        result[role] = {
            "cpu_pct": statistics.mean(value[0] for value in values),
            "rss_mib": statistics.mean(value[1] for value in values),
        }
    result["combined"] = {
        field: result["controller"][field] + result["lrc"][field]
        for field in ["cpu_pct", "rss_mib"]
    }
    return result


def main():
    runs = {system: discover(system) for system in ["ros1", "ros2"]}
    if not runs["ros1"] or not runs["ros2"]:
        raise RuntimeError("Need at least one ROS 1 and one ROS 2 run")
    if set(runs["ros1"]) != set(runs["ros2"]):
        raise RuntimeError(
            f"Run IDs must match: ROS1={sorted(runs['ros1'])}, ROS2={sorted(runs['ros2'])}")

    summary = {
        "design": "matched-workload whole-system comparison",
        "experimental_unit": "run",
        "run_ids": sorted(runs["ros1"]),
        "metrics": {},
        "topic_timing": {},
        "resources": {},
    }
    for metric in METRICS:
        summary["metrics"][metric] = {}
        per_system = {}
        for system in ["ros1", "ros2"]:
            medians = common.run_level_estimate(runs[system], metric, "median")
            p95s = common.run_level_estimate(runs[system], metric, "p95")
            per_system[system] = {"median": medians, "p95": p95s}
            summary["metrics"][metric][system] = {
                "matched_traces_per_run": [len(runs[system][run][metric]) for run in sorted(runs[system])],
                "mean_per_run_median_ms": statistics.mean(medians),
                "mean_per_run_p95_ms": statistics.mean(p95s),
            }
        summary["metrics"][metric]["ros2_minus_ros1_median_ms"] = common.bootstrap_difference(
            per_system["ros1"]["median"], per_system["ros2"]["median"])
        summary["metrics"][metric]["ros2_minus_ros1_p95_ms"] = common.bootstrap_difference(
            per_system["ros1"]["p95"], per_system["ros2"]["p95"])

    for topic in ["controller", "actuator"]:
        summary["topic_timing"][topic] = {}
        for system in ["ros1", "ros2"]:
            frequencies = []
            jitters = []
            for run_id in sorted(runs[system]):
                path = REPORTS / f"{system}-trace-report-run-{run_id:02d}.json"
                report = json.loads(path.read_text())
                item = report.get("topic_timing", {}).get(topic)
                if not item or item["frequency_hz"] is None or item["interarrival_ms"] is None:
                    raise RuntimeError(f"Missing topic timing in {path}; reanalyze this run")
                frequencies.append(item["frequency_hz"])
                jitters.append(item["interarrival_ms"]["stddev"])
            summary["topic_timing"][topic][system] = {
                "frequency_hz_per_run": frequencies,
                "mean_frequency_hz": statistics.mean(frequencies),
                "interarrival_jitter_ms_per_run": jitters,
                "mean_interarrival_jitter_ms": statistics.mean(jitters),
            }

    for system in ["ros1", "ros2"]:
        resource_runs = [resource_run(system, run_id) for run_id in sorted(runs[system])]
        summary["resources"][system] = {}
        for role in ["controller", "lrc", "combined"]:
            summary["resources"][system][role] = {}
            for field in ["cpu_pct", "rss_mib"]:
                values = [run[role][field] for run in resource_runs]
                summary["resources"][system][role][field] = {
                    "per_run": values,
                    "mean": statistics.mean(values),
                    "run_stddev": statistics.pstdev(values),
                }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / "experiment3-summary.json"
    destination.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
