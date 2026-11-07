import json
from typing import Dict, Any, List

class MultiRunMatrixAggregator:
    """
    Esegue e aggrega N ripetizioni dello stesso benchmark per misurare la varianza e stabilità:
    - Pass@1, Pass@3, Pass@k
    - Flakiness Rate (% di task che alternano PASS e FAIL tra i tentativi)
    """

    @staticmethod
    def aggregate_runs(repeated_runs_by_task: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        task_stats = {}
        total_flaky_tasks = 0
        total_tasks = len(repeated_runs_by_task)

        for task_id, runs in repeated_runs_by_task.items():
            k = len(runs)
            successes = sum(1 for r in runs if r.get("success"))
            pass_rate = successes / max(1, k)
            
            # Un task è 'flaky' se non è né sempre 100% né sempre 0%
            is_flaky = (0 < successes < k)
            if is_flaky:
                total_flaky_tasks += 1

            tokens = [r.get("total_tokens", 0) for r in runs]
            avg_tok = sum(tokens) / max(1, k)

            task_stats[task_id] = {
                "attempts": k,
                "successes": successes,
                "pass_at_k": round(pass_rate * 100, 1),
                "is_flaky": is_flaky,
                "avg_tokens": round(avg_tok, 1)
            }

        flakiness_index = (total_flaky_tasks / max(1, total_tasks)) * 100 if total_tasks > 0 else 0.0

        return {
            "total_tasks": total_tasks,
            "flaky_tasks_count": total_flaky_tasks,
            "flakiness_rate_pct": round(flakiness_index, 1),
            "task_breakdown": task_stats
        }
