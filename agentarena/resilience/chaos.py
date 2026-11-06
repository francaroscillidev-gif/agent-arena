import random
import time
from typing import Dict, Any, Callable, Optional
from agentarena.core.models import ToolCallRecord

class ChaosFaultConfig:
    """Configurazione delle percentuali di iniezione di guasti nei tool."""
    def __init__(
        self,
        failure_rate: float = 0.0,        # es. 0.3 = 30% probabilità di errore 500 / ToolException
        latency_spike_ms: float = 0.0,    # es. 1500ms di ritardo artificiale
        malformed_output_rate: float = 0.0 # es. 0.2 = restituisce JSON o tipo inatteso
    ):
        self.failure_rate = failure_rate
        self.latency_spike_ms = latency_spike_ms
        self.malformed_output_rate = malformed_output_rate

class ChaosToolProxy:
    """
    Proxy wrapper per i tool dell'agente che inietta anomalie di rete o backend.
    Verifica se l'agente sa recuperare dagli errori (fallback, retry, self-correction).
    """
    def __init__(self, config: ChaosFaultConfig = None):
        self.config = config or ChaosFaultConfig()

    def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        actual_tool_fn: Optional[Callable[[Dict[str, Any]], Any]] = None,
        default_return: Optional[Any] = None
    ) -> ToolCallRecord:
        start = time.time()
        
        # 1. Iniezione di latenza
        if self.config.latency_spike_ms > 0:
            time.sleep(self.config.latency_spike_ms / 1000.0)

        # 2. Iniezione di errore fatale (503 / Timeout / Connection reset)
        if random.random() < self.config.failure_rate:
            dur = (time.time() - start) * 1000.0
            return ToolCallRecord(
                name=tool_name,
                arguments=tool_args,
                output=None,
                duration_ms=round(dur, 2),
                status="error",
                error=f"ChaosEngineException: Simulated 503 Service Unavailable on [{tool_name}]"
            )

        # 3. Iniezione di output malformato (test schema resilience)
        if random.random() < self.config.malformed_output_rate:
            dur = (time.time() - start) * 1000.0
            return ToolCallRecord(
                name=tool_name,
                arguments=tool_args,
                output="<<MALFORMED_OR_CORRUPTED_RESPONSE>>",
                duration_ms=round(dur, 2),
                status="success"
            )

        # 4. Esecuzione normale
        output = default_return
        if actual_tool_fn:
            try:
                output = actual_tool_fn(tool_args)
            except Exception as e:
                dur = (time.time() - start) * 1000.0
                return ToolCallRecord(
                    name=tool_name,
                    arguments=tool_args,
                    output=None,
                    duration_ms=round(dur, 2),
                    status="error",
                    error=str(e)
                )

        dur = (time.time() - start) * 1000.0
        return ToolCallRecord(
            name=tool_name,
            arguments=tool_args,
            output=output,
            duration_ms=round(dur, 2),
            status="success"
        )
