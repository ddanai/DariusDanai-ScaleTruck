#!/usr/bin/env python
"""Analyze ROS 1 pipeline latency and topic timing from a ROS bag.

The reference stack does not propagate a sensor sequence ID into its custom
command messages. Latencies are therefore estimates: each upstream event is
matched to the first following downstream event inside --max-latency-ms.
"""

from __future__ import print_function

import argparse
import csv
import json
import math
import os
import statistics
import sys


DEFAULT_SENSOR = "/usb_cam/image_raw"
DEFAULT_CONTROLLER = "/xav2lrc_msg"
DEFAULT_ACTUATOR = "/lrc2ocr_msg"


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def distribution(values):
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "min": min(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "max": max(values),
        "stddev": statistics.pstdev(values) if len(values) > 1 else 0.0,
    }


def first_following_matches(upstream, downstream, max_latency_s):
    """Match every upstream event to the first downstream event after it."""
    matches = []
    downstream_index = 0
    for input_time in upstream:
        while (downstream_index < len(downstream)
               and downstream[downstream_index] < input_time):
            downstream_index += 1
        if downstream_index >= len(downstream):
            break
        delay = downstream[downstream_index] - input_time
        if delay <= max_latency_s:
            matches.append((input_time, downstream[downstream_index], delay))
        downstream_index += 1
    return matches


def first_following_latencies(upstream, downstream, max_latency_s):
    """Return delays from each input to the first unused following output."""
    return [
        match[2]
        for match in first_following_matches(
            upstream, downstream, max_latency_s)
    ]


def chained_end_to_end_latencies(sensor, controller, actuator, max_latency_s):
    """Match sensor->controller->actuator and return full-chain delays."""
    delays = []
    sensor_controller = first_following_matches(
        sensor, controller, max_latency_s)
    actuator_index = 0
    for sensor_time, controller_time, _delay in sensor_controller:
        while (actuator_index < len(actuator)
               and actuator[actuator_index] < controller_time):
            actuator_index += 1
        if actuator_index >= len(actuator):
            break
        delay = actuator[actuator_index] - sensor_time
        if delay <= max_latency_s:
            delays.append(delay)
        actuator_index += 1
    return delays


def timing_metrics(timestamps):
    intervals = [
        timestamps[index] - timestamps[index - 1]
        for index in range(1, len(timestamps))
        if timestamps[index] >= timestamps[index - 1]
    ]
    interval_stats = distribution([value * 1000.0 for value in intervals])
    duration = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0.0
    frequency = ((len(timestamps) - 1) / duration) if duration > 0 else None
    median_interval = statistics.median(intervals) if intervals else None
    jitter = (
        statistics.pstdev([(value - median_interval) * 1000.0
                           for value in intervals])
        if len(intervals) > 1 else 0.0
    )
    return {
        "message_count": len(timestamps),
        "duration_s": duration,
        "frequency_hz": frequency,
        "jitter_stddev_ms": jitter,
        "interval_ms": interval_stats,
    }


def analyze_events(events, sensor_topic, controller_topic, actuator_topic,
                   frequency_topics, max_latency_ms):
    max_latency_s = max_latency_ms / 1000.0
    sensor = events.get(sensor_topic, [])
    controller = events.get(controller_topic, [])
    actuator = events.get(actuator_topic, [])

    def latency(upstream, downstream):
        return distribution([
            value * 1000.0
            for value in first_following_latencies(
                upstream, downstream, max_latency_s)
        ])

    return {
        "method": {
            "clock": "ROS bag record timestamp",
            "correlation": "first unused following downstream message",
            "max_latency_ms": max_latency_ms,
            "limitation": (
                "The ROS1 reference messages do not propagate a common trace "
                "ID. Results estimate timing proximity, not exact causality."
            ),
        },
        "topics": {
            "sensor": sensor_topic,
            "controller_command": controller_topic,
            "actuator_command": actuator_topic,
        },
        "latency_ms": {
            "sensor_to_controller": latency(sensor, controller),
            "controller_to_actuator_command": latency(controller, actuator),
            "end_to_end_command": distribution([
                value * 1000.0
                for value in chained_end_to_end_latencies(
                    sensor, controller, actuator, max_latency_s)
            ]),
        },
        "topic_timing": {
            topic: timing_metrics(events.get(topic, []))
            for topic in frequency_topics
        },
    }


def read_bag_events(path, topics, start_s=None, duration_s=None):
    try:
        import rosbag
    except ImportError:
        raise RuntimeError(
            "Cannot import rosbag. Run this inside a sourced ROS1 environment.")

    events = {topic: [] for topic in topics}
    with rosbag.Bag(path, "r") as bag:
        bag_start = bag.get_start_time()
        window_start = bag_start + (start_s or 0.0)
        window_end = (
            window_start + duration_s if duration_s is not None else None)
        for topic, _message, timestamp in bag.read_messages(topics=topics):
            event_time = timestamp.to_sec()
            if event_time < window_start:
                continue
            if window_end is not None and event_time > window_end:
                continue
            events[topic].append(event_time)
    return events


def write_latency_csv(path, events, sensor_topic, controller_topic,
                      actuator_topic, max_latency_ms):
    rows = []
    pairs = [
        ("sensor_to_controller", sensor_topic, controller_topic),
        ("controller_to_actuator_command", controller_topic, actuator_topic),
        ("end_to_end_command", sensor_topic, actuator_topic),
    ]
    for name, upstream, downstream in pairs:
        values = first_following_latencies(
            events.get(upstream, []), events.get(downstream, []),
            max_latency_ms / 1000.0)
        rows.extend((name, value * 1000.0) for value in values)
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "latency_ms"])
        writer.writerows(rows)


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bag", help="ROS1 .bag file")
    parser.add_argument("--sensor-topic", default=DEFAULT_SENSOR)
    parser.add_argument("--controller-topic", default=DEFAULT_CONTROLLER)
    parser.add_argument("--actuator-topic", default=DEFAULT_ACTUATOR)
    parser.add_argument(
        "--frequency-topic", action="append", default=[],
        help="Topic to profile; repeat as needed (defaults to pipeline topics)")
    parser.add_argument("--start", type=float, default=0.0,
                        help="Seconds from bag start")
    parser.add_argument("--duration", type=float,
                        help="Analysis window duration in seconds")
    parser.add_argument("--max-latency-ms", type=float, default=500.0)
    parser.add_argument("--output", default="ros1_latency_report.json")
    parser.add_argument("--csv", help="Optional file for raw matched latencies")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if not os.path.isfile(args.bag):
        print("Bag not found: {0}".format(args.bag), file=sys.stderr)
        return 2
    frequency_topics = args.frequency_topic or [
        args.sensor_topic, args.controller_topic, args.actuator_topic]
    topics = sorted(set(frequency_topics + [
        args.sensor_topic, args.controller_topic, args.actuator_topic]))
    try:
        events = read_bag_events(
            args.bag, topics, args.start, args.duration)
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
        write_latency_csv(
            args.csv, events, args.sensor_topic, args.controller_topic,
            args.actuator_topic, args.max_latency_ms)
    print(json.dumps(report, indent=2, sort_keys=True))
    print("Wrote {0}".format(args.output), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
