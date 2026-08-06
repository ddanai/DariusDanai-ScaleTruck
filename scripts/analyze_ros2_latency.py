#!/usr/bin/env python3
"""Analyze ROS 2 pipeline latency and topic timing from a rosbag2 SQLite bag."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("latency_common", ROOT / "analyze_ros1_latency.py")
COMMON = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMMON)

DEFAULT_SENSOR = "/usb_cam/image_raw"
DEFAULT_CONTROLLER = "/xav2lrc_msg"
DEFAULT_ACTUATOR = "/lrc2ocr_msg"


def find_db3_files(path):
    source = Path(path)
    if source.is_file() and source.suffix == ".db3":
        return [source]
    if source.is_dir():
        files = sorted(source.glob("*.db3"))
        if files:
            return files
    raise RuntimeError("No rosbag2 .db3 file found at: {}".format(path))


def read_bag_events(path, topics, start_s=None, duration_s=None):
    """Read receive timestamps without deserializing ROS messages."""
    rows = []
    available = set()
    for database in find_db3_files(path):
        connection = sqlite3.connect(str(database))
        try:
            topic_rows = connection.execute("SELECT id, name FROM topics").fetchall()
            topic_ids = {identifier: name for identifier, name in topic_rows}
            available.update(topic_ids.values())
            wanted_ids = [identifier for identifier, name in topic_ids.items() if name in topics]
            if wanted_ids:
                placeholders = ",".join("?" for _ in wanted_ids)
                query = (
                    "SELECT topic_id, timestamp FROM messages "
                    "WHERE topic_id IN ({}) ORDER BY timestamp".format(placeholders))
                rows.extend(
                    (topic_ids[topic_id], timestamp)
                    for topic_id, timestamp in connection.execute(query, wanted_ids))
        finally:
            connection.close()

    rows.sort(key=lambda item: item[1])
    if not rows:
        missing = sorted(set(topics) - available)
        raise RuntimeError(
            "No requested messages found. Missing topics: {}. Available: {}".format(
                ", ".join(missing) or "none", ", ".join(sorted(available)) or "none"))
    bag_start_ns = rows[0][1]
    window_start_ns = bag_start_ns + int((start_s or 0.0) * 1e9)
    window_end_ns = window_start_ns + int(duration_s * 1e9) if duration_s is not None else None
    events = {topic: [] for topic in topics}
    for topic, timestamp_ns in rows:
        if timestamp_ns < window_start_ns:
            continue
        if window_end_ns is not None and timestamp_ns > window_end_ns:
            continue
        events[topic].append(timestamp_ns / 1e9)
    return events


def analyze_events(events, sensor_topic, controller_topic, actuator_topic,
                   frequency_topics, max_latency_ms):
    report = COMMON.analyze_events(
        events, sensor_topic, controller_topic, actuator_topic,
        frequency_topics, max_latency_ms)
    report["method"]["clock"] = "rosbag2 SQLite receive timestamp"
    report["method"]["limitation"] = (
        "The current ROS2 command messages do not propagate a common trace ID. "
        "Results estimate timing proximity, not exact causality.")
    return report


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bag", help="rosbag2 directory or .db3 file")
    parser.add_argument("--sensor-topic", default=DEFAULT_SENSOR)
    parser.add_argument("--controller-topic", default=DEFAULT_CONTROLLER)
    parser.add_argument("--actuator-topic", default=DEFAULT_ACTUATOR)
    parser.add_argument("--frequency-topic", action="append", default=[])
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--max-latency-ms", type=float, default=500.0)
    parser.add_argument("--output", default="ros2_latency_report.json")
    parser.add_argument("--csv", help="Optional raw matched latency CSV")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    frequency_topics = args.frequency_topic or [
        args.sensor_topic, args.controller_topic, args.actuator_topic]
    topics = sorted(set(frequency_topics + [
        args.sensor_topic, args.controller_topic, args.actuator_topic]))
    try:
        events = read_bag_events(args.bag, topics, args.start, args.duration)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 2
    report = analyze_events(
        events, args.sensor_topic, args.controller_topic, args.actuator_topic,
        frequency_topics, args.max_latency_ms)
    report["bag"] = os.path.abspath(args.bag)
    report["window"] = {"start_s": args.start, "duration_s": args.duration}
    with open(args.output, "w") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    if args.csv:
        COMMON.write_latency_csv(
            args.csv, events, args.sensor_topic, args.controller_topic,
            args.actuator_topic, args.max_latency_ms)
    print(json.dumps(report, indent=2, sort_keys=True))
    print("Wrote {}".format(args.output), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
