import uuid
import time
from typing import Dict, Any, List
from agentarena.core.models import TaskTrajectory, AgentStepRecord, ToolCallRecord, BenchmarkTask
from agentarena.evaluators.evaluator import TrajectoryEvaluator
from agentarena.judge.llm_judge import LLMasAJudgeEvaluator
from agentarena.core.storage import RunStorage

class BaseAgent:
    """Interface that any agent to be benchmarked should implement."""
    def __init__(self, name: str, version: str, prompt_version: str):
        self.name = name
        self.version = version
        self.prompt_version = prompt_version

    def run_task(self, task: BenchmarkTask) -> TaskTrajectory:
        raise NotImplementedError

class AgentHarness:
    """Benchmark runner for executing benchmarks across agents and recording trajectories."""
    def __init__(self, storage: RunStorage = None, enable_llm_judge: bool = True):
        self.storage = storage or RunStorage()
        self.enable_llm_judge = enable_llm_judge

    def run_benchmark(self, agent: BaseAgent, tasks: List[BenchmarkTask]) -> List[TaskTrajectory]:
        trajectories = []
        for task in tasks:
            traj = agent.run_task(task)
            # 1. Deterministic Multi-Metric Evaluation
            metrics = TrajectoryEvaluator.evaluate(traj, task)
            
            # 2. LLM-as-a-Judge Evaluation (Reasoning, Loop prevention, Faithfulness)
            if self.enable_llm_judge:
                judge_metrics = LLMasAJudgeEvaluator.evaluate_trajectory(traj, task)
                metrics.update(judge_metrics)

            traj.metrics = metrics
            
            # Save run
            self.storage.save_trajectory(traj)
            trajectories.append(traj)
        return trajectories
