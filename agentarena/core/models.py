"""Core data models for AgentArena."""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import time
import uuid

@dataclass
class ToolCallRecord:
    name: str
    arguments: Dict[str, Any]
    output: Optional[Any] = None
    duration_ms: float = 0.0
    status: str = "success"  # success, error
    error: Optional[str] = None

@dataclass
class AgentStepRecord:
    step_number: int
    thought: Optional[str] = None
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    output: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0

@dataclass
class EvaluationMetric:
    name: str
    score: float  # typically 0.0 to 1.0 or custom numeric
    passed: bool
    details: Optional[str] = None

@dataclass
class TaskTrajectory:
    task_id: str
    run_id: str
    agent_id: str
    agent_version: str
    prompt_version: str
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    duration_seconds: float = 0.0
    steps: List[AgentStepRecord] = field(default_factory=list)
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    success: bool = False
    metrics: Dict[str, EvaluationMetric] = field(default_factory=dict)
    final_output: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool, final_output: Optional[str] = None, error: Optional[str] = None):
        self.ended_at = time.time()
        self.duration_seconds = round(self.ended_at - self.started_at, 3)
        self.success = success
        self.final_output = final_output
        self.error = error
        
        # Aggregations
        self.prompt_tokens = sum(s.prompt_tokens for s in self.steps)
        self.completion_tokens = sum(s.completion_tokens for s in self.steps)
        self.total_tokens = self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class BenchmarkTask:
    id: str
    name: str
    description: str
    category: str
    difficulty: str  # easy, medium, hard
    prompt: str
    expected_output: Optional[str] = None
    expected_tools: List[str] = field(default_factory=list)
    max_steps: int = 10
    validation_criteria: Dict[str, Any] = field(default_factory=dict)
