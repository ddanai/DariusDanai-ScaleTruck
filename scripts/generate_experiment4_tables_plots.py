#!/usr/bin/env python3
"""Generate publication-ready Experiment 4 tables and plots from its summary."""

import csv
import json
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results" / "latency" / "experiment4" / "comparison"
SUMMARY = BASE / "experiment4-summary.json"
PLOTS = BASE / "plots"

SYSTEM_COLORS = {"ros1": "#b65a57", "ros2": "#5876ad"}
METRICS = [
    ("sensor_to_controller", "Sensor to controller"),
    ("controller_to_actuator_command", "Controller to actuator"),
    ("end_to_end_command", "End to end"),
]


def fmt(value):
    return f"{value:.2f}"


def save_figure(fig, name):
    PLOTS.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(PLOTS / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(PLOTS / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def latency_rows(summary):
    rows = []
    for key, label in METRICS:
        item = summary["metrics"][key]
        for statistic, suffix in [("Median", "median"), ("P95", "p95")]:
            difference = item[f"ros2_minus_ros1_{suffix}_ms"]
            conclusive = not (difference["ci95_low"] <= 0 <= difference["ci95_high"])
            rows.append({
                "metric": label,
                "statistic": statistic,
                "ros1_ms": item["ros1"][f"mean_per_run_{suffix}_ms"],
                "ros2_ms": item["ros2"][f"mean_per_run_{suffix}_ms"],
                "ros2_minus_ros1_ms": difference["estimate"],
                "ci95_low_ms": difference["ci95_low"],
                "ci95_high_ms": difference["ci95_high"],
                "ci_excludes_zero": conclusive,
            })
    return rows


def write_tables(summary):
    latency = latency_rows(summary)
    with (BASE / "experiment4-latency-comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=latency[0].keys())
        writer.writeheader()
        writer.writerows(latency)

    timing = []
    for topic in ["controller", "actuator"]:
        for system in ["ros1", "ros2"]:
            item = summary["topic_timing"][topic][system]
            timing.append({
                "topic": topic,
                "system": system.upper(),
                "mean_frequency_hz": item["mean_frequency_hz"],
                "mean_interarrival_jitter_ms": item["mean_interarrival_jitter_ms"],
            })
    with (BASE / "experiment4-timing-comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=timing[0].keys())
        writer.writeheader()
        writer.writerows(timing)

    lines = [
        "# Experiment 4 — ROS 1 vs. ROS 2 comparison",
        "",
        "Matched-workload whole-system test on the Xavier; 30 runs per system. Values are means of run-level statistics. Negative ROS 2 − ROS 1 latency differences favor ROS 2.",
        "",
        "| Metric | Statistic | ROS 1 (ms) | ROS 2 (ms) | ROS 2 − ROS 1 (ms) | 95% CI (ms) | CI excludes zero? |",
        "|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for row in latency:
        lines.append(
            f"| {row['metric']} | {row['statistic']} | {fmt(row['ros1_ms'])} | "
            f"{fmt(row['ros2_ms'])} | {fmt(row['ros2_minus_ros1_ms'])} | "
            f"[{fmt(row['ci95_low_ms'])}, {fmt(row['ci95_high_ms'])}] | "
            f"{'Yes' if row['ci_excludes_zero'] else 'No'} |"
        )
    lines += [
        "",
        "## Topic timing",
        "",
        "| Topic | System | Mean frequency (Hz) | Mean interarrival jitter (ms) |",
        "|---|---:|---:|---:|",
    ]
    for row in timing:
        lines.append(
            f"| {row['topic'].title()} | {row['system']} | "
            f"{fmt(row['mean_frequency_hz'])} | {fmt(row['mean_interarrival_jitter_ms'])} |"
        )
    lines += [
        "",
        "## Measurement-window resources",
        "",
        "CPU and RSS were measured during the same five-second post-warm-up window used for latency. Both systems used standardized 50 Hz matched LRC adapters with equivalent logging behavior.",
        "",
        "| System | Combined mean CPU (%) | Combined mean RSS (MiB) |",
        "|---|---:|---:|",
    ]
    for system in ["ros1", "ros2"]:
        combined = summary["resources"][system]["combined"]
        lines.append(
            f"| {system.upper()} | {fmt(combined['cpu_pct']['mean'])} | "
            f"{fmt(combined['rss_mib']['mean'])} |"
        )
    (BASE / "experiment4-comparison-table.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")


def plot_latency(summary):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, (statistic, suffix) in zip(axes, [("Run-level median", "median"), ("Run-level P95", "p95")]):
        estimates, lows, highs = [], [], []
        for key, _ in METRICS:
            item = summary["metrics"][key][f"ros2_minus_ros1_{suffix}_ms"]
            estimates.append(item["estimate"])
            lows.append(item["estimate"] - item["ci95_low"])
            highs.append(item["ci95_high"] - item["estimate"])
        y = np.arange(len(METRICS))
        ax.errorbar(estimates, y, xerr=[lows, highs], fmt="o", color="#303030", capsize=5)
        ax.axvline(0, color="#888888", linestyle="--", linewidth=1)
        ax.set_yticks(y, [label for _, label in METRICS])
        ax.invert_yaxis()
        ax.set_xlabel("ROS 2 − ROS 1 latency (ms)")
        ax.set_title(statistic)
        ax.grid(axis="x", alpha=0.25)
    fig.suptitle("Matched-workload latency differences with 95% bootstrap CIs\nNegative values favor ROS 2")
    save_figure(fig, "experiment4-latency-differences")


def plot_timing(summary):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    topics = ["controller", "actuator"]
    labels = ["Controller", "Actuator"]
    x = np.arange(len(topics))
    width = 0.34
    for index, system in enumerate(["ros1", "ros2"]):
        offset = (index - 0.5) * width
        axes[0].bar(x + offset, [summary["topic_timing"][t][system]["mean_frequency_hz"] for t in topics], width, label=system.upper(), color=SYSTEM_COLORS[system])
        axes[1].bar(x + offset, [summary["topic_timing"][t][system]["mean_interarrival_jitter_ms"] for t in topics], width, label=system.upper(), color=SYSTEM_COLORS[system])
    axes[0].set_ylabel("Mean frequency (Hz)")
    axes[1].set_ylabel("Mean interarrival jitter (ms)")
    for ax in axes:
        ax.set_xticks(x, labels)
        ax.grid(axis="y", alpha=0.25)
        ax.legend()
    fig.suptitle("Topic timing across 30 matched runs per system")
    save_figure(fig, "experiment4-topic-timing")


def plot_resources(summary):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    systems = ["ros1", "ros2"]
    labels = ["ROS 1", "ROS 2"]
    x = np.arange(2)
    cpu = [summary["resources"][s]["combined"]["cpu_pct"] for s in systems]
    rss = [summary["resources"][s]["combined"]["rss_mib"] for s in systems]
    axes[0].bar(x, [v["mean"] for v in cpu], yerr=[v["run_stddev"] for v in cpu], capsize=5, color=[SYSTEM_COLORS[s] for s in systems])
    axes[1].bar(x, [v["mean"] for v in rss], yerr=[v["run_stddev"] for v in rss], capsize=5, color=[SYSTEM_COLORS[s] for s in systems])
    axes[0].set_ylabel("Combined CPU (%)")
    axes[1].set_ylabel("Combined RSS (MiB)")
    for ax in axes:
        ax.set_xticks(x, labels)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Measurement-window resources (mean ± run SD)\nNot a middleware-only comparison")
    save_figure(fig, "experiment4-session-resources")


def main():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    write_tables(summary)
    plot_latency(summary)
    plot_timing(summary)
    plot_resources(summary)
    print(f"Wrote tables to {BASE}")
    print(f"Wrote plots to {PLOTS}")


if __name__ == "__main__":
    main()
