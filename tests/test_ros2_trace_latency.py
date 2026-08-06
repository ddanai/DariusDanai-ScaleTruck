import importlib.util
from pathlib import Path
import unittest


def load_analyzer(filename):
    script = Path(__file__).parents[1] / "scripts" / filename
    spec = importlib.util.spec_from_file_location(filename, script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ANALYZERS = [
    load_analyzer("analyze_ros1_trace_latency.py"),
    load_analyzer("analyze_ros2_trace_latency.py"),
]


class Ros2TraceLatencyTest(unittest.TestCase):
    def test_matches_exact_trace_and_uses_first_timer_publication(self):
        events = {
            "/controller": [
                {"trace_id": 1, "sensor_s": 1.0, "receive_s": 1.010},
                {"trace_id": 1, "sensor_s": 1.0, "receive_s": 1.020},
                {"trace_id": 2, "sensor_s": 2.0, "receive_s": 2.012},
            ],
            "/actuator": [
                {"trace_id": 1, "sensor_s": 1.0, "receive_s": 1.025},
                {"trace_id": 1, "sensor_s": 1.0, "receive_s": 1.030},
                {"trace_id": 2, "sensor_s": 2.0, "receive_s": 2.030},
            ],
        }
        for analyzer in ANALYZERS:
            with self.subTest(analyzer=analyzer.__name__):
                report, rows = analyzer.analyze(events, "/controller", "/actuator")
                self.assertEqual(report["trace_count"], 2)
                self.assertEqual(len(rows), 2)
                self.assertAlmostEqual(
                    report["latency_ms"]["sensor_to_controller"]["mean"], 11.0)
                self.assertAlmostEqual(
                    report["latency_ms"]["controller_to_actuator_command"]["mean"], 16.5)
                self.assertAlmostEqual(
                    report["latency_ms"]["end_to_end_command"]["mean"], 27.5)


if __name__ == "__main__":
    unittest.main()
