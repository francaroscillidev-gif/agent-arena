from typing import Dict, Any, List

class MultiModelCostEngine:
    """
    Calcolatore di costi preciso per i principali fornitori di modelli (OpenAI, Anthropic, Google Gemini, Mistral, Llama).
    Permette di stimare esattamente il costo reale per 1k token prompt e completion.
    """

    MODEL_PRICING_PER_MILLION = {
        # Modello: (Input $/1M tok, Output $/1M tok)
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "claude-3-5-sonnet": (3.00, 15.00),
        "claude-3-haiku": (0.25, 1.25),
        "gemini-1.5-pro": (1.25, 5.00),
        "gemini-1.5-flash": (0.075, 0.30),
        "llama-3.1-70b": (0.60, 0.80),
        "default": (1.00, 3.00)
    }

    @classmethod
    def calculate_cost(cls, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        model_key = model_name.lower()
        pricing = cls.MODEL_PRICING_PER_MILLION.get("default")
        for k, v in cls.MODEL_PRICING_PER_MILLION.items():
            if k in model_key:
                pricing = v
                break

        in_price_per_m, out_price_per_m = pricing
        cost_in = (prompt_tokens / 1_000_000.0) * in_price_per_m
        cost_out = (completion_tokens / 1_000_000.0) * out_price_per_m
        return round(cost_in + cost_out, 6)

    @classmethod
    def get_supported_models(cls) -> List[str]:
        return list(cls.MODEL_PRICING_PER_MILLION.keys())
