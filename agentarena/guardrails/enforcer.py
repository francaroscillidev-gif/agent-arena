from typing import Tuple, Dict, Any, List
from agentarena.core.models import TaskTrajectory

class GuardrailsPolicyEnforcer:
    """
    Policy Enforcer in tempo reale per agenti autonomi.
    Impedisce esecuzioni pericolose:
    - Token budget cap per singola chiamata e cumulativo
    - Cost cap in USD
    - Blacklist o permessi ristretti sui comandi dei tool (es. SQL distruttivi, cancellazioni disco)
    """

    DEFAULT_MAX_TOKENS = 12000
    DEFAULT_MAX_COST_USD = 0.50
    DEFAULT_FORBIDDEN_TOOLS = ["eval", "exec", "os_system", "format_disk"]

    @classmethod
    def validate_trajectory_guardrails(
        cls,
        trajectory: TaskTrajectory,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_cost_usd: float = DEFAULT_MAX_COST_USD
    ) -> Tuple[bool, List[str]]:
        violations = []

        # 1. Token Budget Exceeded
        if trajectory.total_tokens > max_tokens:
            violations.append(f"Token budget exceeded: {trajectory.total_tokens} > limit {max_tokens}")

        # 2. Cost Cap Exceeded
        if trajectory.cost_usd > max_cost_usd:
            violations.append(f"Cost cap exceeded: ${trajectory.cost_usd:.4f} > limit ${max_cost_usd:.4f}")

        # 3. Tool Blacklist Policy
        for s in trajectory.steps:
            for tc in s.tool_calls:
                if tc.name in cls.DEFAULT_FORBIDDEN_TOOLS:
                    violations.append(f"Forbidden high-risk tool invoked: '{tc.name}'")

                # Analisi euristica su argomenti pericolosi
                arg_repr = str(tc.arguments).lower()
                if "drop database" in arg_repr or "rm -rf /" in arg_repr:
                    violations.append(f"Destructive system command blocked in tool '{tc.name}'")

        is_safe = len(violations) == 0
        return is_safe, violations
