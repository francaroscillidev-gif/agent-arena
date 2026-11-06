from typing import Dict, Any, List
from agentarena.core.models import TaskTrajectory, BenchmarkTask, EvaluationMetric

class TrajectoryEvaluator:
    @staticmethod
    def evaluate(trajectory: TaskTrajectory, task: BenchmarkTask) -> Dict[str, EvaluationMetric]:
        metrics = {}

        # 1. Tool Call Accuracy: did agent use required tools?
        used_tools = set()
        for step in trajectory.steps:
            for tc in step.tool_calls:
                used_tools.add(tc.name)
        
        if task.expected_tools:
            matched_tools = [t for t in task.expected_tools if t in used_tools]
            score = len(matched_tools) / len(task.expected_tools)
            metrics["tool_coverage"] = EvaluationMetric(
                name="Tool Coverage",
                score=round(score, 2),
                passed=(score >= 0.8),
                details=f"Called {len(matched_tools)}/{len(task.expected_tools)} expected tools: {matched_tools}"
            )

        # 2. Step Budget Efficiency
        step_count = len(trajectory.steps)
        step_passed = step_count <= task.max_steps
        step_score = max(0.0, 1.0 - (max(0, step_count - 1) / max(1, task.max_steps)))
        metrics["step_efficiency"] = EvaluationMetric(
            name="Step Budget Efficiency",
            score=round(step_score, 2),
            passed=step_passed,
            details=f"Used {step_count}/{task.max_steps} max allowable steps."
        )

        # 3. Output Exact/Keyword Match
        if task.expected_output and trajectory.final_output:
            out_lower = trajectory.final_output.lower()
            exp_lower = task.expected_output.lower()
            is_match = exp_lower in out_lower
            metrics["output_match"] = EvaluationMetric(
                name="Output Accuracy",
                score=1.0 if is_match else 0.0,
                passed=is_match,
                details="Expected output substring present" if is_match else "Output missing target result"
            )

        # 4. Tool Execution Health: check if tool errors occurred
        tool_errors = 0
        total_calls = 0
        for step in trajectory.steps:
            for tc in step.tool_calls:
                total_calls += 1
                if tc.status == "error":
                    tool_errors += 1
        
        health_score = 1.0 if total_calls == 0 else max(0.0, (total_calls - tool_errors) / total_calls)
        metrics["tool_reliability"] = EvaluationMetric(
            name="Tool Reliability",
            score=round(health_score, 2),
            passed=(tool_errors == 0),
            details=f"{tool_errors} tool failures out of {total_calls} calls"
        )

        return metrics
