import unittest
from agentarena.stats.significance import StatisticalSignificanceAnalyzer
from agentarena.leaderboard.elo import EloRatingSystem
from agentarena.guardrails.enforcer import GuardrailsPolicyEnforcer
from agentarena.replay.debugger import TrajectoryReplayDebugger
from agentarena.core.models import TaskTrajectory, AgentStepRecord, ToolCallRecord

class TestEnterpriseModules(unittest.TestCase):
    def test_statistical_significance(self):
        sample_a = [0.0, 0.0, 1.0, 0.0, 1.0]
        sample_b = [1.0, 1.0, 1.0, 1.0, 1.0]
        p_val = StatisticalSignificanceAnalyzer.permutation_test_p_value(sample_a, sample_b, n_permutations=500)
        self.assertIsInstance(p_val, float)
        self.assertGreaterEqual(p_val, 0.0)
        self.assertLessEqual(p_val, 1.0)

    def test_elo_leaderboard(self):
        runs_a = [{"task_id": "t1", "success": False, "total_tokens": 1000}]
        runs_b = [{"task_id": "t1", "success": True, "total_tokens": 500}]
        leaderboard = EloRatingSystem.compute_leaderboard({"v1": runs_a, "v2": runs_b})
        self.assertEqual(len(leaderboard), 2)
        self.assertEqual(leaderboard[0]["version"], "v2")
        self.assertGreater(leaderboard[0]["elo_rating"], leaderboard[1]["elo_rating"])

    def test_guardrails_enforcer(self):
        # 1. Safe trajectory
        traj = TaskTrajectory(task_id="t1", run_id="r1", agent_id="a", agent_version="v1", prompt_version="p1")
        traj.total_tokens = 500
        traj.cost_usd = 0.01
        is_safe, violations = GuardrailsPolicyEnforcer.validate_trajectory_guardrails(traj)
        self.assertTrue(is_safe)
        self.assertEqual(len(violations), 0)

        # 2. Dangerous tool call
        bad_traj = TaskTrajectory(task_id="t2", run_id="r2", agent_id="a", agent_version="v1", prompt_version="p1")
        bad_traj.steps.append(AgentStepRecord(
            step_number=1,
            tool_calls=[ToolCallRecord(name="eval", arguments={"code": "1+1"})]
        ))
        is_safe_bad, violations_bad = GuardrailsPolicyEnforcer.validate_trajectory_guardrails(bad_traj)
        self.assertFalse(is_safe_bad)
        self.assertTrue(any("Forbidden" in v for v in violations_bad))

    def test_trajectory_replay_stream(self):
        traj_data = {
            "task_id": "t1",
            "agent_id": "a",
            "agent_version": "v1",
            "steps": [{"step_number": 1, "thought": "Thinking..."}],
            "success": True
        }
        events = list(TrajectoryReplayDebugger.stream_steps(traj_data))
        self.assertGreaterEqual(len(events), 3) # RUN_START, STEP_START, RUN_FINISH
        self.assertEqual(events[0]["type"], "RUN_START")
        self.assertEqual(events[-1]["type"], "RUN_FINISH")

if __name__ == "__main__":
    unittest.main()
