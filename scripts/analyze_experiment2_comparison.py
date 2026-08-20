#!/usr/bin/env python3
"""Aggregate Experiment 2 trace latency and Xavier resource measurements."""

import csv
import json
from pathlib import Path
import random
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "latency" / "experiment2"
RESOURCES = ROOT / "results" / "latency" / "resources"
OUTPUT = ROOT / "results" / "latency" / "experiment2-comparison"
PLOTS = OUTPUT / "plots"
DATA = OUTPUT / "data"

METRICS = [
    ("sensor_to_controller", "Sensor to controller"),
    ("controller_to_actuator_command", "Controller to actuator"),
    ("end_to_end_command", "End to end"),
]


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def distribution(values):
    return {
        "count": len(values),
        "min": min(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "max": max(values),
        "stddev": statistics.pstdev(values),
    }


def run_level_estimate(runs, metric, statistic):
    """Treat runs, rather than correlated frames, as experimental units."""
    estimates = []
    for run in sorted(runs):
        values = runs[run][metric]
        estimates.append(statistics.median(values) if statistic == "median"
                         else percentile(values, 0.95))
    return estimates


def bootstrap_difference(left, right, iterations=20000, seed=20260819):
    """Independent run-cluster bootstrap CI for ROS2 - ROS1."""
    rng = random.Random(seed)
    differences = []
    for _ in range(iterations):
        left_draw = [rng.choice(left) for _ in left]
        right_draw = [rng.choice(right) for _ in right]
        differences.append(statistics.mean(right_draw) - statistics.mean(left_draw))
    return {
        "estimate": statistics.mean(right) - statistics.mean(left),
        "ci95_low": percentile(differences, 0.025),
        "ci95_high": percentile(differences, 0.975),
        "bootstrap_iterations": iterations,
        "unit": "run",
    }


def read_latency(system):
    reports = []
    samples = {key: [] for key, _ in METRICS}
    run_samples = {}
    for run in range(1, 6):
        report_path = INPUT / f"{system}-trace-report-run-{run:02d}.json"
        sample_path = INPUT / f"{system}-trace-samples-run-{run:02d}.csv"
        reports.append(json.loads(report_path.read_text()))
        current = {key: [] for key, _ in METRICS}
        with sample_path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                columns = {
                    "sensor_to_controller": "sensor_to_controller_ms",
                    "controller_to_actuator_command": "controller_to_actuator_ms",
                    "end_to_end_command": "end_to_end_ms",
                }
                for metric, column in columns.items():
                    value = float(row[column])
                    samples[metric].append(value)
                    current[metric].append(value)
        run_samples[run] = current
    return reports, samples, run_samples


def read_pidstat(path, commands):
    rows = {command: [] for command in commands}
    with path.open(errors="replace") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 16 or parts[1] not in {"AM", "PM"}:
                continue
            command = parts[-1]
            if command not in rows:
                continue
            try:
                rows[command].append({
                    "cpu_pct": float(parts[8]),
                    "rss_mib": float(parts[13]) / 1024.0,
                })
            except ValueError:
                continue
    return rows


def read_resources(system):
    process_names = {
        "ros1": {"controller": "scale_truck_con", "lrc": "LRC"},
        "ros2": {"controller": "scale_truck_con", "lrc": "lrc_node"},
    }[system]
    runs = []
    for run in range(1, 6):
        path = RESOURCES / f"{system}-run-{run:02d}-cpu-memory.txt"
        parsed = read_pidstat(path, set(process_names.values()))
        result = {}
        for role, command in process_names.items():
            values = parsed[command]
            if not values:
                raise RuntimeError(f"No {command} samples in {path}")
            result[role] = {
                "cpu_pct": statistics.mean(item["cpu_pct"] for item in values),
                "rss_mib": statistics.mean(item["rss_mib"] for item in values),
                "sample_count": len(values),
            }
        result["combined"] = {
            "cpu_pct": result["controller"]["cpu_pct"] + result["lrc"]["cpu_pct"],
            "rss_mib": result["controller"]["rss_mib"] + result["lrc"]["rss_mib"],
        }
        runs.append(result)
    return runs


def aggregate_resources(runs):
    summary = {}
    for role in ["controller", "lrc", "combined"]:
        summary[role] = {}
        for field in ["cpu_pct", "rss_mib"]:
            values = [run[role][field] for run in runs]
            summary[role][field] = {
                "mean": statistics.mean(values),
                "run_stddev": statistics.pstdev(values),
                "per_run": values,
            }
    return summary


def plot_latency_ecdf(all_samples):
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    colors = {"ros1": "#c44e52", "ros2": "#4c72b0"}
    for axis, (metric, label) in zip(axes, METRICS):
        for system in ["ros1", "ros2"]:
            ordered = sorted(all_samples[system][metric])
            y = [(index + 1) / len(ordered) for index in range(len(ordered))]
            axis.plot(ordered, y, linewidth=2, color=colors[system], label=system.upper())
        axis.set_title(label)
        axis.set_xlabel("Latency (ms)")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Cumulative fraction")
    axes[-1].legend(loc="lower right")
    fig.suptitle("Experiment 2 exact-trace latency distributions")
    fig.tight_layout()
    fig.savefig(PLOTS / "experiment2-latency-distributions.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_run_latency(run_samples):
    fig, axis = plt.subplots(figsize=(9, 4.2))
    positions = []
    medians = []
    p95s = []
    colors = []
    labels = []
    position = 0
    for system, color in [("ros1", "#c44e52"), ("ros2", "#4c72b0")]:
        for run in range(1, 6):
            values = run_samples[system][run]["end_to_end_command"]
            positions.append(position)
            medians.append(statistics.median(values))
            p95s.append(percentile(values, 0.95))
            colors.append(color)
            labels.append(f"{system.upper()}\n{run}")
            position += 1
        position += 1
    axis.bar(positions, p95s, color=colors, alpha=0.35, label="p95")
    axis.scatter(positions, medians, color=colors, edgecolor="black", zorder=3, label="Median")
    axis.set_xticks(positions, labels)
    axis.set_ylabel("End-to-end latency (ms)")
    axis.set_title("Per-run median and p95 end-to-end latency")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(PLOTS / "experiment2-end-to-end-by-run.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_resources(resources):
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    roles = ["controller", "lrc", "combined"]
    labels = ["Controller", "LRC", "Combined"]
    x = list(range(len(roles)))
    width = 0.36
    for offset, system, color in [(-width / 2, "ros1", "#c44e52"), (width / 2, "ros2", "#4c72b0")]:
        for axis, field, ylabel in [
            (axes[0], "cpu_pct", "Mean CPU (%)"),
            (axes[1], "rss_mib", "Mean RSS memory (MiB)"),
        ]:
            means = [resources[system][role][field]["mean"] for role in roles]
            errors = [resources[system][role][field]["run_stddev"] for role in roles]
            axis.bar([value + offset for value in x], means, width, yerr=errors,
                     capsize=3, color=color, label=system.upper())
            axis.set_xticks(x, labels)
            axis.set_ylabel(ylabel)
            axis.grid(axis="y", alpha=0.25)
    axes[0].set_title("Control-node CPU usage")
    axes[1].set_title("Control-node resident memory")
    axes[1].legend()
    fig.suptitle("Xavier resources (mean across five runs; error bars = run SD)")
    fig.tight_layout()
    fig.savefig(PLOTS / "experiment2-cpu-memory-comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def percent_change(old, new):
    return (new - old) / old * 100.0


def write_report(summary):
    latency = summary["latency_ms"]
    resources = summary["resources"]
    lines = [
        "# Experiment 2: ROS 1 vs. ROS 2 exact-trace comparison",
        "",
        "## Test design",
        "",
        "Five ROS 1 and five ROS 2 runs replayed the same public camera bag on the same Xavier. "
        "Messages carried a trace ID and sensor acquisition timestamp. Power mode, online CPUs, "
        "and WLAN state matched across all runs; ROS 2 used `rmw_fastrtps_cpp`.",
        "",
        "## Latency comparison (pooled exact traces)",
        "",
        "| Metric | System | Samples | Mean (ms) | Median (ms) | p95 (ms) | p99 (ms) | Max (ms) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for metric, label in METRICS:
        for system in ["ros1", "ros2"]:
            item = latency[metric][system]
            lines.append(
                f"| {label} | {system.upper()} | {item['count']} | {item['mean']:.2f} | "
                f"{item['median']:.2f} | {item['p95']:.2f} | {item['p99']:.2f} | {item['max']:.2f} |")
    r1 = latency["end_to_end_command"]["ros1"]
    r2 = latency["end_to_end_command"]["ros2"]
    median_effect = summary["run_level_inference"]["end_to_end_command"]["median"]
    p95_effect = summary["run_level_inference"]["end_to_end_command"]["p95"]
    lines.extend([
        "",
        "## Xavier resource comparison",
        "",
        "Values are means across five runs. CPU can exceed 100% when a process uses more than one core.",
        "",
        "| Process | System | CPU mean (%) | CPU run SD | RSS mean (MiB) | RSS run SD |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for role, label in [("controller", "Controller"), ("lrc", "LRC"), ("combined", "Combined")]:
        for system in ["ros1", "ros2"]:
            item = resources[system][role]
            lines.append(
                f"| {label} | {system.upper()} | {item['cpu_pct']['mean']:.2f} | "
                f"{item['cpu_pct']['run_stddev']:.2f} | {item['rss_mib']['mean']:.2f} | "
                f"{item['rss_mib']['run_stddev']:.2f} |")
    lines.extend([
        "",
        "## Final analysis",
        "",
        f"- ROS 2 reduced pooled median end-to-end latency from {r1['median']:.2f} ms to "
        f"{r2['median']:.2f} ms ({-percent_change(r1['median'], r2['median']):.1f}% lower).",
        f"- ROS 2 reduced pooled p95 end-to-end latency from {r1['p95']:.2f} ms to "
        f"{r2['p95']:.2f} ms ({-percent_change(r1['p95'], r2['p95']):.1f}% lower).",
        f"- End-to-end standard deviation fell from {r1['stddev']:.2f} ms to "
        f"{r2['stddev']:.2f} ms, indicating more consistent timing in this implementation.",
        f"- Using runs as the experimental units, the ROS 2 minus ROS 1 difference in the "
        f"mean per-run median was {median_effect['ros2_minus_ros1']['estimate']:.2f} ms "
        f"(run-cluster bootstrap 95% CI "
        f"{median_effect['ros2_minus_ros1']['ci95_low']:.2f} to "
        f"{median_effect['ros2_minus_ros1']['ci95_high']:.2f} ms).",
        f"- The corresponding difference in the mean per-run p95 was "
        f"{p95_effect['ros2_minus_ros1']['estimate']:.2f} ms (95% CI "
        f"{p95_effect['ros2_minus_ros1']['ci95_low']:.2f} to "
        f"{p95_effect['ros2_minus_ros1']['ci95_high']:.2f} ms).",
        "- Pooled frame counts are descriptive only; frames within one replay are correlated and "
        "must not be treated as independent replicates.",
        "- The exact trace fields remove the main Experiment 1 uncertainty: controller and actuator "
        "commands are matched to the sensor frame that actually produced them.",
        "- This experiment compares the current ROS 1 and ROS 2 implementations, not middleware alone. "
        "The image-processing workloads are not identical, so lower ROS 2 latency and resource use cannot "
        "be attributed only to ROS 2 or DDS.",
        "",
        "## Plots",
        "",
        "- `plots/experiment2-latency-distributions.png`: pooled exact-trace ECDFs.",
        "- `plots/experiment2-end-to-end-by-run.png`: per-run median and p95 latency.",
        "- `plots/experiment2-cpu-memory-comparison.png`: controller/LRC CPU and memory.",
    ])
    (ROOT / "docs" / "testing" / "Experiment2-ros1-vs-ros2-comparison.md").write_text(
        "\n".join(lines) + "\n")


def main():
    PLOTS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    reports = {}
    samples = {}
    run_samples = {}
    resources = {}
    for system in ["ros1", "ros2"]:
        reports[system], samples[system], run_samples[system] = read_latency(system)
        resources[system] = aggregate_resources(read_resources(system))

    inference = {}
    for metric, _ in METRICS:
        inference[metric] = {}
        for statistic in ["median", "p95"]:
            ros1_values = run_level_estimate(run_samples["ros1"], metric, statistic)
            ros2_values = run_level_estimate(run_samples["ros2"], metric, statistic)
            inference[metric][statistic] = {
                "ros1_per_run": ros1_values,
                "ros2_per_run": ros2_values,
                "ros1_run_mean": statistics.mean(ros1_values),
                "ros2_run_mean": statistics.mean(ros2_values),
                "ros2_minus_ros1": bootstrap_difference(ros1_values, ros2_values),
            }

    summary = {
        "method": {
            "runs_per_system": 5,
            "latency_descriptive_aggregation": "all exact-trace samples pooled by ROS version",
            "latency_inference": "run is the experimental unit; independent run-cluster bootstrap",
            "resource_aggregation": "per-run process means, then mean and population SD across runs",
        },
        "trace_counts": {system: sum(report["trace_count"] for report in reports[system]) for system in reports},
        "latency_ms": {
            metric: {system: distribution(samples[system][metric]) for system in ["ros1", "ros2"]}
            for metric, _ in METRICS
        },
        "resources": resources,
        "run_level_inference": inference,
    }
    (DATA / "experiment2-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    with (DATA / "experiment2-comparison.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "system", "count", "mean_ms", "median_ms", "p95_ms", "p99_ms", "max_ms", "stddev_ms"])
        for metric, label in METRICS:
            for system in ["ros1", "ros2"]:
                item = summary["latency_ms"][metric][system]
                writer.writerow([label, system.upper(), item["count"], item["mean"], item["median"], item["p95"], item["p99"], item["max"], item["stddev"]])
    plot_latency_ecdf(samples)
    plot_run_latency(run_samples)
    plot_resources(resources)
    write_report(summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
