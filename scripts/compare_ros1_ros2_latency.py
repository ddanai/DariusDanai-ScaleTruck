#!/usr/bin/env python3
"""Aggregate latency reports and create ROS 1 versus ROS 2 plots and tables."""

import argparse
import csv
import json
from pathlib import Path
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


METRICS = [
    ("sensor_to_controller", "Sensor to controller"),
    ("controller_to_actuator_command", "Controller to actuator"),
    ("end_to_end_command", "End to end"),
]
TOPICS = [
    ("/usb_cam/image_raw", "Camera"),
    ("/xav2lrc_msg", "Controller command"),
    ("/lrc2ocr_msg", "Actuator command"),
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


def read_samples(paths):
    samples = {key: [] for key, _label in METRICS}
    for path in paths:
        with open(path, newline="") as handle:
            for row in csv.DictReader(handle):
                samples[row["metric"]].append(float(row["latency_ms"]))
    return samples


def read_reports(paths):
    return [json.loads(Path(path).read_text()) for path in paths]


def mean_and_run_stddev(values):
    return {
        "mean": statistics.mean(values),
        "run_stddev": statistics.pstdev(values) if len(values) > 1 else 0.0,
    }


def ecdf(values):
    ordered = sorted(values)
    return ordered, [(index + 1) / len(ordered) for index in range(len(ordered))]


def plot_distributions(ros1, ros2, output):
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for axis, (key, label) in zip(axes, METRICS):
        for values, name, color in [
            (ros1[key], "ROS 1", "#c44e52"),
            (ros2[key], "ROS 2", "#4c72b0"),
        ]:
            x, y = ecdf(values)
            axis.plot(x, y, label=name, color=color, linewidth=2)
        axis.set_title(label)
        axis.set_xlabel("Latency (ms)")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Cumulative fraction")
    axes[-1].legend(loc="lower right")
    fig.suptitle("Latency distributions (empirical CDF)")
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_topic_metric(ros1_report, ros2_reports, field, ylabel, title, output):
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    for axis, (topic, label) in zip(axes, TOPICS):
        ros1_value = ros1_report["topic_timing"][topic][field]
        ros2_values = [report["topic_timing"][topic][field] for report in ros2_reports]
        axis.bar(
            ["ROS 1", "ROS 2"], [ros1_value, statistics.mean(ros2_values)],
            color=["#c44e52", "#4c72b0"])
        axis.errorbar(
            [1], [statistics.mean(ros2_values)],
            yerr=[statistics.pstdev(ros2_values)], fmt="none",
            ecolor="black", capsize=4)
        axis.set_title(label)
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ros1-report", required=True)
    parser.add_argument("--ros1-samples", required=True)
    parser.add_argument("--ros2-reports", nargs="+", required=True)
    parser.add_argument("--ros2-samples", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    ros1_report = read_reports([args.ros1_report])[0]
    ros2_reports = read_reports(args.ros2_reports)
    ros1_samples = read_samples([args.ros1_samples])
    ros2_samples = read_samples(args.ros2_samples)

    summary = {
        "method": {
            "ros1_runs": 1,
            "ros2_runs": len(ros2_reports),
            "latency_aggregation": "all matched samples pooled by ROS version",
            "ros2_rate_and_jitter": "mean across runs with population standard deviation",
        },
        "latency_ms": {},
        "topic_timing": {},
    }
    for key, _label in METRICS:
        summary["latency_ms"][key] = {
            "ros1": distribution(ros1_samples[key]),
            "ros2": distribution(ros2_samples[key]),
        }
    for topic, _label in TOPICS:
        summary["topic_timing"][topic] = {
            "ros1": {
                "frequency_hz": ros1_report["topic_timing"][topic]["frequency_hz"],
                "jitter_stddev_ms": ros1_report["topic_timing"][topic]["jitter_stddev_ms"],
            },
            "ros2": {
                "frequency_hz": mean_and_run_stddev([
                    report["topic_timing"][topic]["frequency_hz"]
                    for report in ros2_reports]),
                "jitter_stddev_ms": mean_and_run_stddev([
                    report["topic_timing"][topic]["jitter_stddev_ms"]
                    for report in ros2_reports]),
            },
        }

    (output / "ros1-ros2-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    with open(output / "ros1-ros2-comparison.csv", "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "system", "count", "mean_ms", "median_ms", "p95_ms", "p99_ms", "stddev_ms"])
        for key, label in METRICS:
            for system in ["ros1", "ros2"]:
                stats = summary["latency_ms"][key][system]
                writer.writerow([
                    label, system.upper(), stats["count"], stats["mean"],
                    stats["median"], stats["p95"], stats["p99"], stats["stddev"]])

    plot_distributions(ros1_samples, ros2_samples, output / "latency-distributions.png")
    plot_topic_metric(
        ros1_report, ros2_reports, "frequency_hz", "Frequency (Hz)",
        "Topic publishing frequency", output / "topic-frequency.png")
    plot_topic_metric(
        ros1_report, ros2_reports, "jitter_stddev_ms", "Jitter std. dev. (ms)",
        "Topic timing jitter", output / "topic-jitter.png")


if __name__ == "__main__":
    main()
