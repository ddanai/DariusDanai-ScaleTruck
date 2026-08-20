import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_experiment3_comparison.py"
SPEC = importlib.util.spec_from_file_location("experiment3_comparison", SCRIPT)
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


class Experiment3ResourceParsingTest(unittest.TestCase):
    def test_reads_24_hour_pidstat_without_ampm_column(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ros2-run-01-environment.txt").write_text(
                "controller_pid=38\nlrc_pid=41\n")
            (root / "ros2-run-01-cpu-memory.txt").write_text(
                "09:28:17 0 38 1.00 2.00 0.00 0.00 3.00 0 0.00 0.00 624260 53652 0.17 python3\n"
                "09:28:17 0 41 2.00 2.00 0.00 0.00 4.00 3 0.00 0.00 583372 23204 0.07 lrc_node\n")
            with mock.patch.object(ANALYZER, "RESOURCES", root):
                result = ANALYZER.resource_run("ros2", 1)
            self.assertEqual(result["controller"]["cpu_pct"], 3.0)
            self.assertEqual(result["lrc"]["cpu_pct"], 4.0)
            self.assertAlmostEqual(result["combined"]["rss_mib"],
                                   (53652 + 23204) / 1024.0)


if __name__ == "__main__":
    unittest.main()
