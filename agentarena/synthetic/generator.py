import random
import uuid
from typing import List, Dict, Any
from agentarena.core.models import BenchmarkTask

class SyntheticTaskGenerator:
    """
    Generatore automatico di compiti di benchmark sintetici per generare test suite scalabili
    su domini specifici (e-commerce, DevOps, finanza, sicurezza).
    """

    DOMAINS = {
        "ecommerce": {
            "categories": ["Order Management", "Inventory", "Customer Support"],
            "orders": ["ORD-101", "ORD-202", "ORD-303", "ORD-999"],
            "amounts": [25, 59, 120, 450],
            "tools": ["lookup_order", "process_refund", "send_notification"]
        },
        "devops": {
            "categories": ["Incident Response", "Database Tuning", "Cluster Health"],
            "services": ["auth-service", "billing-gateway", "event-worker"],
            "tools": ["check_logs", "restart_pod", "explain_query", "schema_inspector"]
        },
        "finance": {
            "categories": ["P&L Analysis", "Tax Validation", "Reconciliation"],
            "quarters": ["Q1", "Q2", "Q3", "Q4"],
            "tools": ["financial_db", "calculator", "currency_converter"]
        }
    }

    @classmethod
    def generate_suite(cls, domain: str = "ecommerce", count: int = 3) -> List[BenchmarkTask]:
        config = cls.DOMAINS.get(domain, cls.DOMAINS["ecommerce"])
        tasks = []

        for i in range(1, count + 1):
            task_id = f"synth_{domain}_{i}_{uuid.uuid4().hex[:6]}"
            category = random.choice(config["categories"])

            if domain == "ecommerce":
                order = random.choice(config["orders"])
                amt = random.choice(config["amounts"])
                tasks.append(BenchmarkTask(
                    id=task_id,
                    name=f"Synthesized Refund Check #{i}",
                    description=f"Validate eligibility and process automated refund for {order}.",
                    category=category,
                    difficulty="medium",
                    prompt=f"Richiesta di rimborso per ordine {order} con importo {amt}€. Esegui verifica e notifica.",
                    expected_output="Refund successful",
                    expected_tools=config["tools"],
                    max_steps=4
                ))
            elif domain == "devops":
                svc = random.choice(config["services"])
                tasks.append(BenchmarkTask(
                    id=task_id,
                    name=f"Synthesized DevOps Outage #{i}",
                    description=f"Diagnose latency spike on {svc} microservice.",
                    category=category,
                    difficulty="hard",
                    prompt=f"Il servizio {svc} ha una latenza anomala p99 > 3s. Analizza i log e applica fix.",
                    expected_output="Fix applied",
                    expected_tools=config["tools"],
                    max_steps=5
                ))
            else: # finance
                q = random.choice(config["quarters"])
                tasks.append(BenchmarkTask(
                    id=task_id,
                    name=f"Synthesized Financial Analysis #{i}",
                    description=f"Verify revenue reconciliation for {q}.",
                    category=category,
                    difficulty="easy",
                    prompt=f"Verifica la riconciliazione contabile per il trimestre {q}.",
                    expected_output="Reconciled",
                    expected_tools=config["tools"],
                    max_steps=3
                ))

        return tasks
