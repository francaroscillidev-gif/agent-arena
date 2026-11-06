import json
import os
from typing import List, Dict, Any, Optional
from .models import TaskTrajectory

class RunStorage:
    def __init__(self, runs_dir: str = "runs"):
        self.runs_dir = runs_dir
        os.makedirs(self.runs_dir, exist_ok=True)

    def save_trajectory(self, trajectory: TaskTrajectory) -> str:
        agent_dir = os.path.join(self.runs_dir, trajectory.agent_version)
        os.makedirs(agent_dir, exist_ok=True)
        filename = f"{trajectory.task_id}_{trajectory.run_id}.json"
        filepath = os.path.join(agent_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trajectory.to_dict(), f, indent=2, ensure_ascii=False)
        return filepath

    def list_versions(self) -> List[str]:
        if not os.path.exists(self.runs_dir):
            return []
        versions = [
            d for d in os.listdir(self.runs_dir) 
            if os.path.isdir(os.path.join(self.runs_dir, d)) and not d.startswith(".")
        ]
        return sorted(versions)

    def load_runs_for_version(self, version: str) -> List[Dict[str, Any]]:
        target_dir = os.path.join(self.runs_dir, version)
        if not os.path.isdir(target_dir):
            return []
        
        runs = []
        for file in sorted(os.listdir(target_dir)):
            if file.endswith(".json"):
                try:
                    with open(os.path.join(target_dir, file), "r", encoding="utf-8") as f:
                        runs.append(json.load(f))
                except Exception:
                    continue
        return runs

    def get_version_summary(self, version: str) -> Dict[str, Any]:
        runs = self.load_runs_for_version(version)
        if not runs:
            return {
                "version": version,
                "total_tasks": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "avg_tokens": 0.0,
                "avg_steps": 0.0,
                "total_cost": 0.0
            }

        total = len(runs)
        successes = sum(1 for r in runs if r.get("success", False))
        total_duration = sum(r.get("duration_seconds", 0) for r in runs)
        total_tokens = sum(r.get("total_tokens", 0) for r in runs)
        total_steps = sum(len(r.get("steps", [])) for r in runs)
        total_cost = sum(r.get("cost_usd", 0.0) for r in runs)

        return {
            "version": version,
            "total_tasks": total,
            "successes": successes,
            "success_rate": round((successes / total) * 100, 1),
            "avg_duration": round(total_duration / total, 2),
            "avg_tokens": round(total_tokens / total, 1),
            "avg_steps": round(total_steps / total, 2),
            "total_cost": round(total_cost, 4)
        }
