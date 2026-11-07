import unittest
from agentarena.badging.generator import SvgBadgeGenerator
from agentarena.matrix.aggregator import MultiRunMatrixAggregator

class TestBadgeAndMatrix(unittest.TestCase):
    def test_badge_generation(self):
        svg = SvgBadgeGenerator.generate_badge_svg("Pass@1", "100%", "success")
        self.assertIn("<svg", svg)
        self.assertIn("Pass@1", svg)
        self.assertIn("100%", svg)

    def test_matrix_aggregator_flakiness(self):
        repeated = {
            "task_stable_pass": [{"success": True, "total_tokens": 100}, {"success": True, "total_tokens": 105}],
            "task_flaky": [{"success": True, "total_tokens": 120}, {"success": False, "total_tokens": 90}],
            "task_stable_fail": [{"success": False, "total_tokens": 80}, {"success": False, "total_tokens": 85}]
        }
        res = MultiRunMatrixAggregator.aggregate_runs(repeated)
        self.assertEqual(res["total_tasks"], 3)
        self.assertEqual(res["flaky_tasks_count"], 1)
        self.assertEqual(res["task_breakdown"]["task_flaky"]["is_flaky"], True)
        self.assertEqual(res["task_breakdown"]["task_stable_pass"]["is_flaky"], False)

if __name__ == "__main__":
    unittest.main()
