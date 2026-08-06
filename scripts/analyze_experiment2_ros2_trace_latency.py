#!/usr/bin/env python3
"""Analyze an Experiment 2 ROS 2 bag using exact command trace IDs."""

import argparse
import csv
import importlib.util
import json
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "latency_common", Path(__file__).with_name("analyze_ros1_latency.py"))
COMMON = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMMON)


def first_by_trace(events):
    result = {}
    for event in events:
        result.setdefault(event["trace_id"], event)
    return result


def analyze(events, controller_topic, actuator_topic):
    controller = first_by_trace(events[controller_topic])
    actuator = first_by_trace(events[actuator_topic])
    rows = []
    for trace_id in sorted(set(controller) & set(actuator)):
        command = controller[trace_id]
        output = actuator[trace_id]
        values = [
            (command["receive_s"] - command["sensor_s"]) * 1000.0,
            (output["receive_s"] - command["receive_s"]) * 1000.0,
            (output["receive_s"] - command["sensor_s"]) * 1000.0,
        ]
        if min(values) >= 0:
            rows.append([trace_id] + values)
    columns = list(zip(*[row[1:] for row in rows])) if rows else [[], [], []]
    return {
        "method": {
            "correlation": "first controller and actuator messages with the same trace_id",
            "clock": "sensor header stamp and rosbag2 receive timestamps",
        },
        "trace_count": len(rows),
        "latency_ms": {
            "sensor_to_controller": COMMON.distribution(list(columns[0])),
            "controller_to_actuator_command": COMMON.distribution(list(columns[1])),
            "end_to_end_command": COMMON.distribution(list(columns[2])),
        },
    }, rows


def read_bag(uri, controller_topic, actuator_topic, start_s, duration_s):
    try:
        import rosbag2_py
        from rclpy.serialization import deserialize_message
        from rosidl_runtime_py.utilities import get_message
    except ImportError as error:
        raise RuntimeError(
            "Run inside a sourced ROS 2 workspace with rosbag2_py available") from error

    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=uri, storage_id="sqlite3"),
        rosbag2_py.ConverterOptions("cdr", "cdr"))
    type_names = {item.name: item.type for item in reader.get_all_topics_and_types()}
    required = {controller_topic, actuator_topic}
    missing = required - set(type_names)
    if missing:
        raise RuntimeError("Missing topics: {}".format(", ".join(sorted(missing))))
    types = {topic: get_message(type_names[topic]) for topic in required}
    events = {topic: [] for topic in required}
    bag_start_ns = None
    while reader.has_next():
        topic, data, receive_ns = reader.read_next()
        if topic not in required:
            continue
        if bag_start_ns is None:
            bag_start_ns = receive_ns
        elapsed = (receive_ns - bag_start_ns) / 1e9
        if elapsed < start_s or (duration_s is not None and elapsed > start_s + duration_s):
            continue
        message = deserialize_message(data, types[topic])
        if not hasattr(message, "trace_id"):
            raise RuntimeError("Bag was recorded before trace fields were added")
        if message.trace_id == 0:
            continue
        events[topic].append({
            "trace_id": int(message.trace_id),
            "sensor_s": message.sensor_stamp.sec + message.sensor_stamp.nanosec / 1e9,
            "receive_s": receive_ns / 1e9,
        })
    return events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bag")
    parser.add_argument("--controller-topic", default="/xav2lrc_msg")
    parser.add_argument("--actuator-topic", default="/lrc2ocr_msg")
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--output", default="experiment2_ros2_trace_latency_report.json")
    parser.add_argument("--csv")
    args = parser.parse_args()
    events = read_bag(
        args.bag, args.controller_topic, args.actuator_topic,
        args.start, args.duration)
    report, rows = analyze(events, args.controller_topic, args.actuator_topic)
    report["bag"] = str(Path(args.bag).resolve())
    report["window"] = {"start_s": args.start, "duration_s": args.duration}
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.csv:
        with open(args.csv, "w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow([
                "trace_id", "sensor_to_controller_ms",
                "controller_to_actuator_ms", "end_to_end_ms"])
            writer.writerows(rows)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
