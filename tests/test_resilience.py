import unittest
from agentarena.resilience.chaos import ChaosToolProxy, ChaosFaultConfig
from agentarena.resilience.evaluator import ResilienceEvaluator
from agentarena.core.models import TaskTrajectory, AgentStepRecord, ToolCallRecord

class TestChaosAndResilience(unittest.TestCase):
    def test_chaos_proxy_injection(self):
        # Config 100% failure
        config = ChaosFaultConfig(failure_rate=1.0)
        proxy = ChaosToolProxy(config)
        record = proxy.execute_tool("calculator", {"expr": "2+2"})
        self.assertEqual(record.status, "error")
        self.assertIn("Simulated 503", record.error)

    def test_resilience_evaluator(self):
        traj = TaskTrajectory(
            task_id="t1", run_id="r1", agent_id="ag", agent_version="v1", prompt_version="p1"
        )
        # Step 1: Tool failure
        traj.steps.append(AgentStepRecord(
            step_number=1,
            tool_calls=[ToolCallRecord(name="web_search", arguments={}, status="error", error="Timeout")]
        ))
        # Step 2: Self-healing retry / fallback
        traj.steps.append(AgentStepRecord(
            step_number=2,
            tool_calls=[ToolCallRecord(name="doc_search", arguments={}, status="success", output="Found")]
        ))
        traj.finish(success=True)

        res = ResilienceEvaluator.evaluate_resilience(traj)
        self.assertIn("resilience_self_healing", res)
        self.assertEqual(res["resilience_self_healing"].score, 1.0)
        self.assertTrue(res["resilience_self_healing"].passed)

if __name__ == "__main__":
    unittest.main()
