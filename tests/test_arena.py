"""
Test suite per AgentArena Core, Evaluators e Storage.
Eseguibile tramite: python3 -m unittest discover -s tests
"""
import unittest
import os
import shutil
from agentarena.core.models import TaskTrajectory, AgentStepRecord, ToolCallRecord, BenchmarkTask
from agentarena.core.storage import RunStorage
from agentarena.evaluators.evaluator import TrajectoryEvaluator
from agentarena.evaluators.reporter import ReportExporter
from agentarena.core.mock_agents import MockLegacyAgent, MockOptimizedAgent
from agentarena.core.harness import AgentHarness
from agentarena.tasks.benchmarks import get_standard_tasks

class TestAgentArena(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_runs_temp"
        self.storage = RunStorage(runs_dir=self.test_dir)
        self.harness = AgentHarness(storage=self.storage)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mock_agents_benchmark(self):
        tasks = get_standard_tasks()
        self.assertGreater(len(tasks), 0)

        # Baseline
        agent_v1 = MockLegacyAgent()
        trajs_v1 = self.harness.run_benchmark(agent_v1, tasks)
        self.assertEqual(len(trajs_v1), len(tasks))

        # Optimized
        agent_v2 = MockOptimizedAgent()
        trajs_v2 = self.harness.run_benchmark(agent_v2, tasks)
        self.assertEqual(len(trajs_v2), len(tasks))

        # Check storage
        versions = self.storage.list_versions()
        self.assertIn("v1.0.0-baseline", versions)
        self.assertIn("v2.0.0-optimized", versions)

        # Check evaluator metrics
        s_v1 = self.storage.get_version_summary("v1.0.0-baseline")
        s_v2 = self.storage.get_version_summary("v2.0.0-optimized")
        self.assertGreater(s_v2["success_rate"], s_v1["success_rate"])

    def test_markdown_diff_export(self):
        tasks = get_standard_tasks()
        self.harness.run_benchmark(MockLegacyAgent(), tasks)
        self.harness.run_benchmark(MockOptimizedAgent(), tasks)

        exporter = ReportExporter(self.storage)
        diff_md = exporter.generate_markdown_diff("v1.0.0-baseline", "v2.0.0-optimized")
        self.assertIn("AgentArena Benchmark Diff", diff_md)
        self.assertIn("Success Rate", diff_md)

if __name__ == "__main__":
    unittest.main()
