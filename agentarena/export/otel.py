import json
import uuid
import time
from typing import Dict, Any, List
from agentarena.core.models import TaskTrajectory

class OpenTelemetryOTelExporter:
    """
    Converte le traiettorie dell'agente nel formato standard OpenTelemetry Spans/Traces (OTel).
    Permette l'ingestione diretta in Jaeger, Datadog, Honeycomb o Langfuse.
    """
    
    @staticmethod
    def trajectory_to_otel_spans(trajectory: TaskTrajectory) -> Dict[str, Any]:
        trace_id = uuid.uuid4().hex
        root_span_id = uuid.uuid4().hex[:16]
        
        start_nano = int(trajectory.started_at * 1e9)
        end_nano = int((trajectory.ended_at or trajectory.started_at + 1.0) * 1e9)

        root_span = {
            "trace_id": trace_id,
            "span_id": root_span_id,
            "parent_span_id": None,
            "name": f"AgentTaskExecution:{trajectory.task_id}",
            "kind": "SPAN_KIND_INTERNAL",
            "start_time_unix_nano": start_nano,
            "end_time_unix_nano": end_nano,
            "attributes": {
                "agent.id": trajectory.agent_id,
                "agent.version": trajectory.agent_version,
                "agent.prompt_version": trajectory.prompt_version,
                "agent.success": trajectory.success,
                "agent.total_tokens": trajectory.total_tokens,
                "agent.cost_usd": trajectory.cost_usd,
                "agent.step_count": len(trajectory.steps)
            },
            "status": {
                "code": "STATUS_CODE_OK" if trajectory.success else "STATUS_CODE_ERROR",
                "message": trajectory.error or ""
            }
        }

        child_spans = []
        current_time_offset = trajectory.started_at

        for step in trajectory.steps:
            step_span_id = uuid.uuid4().hex[:16]
            step_dur_sec = max(0.01, step.latency_ms / 1000.0)
            step_start_nano = int(current_time_offset * 1e9)
            step_end_nano = int((current_time_offset + step_dur_sec) * 1e9)

            step_span = {
                "trace_id": trace_id,
                "span_id": step_span_id,
                "parent_span_id": root_span_id,
                "name": f"Step:{step.step_number}",
                "kind": "SPAN_KIND_INTERNAL",
                "start_time_unix_nano": step_start_nano,
                "end_time_unix_nano": step_end_nano,
                "attributes": {
                    "gen_ai.prompt_tokens": step.prompt_tokens,
                    "gen_ai.completion_tokens": step.completion_tokens,
                    "agent.thought": step.thought or ""
                }
            }
            child_spans.append(step_span)

            # Tool call sub-spans
            for tc in step.tool_calls:
                tool_span_id = uuid.uuid4().hex[:16]
                tool_dur_sec = max(0.005, tc.duration_ms / 1000.0)
                tool_start_nano = step_start_nano
                tool_end_nano = int((current_time_offset + tool_dur_sec) * 1e9)

                tool_span = {
                    "trace_id": trace_id,
                    "span_id": tool_span_id,
                    "parent_span_id": step_span_id,
                    "name": f"Tool:{tc.name}",
                    "kind": "SPAN_KIND_CLIENT",
                    "start_time_unix_nano": tool_start_nano,
                    "end_time_unix_nano": tool_end_nano,
                    "attributes": {
                        "tool.name": tc.name,
                        "tool.arguments": json.dumps(tc.arguments),
                        "tool.output": json.dumps(tc.output),
                        "tool.status": tc.status
                    }
                }
                child_spans.append(tool_span)

            current_time_offset += step_dur_sec

        return {
            "resource_spans": [
                {
                    "resource": {
                        "attributes": {
                            "service.name": "agentarena",
                            "agent.name": trajectory.agent_id,
                            "agent.version": trajectory.agent_version
                        }
                    },
                    "scope_spans": [
                        {
                            "scope": {"name": "agentarena.tracer", "version": "1.0.0"},
                            "spans": [root_span] + child_spans
                        }
                    ]
                }
            ]
        }
