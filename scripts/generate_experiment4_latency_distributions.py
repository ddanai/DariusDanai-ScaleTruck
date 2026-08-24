#!/usr/bin/env python3
"""Plot descriptive Experiment 4 latency ECDFs from all official trace samples."""

import argparse
import csv
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
METRICS = [
    ("sensor_to_controller_ms", "Sensor to controller"),
    ("controller_to_actuator_ms", "Controller to actuator"),
    ("end_to_end_ms", "End to end"),
]
COLORS = {"ros1": "#b65a57", "ros2": "#5876ad"}


def read_samples(sample_dir, system):
    values = {column: [] for column, _ in METRICS}
    run_counts = []
    for run_id in range(1, 31):
        path = sample_dir / f"{system}-trace-samples-run-{run_id:02d}.csv"
        if not path.exists():
            raise RuntimeError(f"Missing official sample file: {path}")
        count = 0
        with path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                for column, _ in METRICS:
                    value = float(row[column])
                    if value < 0:
                        raise RuntimeError(f"Negative latency in {path}: {value}")
                    values[column].append(value)
                count += 1
        if count == 0:
            raise RuntimeError(f"No traces in {path}")
        run_counts.append(count)
    return values, run_counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base", type=Path,
        default=ROOT / "results" / "latency" / "experiment4",
        help="Experiment 4 results directory")
    args = parser.parse_args()

    sample_dir = args.base / "samples"
    output_dir = args.base / "comparison" / "plots"
    data = {}
    counts = {}
    for system in ("ros1", "ros2"):
        data[system], counts[system] = read_samples(sample_dir, system)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
    for axis, (column, title) in zip(axes, METRICS):
        for system in ("ros1", "ros2"):
            ordered = np.sort(np.asarray(data[system][column]))
            cumulative = np.arange(1, len(ordered) + 1) / len(ordered)
            axis.step(
                ordered, cumulative, where="post", linewidth=2,
                color=COLORS[system],
                label=f"{system.upper()} (n={len(ordered):,})")
        axis.set_title(title)
        axis.set_xlabel("Latency (ms)")
        axis.set_ylim(0, 1.01)
        axis.grid(alpha=0.25)
        axis.legend(loc="lower right")
    axes[0].set_ylabel("Cumulative fraction of matched traces")
    fig.suptitle(
        "Experiment 4 latency distributions across 30 runs per system\n"
        "Curves farther left indicate lower latency")
    fig.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "pdf"):
        destination = output_dir / f"experiment4-latency-distributions.{extension}"
        fig.savefig(destination, dpi=300, bbox_inches="tight")
        print(f"Wrote {destination}")
    plt.close(fig)
    print(
        "Trace counts: "
        f"ROS1={sum(counts['ros1'])} across {len(counts['ros1'])} runs; "
        f"ROS2={sum(counts['ros2'])} across {len(counts['ros2'])} runs")
    print("Note: pooled ECDFs are descriptive; run-level confidence intervals remain inferential.")


if __name__ == "__main__":
    main()
