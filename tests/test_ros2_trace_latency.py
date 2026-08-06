import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_ros2_trace_latency.py"
SPEC = importlib.util.spec_from_file_location("trace_latency", SCRIPT)
TRACE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRACE)


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
        report, rows = TRACE.analyze(events, "/controller", "/actuator")
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
