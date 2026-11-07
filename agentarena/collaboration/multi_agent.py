import time
import uuid
from typing import Dict, Any, List
from agentarena.core.models import TaskTrajectory, AgentStepRecord, ToolCallRecord, BenchmarkTask

class MultiAgentTeamTracker:
    """
    Tracciatore per sistemi multi-agente (Router, Orchestrator-Workers, Debate, Hierarchical Teams).
    Traccia i passaggi di consegne (hand-offs), la comunicazione inter-agente e la latenza dei singoli agenti.
    """

    def __init__(self, team_name: str, team_version: str):
        self.team_name = team_name
        self.team_version = team_version
        self.hand_offs = []

    def record_agent_interaction(
        self,
        from_agent: str,
        to_agent: str,
        intent: str,
        payload_summary: str,
        latency_ms: float = 120.0
    ):
        self.hand_offs.append({
            "timestamp": time.time(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "intent": intent,
            "payload_summary": payload_summary,
            "latency_ms": latency_ms
        })

    def attach_to_trajectory(self, trajectory: TaskTrajectory) -> TaskTrajectory:
        trajectory.metadata["multi_agent_team"] = {
            "team_name": self.team_name,
            "team_version": self.team_version,
            "total_hand_offs": len(self.hand_offs),
            "hand_offs": self.hand_offs
        }
        return trajectory
