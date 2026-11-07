import time
import json
from typing import Dict, Any, Generator

class TrajectoryReplayDebugger:
    """
    Motore di Replay per riprodurre e analizzare l'esecuzione di un agente passo per passo
    con timing simulato o avanzamento manuale.
    """

    @staticmethod
    def stream_steps(trajectory_data: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Produce un generatore di step per il replay in tempo reale."""
        task_id = trajectory_data.get("task_id")
        agent_id = trajectory_data.get("agent_id")
        steps = trajectory_data.get("steps", [])

        yield {
            "type": "RUN_START",
            "task_id": task_id,
            "agent_id": agent_id,
            "version": trajectory_data.get("agent_version"),
            "total_steps": len(steps)
        }

        for step in steps:
            yield {
                "type": "STEP_START",
                "step_number": step.get("step_number"),
                "thought": step.get("thought"),
                "tokens": step.get("prompt_tokens", 0) + step.get("completion_tokens", 0),
                "latency_ms": step.get("latency_ms", 0)
            }

            for tc in step.get("tool_calls", []):
                yield {
                    "type": "TOOL_INVOCATION",
                    "step_number": step.get("step_number"),
                    "tool": tc.get("name"),
                    "arguments": tc.get("arguments"),
                    "output": tc.get("output"),
                    "status": tc.get("status"),
                    "duration_ms": tc.get("duration_ms")
                }

        yield {
            "type": "RUN_FINISH",
            "task_id": task_id,
            "success": trajectory_data.get("success"),
            "final_output": trajectory_data.get("final_output"),
            "duration_seconds": trajectory_data.get("duration_seconds")
        }
