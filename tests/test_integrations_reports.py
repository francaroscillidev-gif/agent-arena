import unittest
from agentarena.integrations.adapters import LangChainAgentArenaAdapter, LlamaIndexAgentArenaAdapter
from agentarena.reports.html_report import StandaloneHtmlReportGenerator
from agentarena.core.storage import RunStorage
from agentarena.core.models import BenchmarkTask

class TestIntegrationsAndReports(unittest.TestCase):
    def test_langchain_adapter(self):
        # Mock callable executor
        mock_executor = lambda prompt: f"Echo: {prompt}"
        adapter = LangChainAgentArenaAdapter(
            agent_executor=mock_executor,
            name="LangChainAgent",
            version="lc-v1",
            prompt_version="p1"
        )
        task = BenchmarkTask(id="test_task", name="Test", description="Desc", category="Cat", difficulty="easy", prompt="Hello")
        traj = adapter.run_task(task)
        self.assertTrue(traj.success)
        self.assertIn("Echo: Hello", traj.final_output)

    def test_llamaindex_adapter(self):
        class MockLlamaRunner:
            def chat(self, prompt):
                return "Llama response"

        adapter = LlamaIndexAgentArenaAdapter(
            agent_runner=MockLlamaRunner(),
            name="LlamaAgent",
            version="llama-v1",
            prompt_version="p1"
        )
        task = BenchmarkTask(id="test_task", name="Test", description="Desc", category="Cat", difficulty="easy", prompt="Query")
        traj = adapter.run_task(task)
        self.assertTrue(traj.success)
        self.assertEqual(traj.final_output, "Llama response")

    def test_html_report_generation(self):
        storage = RunStorage()
        html = StandaloneHtmlReportGenerator.generate_html_report(storage, "v1.0.0-baseline", "v2.0.0-optimized")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("AgentArena Audit Report", html)
        self.assertIn("Franca Roscilli", html)

if __name__ == "__main__":
    unittest.main()
