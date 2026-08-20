import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from matched_controller_workload import process_image


class MatchedControllerWorkloadTest(unittest.TestCase):
    def test_is_deterministic(self):
        image = bytes(range(256)) * 20
        self.assertEqual(process_image(image, 64, 80, 3),
                         process_image(image, 64, 80, 3))

    def test_pass_count_changes_work(self):
        image = bytes(range(128))
        self.assertNotEqual(process_image(image, 16, 8, 1)[2],
                            process_image(image, 16, 8, 2)[2])

    def test_rejects_invalid_pass_count(self):
        with self.assertRaises(ValueError):
            process_image(b"abc", 1, 1, 0)


if __name__ == "__main__":
    unittest.main()
