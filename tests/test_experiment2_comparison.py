import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "analyze_experiment2_comparison.py"
SPEC = importlib.util.spec_from_file_location("experiment2_comparison", SCRIPT)
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


class Experiment2ComparisonTest(unittest.TestCase):
    def test_run_level_estimate_does_not_weight_large_runs_more(self):
        runs = {
            1: {"latency": [1.0]},
            2: {"latency": [100.0] * 100},
        }
        self.assertEqual(ANALYZER.run_level_estimate(runs, "latency", "median"),
                         [1.0, 100.0])

    def test_bootstrap_difference_is_reproducible_and_directional(self):
        result = ANALYZER.bootstrap_difference([10.0] * 5, [4.0] * 5,
                                               iterations=100, seed=7)
        self.assertEqual(result["estimate"], -6.0)
        self.assertEqual(result["ci95_low"], -6.0)
        self.assertEqual(result["ci95_high"], -6.0)
        self.assertEqual(result["unit"], "run")


if __name__ == "__main__":
    unittest.main()
