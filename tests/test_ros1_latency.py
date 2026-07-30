import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_ros1_latency.py"
SPEC = importlib.util.spec_from_file_location("analyze_ros1_latency", SCRIPT)
LATENCY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LATENCY)


class Ros1LatencyAnalysisTest(unittest.TestCase):
    def test_first_following_correlation_and_limit(self):
        upstream = [0.0, 1.0, 2.0]
        downstream = [0.020, 1.030, 2.700]
        self.assertEqual(
            LATENCY.first_following_latencies(upstream, downstream, 0.5),
            [0.020, 0.030000000000000027],
        )

    def test_repeated_actuator_publications_use_first_response_only(self):
        controller = [1.0, 2.0]
        actuator = [1.001, 1.002, 1.003, 2.004, 2.005]
        self.assertEqual(
            LATENCY.first_following_latencies(controller, actuator, 0.1),
            [0.0009999999999998899, 0.0040000000000000036],
        )

    def test_pipeline_metrics(self):
        events = {
            "/camera": [0.0, 0.1, 0.2, 0.3],
            "/controller": [0.02, 0.12, 0.22, 0.32],
            "/actuator": [0.03, 0.13, 0.23, 0.33],
        }
        report = LATENCY.analyze_events(
            events, "/camera", "/controller", "/actuator",
            list(events), 100.0)
        self.assertAlmostEqual(
            report["latency_ms"]["sensor_to_controller"]["mean"], 20.0)
        self.assertAlmostEqual(
            report["latency_ms"]["controller_to_actuator_command"]["mean"],
            10.0)
        self.assertAlmostEqual(
            report["latency_ms"]["end_to_end_command"]["mean"], 30.0)
        self.assertAlmostEqual(
            report["topic_timing"]["/camera"]["frequency_hz"], 10.0)
        self.assertAlmostEqual(
            report["topic_timing"]["/camera"]["jitter_stddev_ms"], 0.0)

    def test_empty_topic_is_reported(self):
        metrics = LATENCY.timing_metrics([])
        self.assertEqual(metrics["message_count"], 0)
        self.assertIsNone(metrics["frequency_hz"])


if __name__ == "__main__":
    unittest.main()
