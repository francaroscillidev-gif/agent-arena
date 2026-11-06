from typing import List
from agentarena.core.models import BenchmarkTask
from agentarena.tasks.loader import DatasetLoader
import os

DEFAULT_DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets", "standard_eval_suite.json")

def get_standard_tasks(dataset_path: str = None) -> List[BenchmarkTask]:
    path = dataset_path or DEFAULT_DATASET_PATH
    if os.path.exists(path):
        return DatasetLoader.load_from_json(path)
    
    # Fallback if file missing
    return [
        BenchmarkTask(
            id="task_calc_finance",
            name="Calculate Quarterly Revenue Growth",
            description="Fetch Q1 and Q2 financial data from db and compute percentage growth.",
            category="Financial Analysis",
            difficulty="easy",
            prompt="Calcola la percentuale di crescita dei ricavi tra Q1 ($120k) e Q2 ($156k).",
            expected_output="30%",
            expected_tools=["calculator", "financial_db"],
            max_steps=3
        )
    ]
