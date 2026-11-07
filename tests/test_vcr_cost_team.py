import unittest
import os
import shutil
from agentarena.vcr.recorder import ToolVCRRecorder
from agentarena.cost.pricing import MultiModelCostEngine
from agentarena.collaboration.multi_agent import MultiAgentTeamTracker
from agentarena.core.models import TaskTrajectory

class TestVCRAndCostAndTeam(unittest.TestCase):
    def setUp(self):
        self.temp_cassette_dir = "test_cassettes_temp"
        self.vcr = ToolVCRRecorder(cassette_dir=self.temp_cassette_dir, mode="playback_or_record")

    def tearDown(self):
        if os.path.exists(self.temp_cassette_dir):
            shutil.rmtree(self.temp_cassette_dir)

    def test_vcr_record_and_playback(self):
        call_count = [0]
        def expensive_api(args):
            call_count[0] += 1
            return {"data": args["q"].upper()}

        # 1. Prima esecuzione: registra
        res1 = self.vcr.execute_with_vcr(
            cassette_name="web_query",
            tool_name="search",
            arguments={"q": "antigravity"},
            actual_fn=expensive_api
        )
        self.assertEqual(call_count[0], 1)
        self.assertEqual(res1.output, {"data": "ANTIGRAVITY"})

        # 2. Seconda esecuzione: riproduce dalla cassetta (nessun incremento di call_count)
        res2 = self.vcr.execute_with_vcr(
            cassette_name="web_query",
            tool_name="search",
            arguments={"q": "antigravity"},
            actual_fn=expensive_api
        )
        self.assertEqual(call_count[0], 1)  # Non ha richiamato l'API!
        self.assertEqual(res2.output, {"data": "ANTIGRAVITY"})
        self.assertEqual(res2.duration_ms, 1.0)

    def test_cost_engine(self):
        cost_mini = MultiModelCostEngine.calculate_cost("gpt-4o-mini", 1000, 200)
        self.assertGreater(cost_mini, 0.0)

        cost_flash = MultiModelCostEngine.calculate_cost("gemini-1.5-flash", 1000, 200)
        self.assertGreater(cost_flash, 0.0)
        self.assertLess(cost_flash, cost_mini)

    def test_multi_agent_team_tracker(self):
        tracker = MultiAgentTeamTracker("SupportTeam", "v1")
        tracker.record_agent_interaction("RouterAgent", "RefundAgent", "handoff", "Process refund ORD-1")
        
        traj = TaskTrajectory(task_id="t1", run_id="r1", agent_id="team", agent_version="v1", prompt_version="p1")
        tracker.attach_to_trajectory(traj)

        self.assertIn("multi_agent_team", traj.metadata)
        self.assertEqual(traj.metadata["multi_agent_team"]["total_hand_offs"], 1)

if __name__ == "__main__":
    unittest.main()
