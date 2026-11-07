import json
import os
import hashlib
from typing import Dict, Any, Callable, Optional
from agentarena.core.models import ToolCallRecord

class ToolVCRRecorder:
    """
    Registratore e Riproduttore in stile VCR/Cassette per chiamate a Tool ed API esterne.
    Permette di:
    - 'record': Esegue il tool reale la prima volta e ne salva la 'cassetta' (input hash -> output).
    - 'playback': Nelle esecuzioni successive rigioca istantaneamente la risposta senza chiamare API a pagamento,
      garantendo costo zero, esecuzione deterministica al 100% e velocità istantanea (sub-millisecondo).
    """

    def __init__(self, cassette_dir: str = "cassettes", mode: str = "playback_or_record"):
        self.cassette_dir = cassette_dir
        self.mode = mode  # 'record', 'playback', 'playback_or_record'
        os.makedirs(self.cassette_dir, exist_ok=True)

    def _hash_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        serialized = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    def execute_with_vcr(
        self,
        cassette_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        actual_fn: Optional[Callable[[Dict[str, Any]], Any]] = None,
        default_return: Optional[Any] = None
    ) -> ToolCallRecord:
        cassette_file = os.path.join(self.cassette_dir, f"{cassette_name}.json")
        call_hash = self._hash_call(tool_name, arguments)
        
        cassette_data = {}
        if os.path.exists(cassette_file):
            try:
                with open(cassette_file, "r", encoding="utf-8") as f:
                    cassette_data = json.load(f)
            except Exception:
                cassette_data = {}

        # 1. Controlla se la risposta è già registrata nella cassetta
        if self.mode in ["playback", "playback_or_record"] and call_hash in cassette_data:
            entry = cassette_data[call_hash]
            return ToolCallRecord(
                name=tool_name,
                arguments=arguments,
                output=entry.get("output"),
                duration_ms=1.0,  # istantaneo
                status="success",
                error=entry.get("error")
            )

        # 2. Altrimenti, esegui il tool reale e registra
        if actual_fn:
            try:
                out = actual_fn(arguments)
                err = None
                status = "success"
            except Exception as e:
                out = None
                err = str(e)
                status = "error"
        else:
            out = default_return
            err = None
            status = "success"

        # Salva nella cassetta
        if self.mode in ["record", "playback_or_record"]:
            cassette_data[call_hash] = {
                "tool": tool_name,
                "arguments": arguments,
                "output": out,
                "error": err
            }
            with open(cassette_file, "w", encoding="utf-8") as f:
                json.dump(cassette_data, f, indent=2, ensure_ascii=False)

        return ToolCallRecord(
            name=tool_name,
            arguments=arguments,
            output=out,
            duration_ms=45.0,
            status=status,
            error=err
        )
