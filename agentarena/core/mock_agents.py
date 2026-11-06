import uuid
import time
from agentarena.core.models import TaskTrajectory, AgentStepRecord, ToolCallRecord, BenchmarkTask
from agentarena.core.harness import BaseAgent

class MockLegacyAgent(BaseAgent):
    """v1.0.0: Baseline agent with older naive prompt, tendency to make redundant steps & occasional tool fail."""
    def __init__(self):
        super().__init__(name="CustomerOpsAgent", version="v1.0.0-baseline", prompt_version="prompt-v1-generic")

    def run_task(self, task: BenchmarkTask) -> TaskTrajectory:
        traj = TaskTrajectory(
            task_id=task.id,
            run_id=str(uuid.uuid4())[:8],
            agent_id=self.name,
            agent_version=self.version,
            prompt_version=self.prompt_version,
            started_at=time.time()
        )

        if task.id == "task_calc_finance":
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Provo a cercare nei documenti generici aziendali invece del db.",
                tool_calls=[ToolCallRecord(name="doc_search", arguments={"query": "revenue"}, output="Non trovato.", duration_ms=450)],
                prompt_tokens=420, completion_tokens=45, latency_ms=620
            ))
            traj.steps.append(AgentStepRecord(
                step_number=2,
                thought="Controllo il DB finanziario per i valori.",
                tool_calls=[ToolCallRecord(name="financial_db", arguments={"quarter": ["Q1", "Q2"]}, output={"Q1": 120000, "Q2": 156000}, duration_ms=210)],
                prompt_tokens=520, completion_tokens=35, latency_ms=410
            ))
            traj.steps.append(AgentStepRecord(
                step_number=3,
                thought="Calcolo a mente: (156k - 120k)/120k.",
                output="La crescita registrata tra Q1 e Q2 è circa del 25%",
                prompt_tokens=600, completion_tokens=60, latency_ms=380
            ))
            time.sleep(0.05)
            traj.cost_usd = 0.0084
            traj.finish(success=False, final_output="La crescita registrata tra Q1 e Q2 è circa del 25%")

        elif task.id == "task_support_refund":
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Verifico stato ordine.",
                tool_calls=[ToolCallRecord(name="lookup_order", arguments={"id": "ORD-9821"}, output={"status": "delivered", "amount": 45, "date": "2026-10-15"}, duration_ms=180)],
                prompt_tokens=310, completion_tokens=30, latency_ms=320
            ))
            traj.steps.append(AgentStepRecord(
                step_number=2,
                thought="Eseguo procedura di rimborso.",
                tool_calls=[ToolCallRecord(name="process_refund", arguments={"order_id": "ORD-9821", "amount": 45}, output={"status": "ok"}, duration_ms=510)],
                prompt_tokens=450, completion_tokens=40, latency_ms=600
            ))
            traj.cost_usd = 0.0062
            time.sleep(0.04)
            traj.finish(success=True, final_output="Rimborso completato con successo per ORD-9821 (Refund successful).")

        elif task.id == "task_sql_bug_investigation":
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Leggo i log generici.",
                tool_calls=[ToolCallRecord(name="sql_executor", arguments={"sql": "SELECT COUNT(*) FROM events"}, output={"count": 5000000}, duration_ms=1200)],
                prompt_tokens=680, completion_tokens=90, latency_ms=1400
            ))
            traj.cost_usd = 0.0095
            time.sleep(0.06)
            traj.finish(success=False, final_output="La tabella ha 5M righe. Suggerisco di ridurre i dati.")

        elif task.id == "task_security_auth_audit":
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Controllo solo i log di autenticazione generali.",
                tool_calls=[ToolCallRecord(name="audit_logger", arguments={"user": "user_8829"}, output={"recent_logins": 5}, duration_ms=250)],
                prompt_tokens=400, completion_tokens=30, latency_ms=300
            ))
            traj.cost_usd = 0.0051
            time.sleep(0.03)
            traj.finish(success=False, final_output="Non ho trovato token scaduti nei log generali.")

        else: # task_multi_source_summary
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Cerco prezzi competitor.",
                tool_calls=[ToolCallRecord(name="web_search", arguments={"query": "Competitor pricing"}, output="Trovate pagine pricing", duration_ms=800)],
                prompt_tokens=500, completion_tokens=50, latency_ms=900
            ))
            traj.steps.append(AgentStepRecord(
                step_number=2,
                thought="Estraggo i prezzi.",
                tool_calls=[ToolCallRecord(name="html_parser", arguments={"url": "competitor.com"}, output="Competitor X: $29/mo, Competitor Y: $35/mo", duration_ms=450)],
                prompt_tokens=750, completion_tokens=65, latency_ms=750
            ))
            traj.cost_usd = 0.0078
            time.sleep(0.05)
            traj.finish(success=True, final_output="Ecco i dettagli: Competitor X: $29/mo, Competitor Y: $35/mo.")

        return traj


