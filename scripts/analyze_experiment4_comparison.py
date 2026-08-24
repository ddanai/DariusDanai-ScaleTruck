#!/usr/bin/env python3
"""Analyze Experiment 4 only after its preregistered 30+30 runs exist."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "experiment_comparison", Path(__file__).with_name("analyze_experiment3_comparison.py"))
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)

comparison.BASE = ROOT / "results" / "latency" / "experiment4"
comparison.REPORTS = comparison.BASE / "reports"
comparison.SAMPLES = comparison.BASE / "samples"
comparison.OUTPUT = comparison.BASE / "comparison"
comparison.RESOURCES = comparison.BASE / "resources"
comparison.RUN_LIMIT = 30


def validate_complete():
    expected = set(range(1, 31))
    for system in ("ros1", "ros2"):
        found = set(comparison.discover(system))
        if found != expected:
            missing = sorted(expected - found)
            extra = sorted(found - expected)
            raise RuntimeError(
                f"Experiment 4 analysis is locked until all 30 {system.upper()} runs exist; "
                f"missing={missing}, unexpected={extra}")
        for run_id in sorted(expected):
            resources = comparison.resource_run(system, run_id)
            for role in ("controller", "lrc"):
                count = resources[role]["sample_count"]
                if count != 5:
                    raise RuntimeError(
                        f"{system} run {run_id:02d} has {count} {role} resource samples; expected 5")


if __name__ == "__main__":
    validate_complete()
    comparison.main()
    old = comparison.OUTPUT / "experiment3-summary.json"
    new = comparison.OUTPUT / "experiment4-summary.json"
    old.replace(new)
    print(f"Wrote {new}")
