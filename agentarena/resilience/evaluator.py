from typing import Dict, Any, List
from agentarena.core.models import TaskTrajectory, EvaluationMetric

class ResilienceEvaluator:
    """Valuta la capacità di autoguarigione e tolleranza ai guasti (Self-Correction Score)."""

    @staticmethod
    def evaluate_resilience(trajectory: TaskTrajectory) -> Dict[str, EvaluationMetric]:
        metrics = {}
        
        errors_encountered = 0
        successful_retries_or_fallbacks = 0
        consecutive_repeats_on_failure = 0

        prev_tool_failed = False
        prev_tool_name = None

        for step in trajectory.steps:
            for tc in step.tool_calls:
                if tc.status == "error":
                    errors_encountered += 1
                    prev_tool_failed = True
                    prev_tool_name = tc.name
                else:
                    if prev_tool_failed:
                        # Ha gestito l'errore precedente con successo (retry con args corretti o fallback su tool alternativo)
                        successful_retries_or_fallbacks += 1
                        prev_tool_failed = False

        recovery_rate = 1.0 if errors_encountered == 0 else (successful_retries_or_fallbacks / errors_encountered)
        
        metrics["resilience_self_healing"] = EvaluationMetric(
            name="Resilience: Fault Self-Healing",
            score=round(recovery_rate, 2),
            passed=(recovery_rate >= 0.7 or errors_encountered == 0),
            details=f"Errors encountered: {errors_encountered}. Successfully recovered: {successful_retries_or_fallbacks}"
        )

        return metrics