class MockOptimizedAgent(BaseAgent):
    """v2.0.0: Upgraded agent with structured tool planning prompt and strict validation."""
    def __init__(self):
        super().__init__(name="CustomerOpsAgent", version="v2.0.0-optimized", prompt_version="prompt-v2-chain-of-tools")

    def run_task(self, task: BenchmarkTask) -> TaskTrajectory:
        traj = TaskTrajectory(
            task_id=task.id,
            run_id=str(uuid.uuid4())[:8],
            agent_id=self.name,
            agent_version=self.version,
            prompt_version=self.prompt_version,
            started_at=time.time()
        )

        if task.id == "task_calc_finance":
            # Direct target tools
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Estraggo i dati esatti con il tool financial_db e passo a calculator.",
                tool_calls=[
                    ToolCallRecord(name="financial_db", arguments={"quarter": ["Q1", "Q2"]}, output={"Q1": 120000, "Q2": 156000}, duration_ms=150),
                    ToolCallRecord(name="calculator", arguments={"expr": "((156000 - 120000) / 120000) * 100"}, output="30.0", duration_ms=10)
                ],
                prompt_tokens=280, completion_tokens=60, latency_ms=310
            ))
            traj.steps.append(AgentStepRecord(
                step_number=2,
                thought="Formula confermata: incremento del 30%.",
                output="La percentuale di crescita del fatturato tra Q1 e Q2 è esattamente del 30%.",
                prompt_tokens=360, completion_tokens=35, latency_ms=210
            ))
            traj.cost_usd = 0.0038
            traj.finish(success=True, final_output="La percentuale di crescita del fatturato tra Q1 e Q2 è esattamente del 30%.")

        elif task.id == "task_support_refund":
            # Clean chain of lookup -> refund -> notification
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Controllo eleggibilità ordine ORD-9821.",
                tool_calls=[ToolCallRecord(name="lookup_order", arguments={"id": "ORD-9821"}, output={"eligible": True, "amount": 45}, duration_ms=120)],
                prompt_tokens=240, completion_tokens=25, latency_ms=250
            ))
            traj.steps.append(AgentStepRecord(
                step_number=2,
                thought="Eseguo rimborso e notifica cliente in parallelo.",
                tool_calls=[
                    ToolCallRecord(name="process_refund", arguments={"order_id": "ORD-9821", "amount": 45}, output={"status": "ok", "refund_id": "RF-11"}, duration_ms=320),
                    ToolCallRecord(name="send_notification", arguments={"to": "user@example.com", "msg": "Refund processed"}, output="sent", duration_ms=150)
                ],
                prompt_tokens=380, completion_tokens=40, latency_ms=450
            ))
            traj.cost_usd = 0.0041
            time.sleep(0.03)
            traj.finish(success=True, final_output="Procedura completata. Refund successful. Notifica inviata via email.")

        elif task.id == "task_sql_bug_investigation":
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Eseguo EXPLAIN per analizzare il piano di esecuzione.",
                tool_calls=[ToolCallRecord(name="explain_query", arguments={"query": "SELECT * FROM events WHERE user_id = 42"}, output={"plan": "Seq Scan on events (cost=0.00..125000.00)"}, duration_ms=300)],
                prompt_tokens=410, completion_tokens=45, latency_ms=390
            ))
            traj.steps.append(AgentStepRecord(
                step_number=2,
                thought="Rilevata scansione sequenziale su tabella grande. Ispeziono indici correnti.",
                tool_calls=[
                    ToolCallRecord(name="schema_inspector", arguments={"table": "events"}, output={"indexes": ["PRIMARY KEY id"]}, duration_ms=110),
                    ToolCallRecord(name="sql_executor", arguments={"sql": "CREATE INDEX idx_events_user_id ON events(user_id);"}, output="Index created successfully", duration_ms=420)
                ],
                prompt_tokens=520, completion_tokens=70, latency_ms=580
            ))
            traj.cost_usd = 0.0059
            time.sleep(0.04)
            traj.finish(success=True, final_output="Causa individuata: Sequential Scan per assenza di indice. Eseguito: CREATE INDEX idx_events_user_id ON events(user_id); Tempo query ridotto a 1.2ms.")

        elif task.id == "task_security_auth_audit":
            # Optimized succeeds: inspects tokens & pushes revocation to redis blacklist
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Scansiono i token JWT di user_8829 per scadenze e anomalie.",
                tool_calls=[ToolCallRecord(name="token_inspector", arguments={"user": "user_8829"}, output={"expired": ["tok_91a", "tok_44b"], "valid": ["tok_99z"]}, duration_ms=180)],
                prompt_tokens=320, completion_tokens=35, latency_ms=220
            ))
            traj.steps.append(AgentStepRecord(
                step_number=2,
                thought="Aggiungo i 2 token scaduti alla blacklist Redis e registro audit log.",
                tool_calls=[
                    ToolCallRecord(name="redis_blacklist", arguments={"tokens": ["tok_91a", "tok_44b"]}, output={"blacklisted": 2}, duration_ms=80),
                    ToolCallRecord(name="audit_logger", arguments={"action": "revoke_tokens", "count": 2}, output={"status": "logged"}, duration_ms=120)
                ],
                prompt_tokens=410, completion_tokens=40, latency_ms=310
            ))
            traj.cost_usd = 0.0039
            time.sleep(0.03)
            traj.finish(success=True, final_output="Audit completato. Revoked 2 tokens con successo e registrato nei log di sicurezza.")

        else: # task_multi_source_summary
            traj.steps.append(AgentStepRecord(
                step_number=1,
                thought="Cerco e parso con precisione i prezzi dei competitor.",
                tool_calls=[
                    ToolCallRecord(name="web_search", arguments={"query": "Competitor X Y Pro plan pricing"}, output="Pricing URLs found", duration_ms=400),
                    ToolCallRecord(name="html_parser", arguments={"url": "competitor.com"}, output="Competitor X: $29/mo, Competitor Y: $35/mo", duration_ms=310),
                    ToolCallRecord(name="summarizer", arguments={"text": "Competitor X: $29/mo, Competitor Y: $35/mo"}, output="Summary verified", duration_ms=180)
                ],
                prompt_tokens=460, completion_tokens=50, latency_ms=620
            ))
            traj.cost_usd = 0.0045
            time.sleep(0.03)
            traj.finish(success=True, final_output="Rapporto prezzi sintetizzato: Competitor X: $29/mo, Competitor Y: $35/mo.")

        return traj
