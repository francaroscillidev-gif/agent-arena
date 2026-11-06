# 🏟️ AgentArena: Agent Evaluation & Benchmarking Harness

Un framework open-source leggero, modulare e standardizzato per testare, tracciare e confrontare le prestazioni di agenti autonomi complessi su compiti reali multi-step.

---

## 💡 Il Problema
Quando si sviluppano agenti LLM (con ReAct, plan-and-solve, tool-use o architetture multi-agente), misurare l'impatto reale di una modifica al **system prompt**, al **tool definition** o ai **few-shot examples** è estremamente difficile:
- Come verificare se una prompt tweak ha risolto un task ma ha causato regressioni su altri 10?
- Quanti token in più o in meno sta consumando la nuova versione?
- L'agente sta chiamando i tool corretti o sta facendo loop ridondanti?

## 🚀 La Soluzione: AgentArena
AgentArena fornisce:
1. **Trajectory Recording Engine**: Registrazione dettagliata di ogni singolo step (pensiero/reasoning, chiamate a tool con argomenti e output, durata in ms, token consumati, esito e costo USD).
2. **Standard Benchmark Suite**: Suite di compiti complessi multi-step (finanza, customer support, DB/devops, market intelligence).
3. **Automated Evaluator**: Valutazione automatica su 4 dimensioni:
   - Tool Coverage (frequenza d'uso dei tool corretti)
   - Step Budget Efficiency (compattezza dei passaggi)
   - Output Accuracy (risultato atteso)
   - Tool Reliability (assenza di errori/eccezioni nei tool)
4. **Side-by-Side Comparison UI**: Dashboard web interattiva con grafici radar, differenze percentuali (Success rate, latency, token, cost) e visualizzazione parallela passo per passo (diff step-by-step).

---

## 🛠️ Quick Start

### 1. Eseguire un Benchmark
```bash
# Esegue la suite su entrambe le versioni demo dell'agente (baseline vs optimized)
python3 -m agentarena.cli.main benchmark --agent both
```

### 2. Ispezionare il Riepilogo da CLI
```bash
python3 -m agentarena.cli.main summary
```

### 3. Generare un Diff Report Markdown tra Versioni
```bash
python3 -m agentarena.cli.main diff --a v1.0.0-baseline --b v2.0.0-optimized
```

### 4. Esportare Tracce in formato OpenTelemetry (OTel)
```bash
python3 -m agentarena.cli.main otel --version v2.0.0-optimized --out traces.json
```

### 5. Regression Gate per CI/CD
```bash
python3 -m agentarena.cli.main gate --baseline v1.0.0-baseline --candidate v2.0.0-optimized --max-success-drop 0.0 --max-token-increase 20.0
```

### 7. Generatore di Benchmark Sintetici
Genera al volo dataset di benchmark complessi per specifici domini (ecommerce, devops, finanza):
```bash
python3 -m agentarena.cli.main synth --domain devops --count 5 --out datasets/synth_devops.json
```

### 8. Chaos Engineering & Fault Resilience Testing
Simula fallimenti intermittenti dei tool, latenze di rete e payload malformati per valutare la capacità di auto-riparazione (Self-Healing) dell'agente:
```bash
python3 -m agentarena.cli.main benchmark --agent both --chaos
```

### 9. Avviare la Dashboard Web Side-by-Side
```bash
python3 -m agentarena.cli.main ui --port 8080
```
Apri il browser su `http://localhost:8080`.

---

## 📁 Struttura del Progetto

```text
agentarena/
├── core/
│   ├── models.py         # Modelli dati: TaskTrajectory, AgentStepRecord, ToolCallRecord, BenchmarkTask
│   ├── storage.py        # Salvataggio e indicizzazione persistente delle traiettorie JSON
│   ├── harness.py        # Benchmark Runner orchestratore
│   └── mock_agents.py    # Agenti di test (v1.0.0-baseline vs v2.0.0-optimized)
├── evaluators/
│   └── evaluator.py      # Algoritmi di scoring multi-dimensionale delle traiettorie
├── tasks/
│   └── benchmarks.py     # Definizione compiti standard multi-step
├── web/
│   ├── index.html        # Web Dashboard moderna (TailwindCSS, Chart.js, Side-by-Side Diff)
│   └── server.py         # Server HTTP e REST API integrato (Zero-dependency)
└── cli/
    └── main.py           # Entrypoint CLI
```

## 🔌 Come collegare il proprio Agent
Basta implementare la classe `BaseAgent`:

```python
from agentarena.core.harness import BaseAgent
from agentarena.core.models import TaskTrajectory, AgentStepRecord, ToolCallRecord

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MyAgent", version="v1.2.0-rc", prompt_version="prompt-v4")

    def run_task(self, task):
        traj = TaskTrajectory(
            task_id=task.id,
            run_id="run_123",
            agent_id=self.name,
            agent_version=self.version,
            prompt_version=self.prompt_version
        )
        # Esegui il ciclo di reasoning del tuo agente e registra gli step:
        # traj.steps.append(AgentStepRecord(...))
        traj.finish(success=True, final_output="Risultato")
        return traj
```

---

## 👩‍💻 Autore & Maintainer

- **Autore**: Franca Roscilli
- **Email**: [francaroscillidev@gmail.com](mailto:francaroscillidev@gmail.com)
- **GitHub**: [@francaroscillidev-gif](https://github.com/francaroscillidev-gif)
- **Licenza**: MIT
