import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_ros2_latency.py"
SPEC = importlib.util.spec_from_file_location("analyze_ros2_latency", SCRIPT)
LATENCY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LATENCY)


class Ros2LatencyAnalysisTest(unittest.TestCase):
    def make_bag(self, directory):
        database = Path(directory) / "latency_0.db3"
        connection = sqlite3.connect(str(database))
        connection.executescript("""
            CREATE TABLE topics(id INTEGER PRIMARY KEY, name TEXT NOT NULL,
              type TEXT NOT NULL, serialization_format TEXT NOT NULL,
              offered_qos_profiles TEXT NOT NULL);
            CREATE TABLE messages(id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL,
              timestamp INTEGER NOT NULL, data BLOB NOT NULL);
        """)
        topics = ["/camera", "/controller", "/actuator"]
        for identifier, name in enumerate(topics, 1):
            connection.execute("INSERT INTO topics VALUES (?, ?, '', 'cdr', '')", (identifier, name))
        timestamps = {
            1: [1_000_000_000, 1_100_000_000, 1_200_000_000],
            2: [1_020_000_000, 1_120_000_000, 1_220_000_000],
            3: [1_030_000_000, 1_130_000_000, 1_230_000_000],
        }
        for topic_id, values in timestamps.items():
            for timestamp in values:
                connection.execute(
                    "INSERT INTO messages(topic_id, timestamp, data) VALUES (?, ?, ?)",
                    (topic_id, timestamp, b"x"))
        connection.commit()
        connection.close()

    def test_reads_sqlite_bag_and_computes_pipeline(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_bag(directory)
            topics = ["/camera", "/controller", "/actuator"]
            events = LATENCY.read_bag_events(directory, topics)
            report = LATENCY.analyze_events(events, *topics, topics, 100.0)
            self.assertAlmostEqual(report["latency_ms"]["sensor_to_controller"]["mean"], 20.0)
            self.assertAlmostEqual(report["latency_ms"]["controller_to_actuator_command"]["mean"], 10.0)
            self.assertAlmostEqual(report["latency_ms"]["end_to_end_command"]["mean"], 30.0)
            self.assertAlmostEqual(report["topic_timing"]["/camera"]["frequency_hz"], 10.0)

    def test_analysis_window_filters_messages(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_bag(directory)
            events = LATENCY.read_bag_events(
                directory, ["/camera"], start_s=0.05, duration_s=0.10)
            self.assertEqual(len(events["/camera"]), 1)

    def test_missing_topics_raise_clear_error(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_bag(directory)
            with self.assertRaisesRegex(RuntimeError, "Missing topics"):
                LATENCY.read_bag_events(directory, ["/missing"])


if __name__ == "__main__":
    unittest.main()
