import json
import yaml
import os
from typing import List, Dict, Any
from agentarena.core.models import BenchmarkTask

class DatasetLoader:
    """Caricatore e parser di benchmark task da file YAML o JSON standard."""
    
    @staticmethod
    def load_from_json(filepath: str) -> List[BenchmarkTask]:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        tasks = []
        for item in data:
            tasks.append(BenchmarkTask(
                id=item["id"],
                name=item["name"],
                description=item.get("description", ""),
                category=item.get("category", "General"),
                difficulty=item.get("difficulty", "medium"),
                prompt=item["prompt"],
                expected_output=item.get("expected_output"),
                expected_tools=item.get("expected_tools", []),
                max_steps=item.get("max_steps", 10),
                validation_criteria=item.get("validation_criteria", {})
            ))
        return tasks

    @staticmethod
    def save_to_json(tasks: List[BenchmarkTask], filepath: str):
        data = [t.__dict__ for t in tasks]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
