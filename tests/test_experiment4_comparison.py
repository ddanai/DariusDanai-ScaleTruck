import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_experiment4_comparison.py"
SPEC = importlib.util.spec_from_file_location("experiment4_comparison", SCRIPT)
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


class Experiment4StoppingRuleTest(unittest.TestCase):
    def test_analysis_refuses_incomplete_collection(self):
        with mock.patch.object(ANALYZER.comparison, "discover", return_value={1: {}}):
            with self.assertRaisesRegex(RuntimeError, "locked until all 30"):
                ANALYZER.validate_complete()

    def test_analysis_accepts_exact_preregistered_ids(self):
        complete = {run: {} for run in range(1, 31)}
        resources = {
            "controller": {"sample_count": 5},
            "lrc": {"sample_count": 5},
        }
        with mock.patch.object(ANALYZER.comparison, "discover", return_value=complete), \
                mock.patch.object(ANALYZER.comparison, "resource_run", return_value=resources):
            ANALYZER.validate_complete()


if __name__ == "__main__":
    unittest.main()
