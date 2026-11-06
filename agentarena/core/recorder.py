import os
import time
import uuid
from typing import Callable, Dict, Any, List, Optional
from agentarena.core.models import TaskTrajectory, AgentStepRecord, ToolCallRecord, BenchmarkTask
from agentarena.core.harness import BaseAgent

class GenericLLMAgent(BaseAgent):
    """
    Adapter generico per testare agenti collegati ad API esterne (OpenAI, Anthropic, Gemini, o locale).
    Accetta una funzione di inferenza step-by-step o esecuzione completa.
    """
    def __init__(
        self,
        name: str,
        version: str,
        prompt_version: str,
        runner_fn: Callable[[BenchmarkTask], TaskTrajectory]
    ):
        super().__init__(name=name, version=version, prompt_version=prompt_version)
        self.runner_fn = runner_fn

    def run_task(self, task: BenchmarkTask) -> TaskTrajectory:
        return self.runner_fn(task)


class TrajectoryRecorder:
    """
    Context manager / helper per catturare e profilare step e tool call in tempo reale.
    """
    def __init__(self, task_id: str, agent_id: str, agent_version: str, prompt_version: str):
        self.trajectory = TaskTrajectory(
            task_id=task_id,
            run_id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            agent_version=agent_version,
            prompt_version=prompt_version,
            started_at=time.time()
        )
        self.current_step = 1

    def record_step(
        self,
        thought: Optional[str] = None,
        tool_calls: Optional[List[ToolCallRecord]] = None,
        output: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0
    ):
        step = AgentStepRecord(
            step_number=self.current_step,
            thought=thought,
            tool_calls=tool_calls or [],
            output=output,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms
        )
        self.trajectory.steps.append(step)
        self.current_step += 1

    def finish(self, success: bool, final_output: Optional[str] = None, error: Optional[str] = None, cost_usd: float = 0.0) -> TaskTrajectory:
        self.trajectory.cost_usd = cost_usd
        self.trajectory.finish(success=success, final_output=final_output, error=error)
        return self.trajectory
