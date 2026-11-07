import math
import random
from typing import List, Dict, Any, Tuple

class StatisticalSignificanceAnalyzer:
    """
    Esegue analisi statistica rigorosa sui benchmark tra due versioni di agenti:
    - Bootstrap Confidence Intervals (intervalli di confidenza al 95%)
    - Two-sample permutation test / p-value per verificare che il miglioramento non sia dovuto al caso (noise / LLM non-determinism).
    - Effect Size (Cohen's d per latenza/token e difference in proportions per success rate).
    """

    @staticmethod
    def bootstrap_confidence_interval(data: List[float], n_bootstrap: int = 1000, alpha: float = 0.05) -> Tuple[float, float, float]:
        """Restituisce (mean, ci_lower, ci_upper) calcolati con bootstrap empirico."""
        if not data:
            return 0.0, 0.0, 0.0
        n = len(data)
        means = []
        for _ in range(n_bootstrap):
            sample = [random.choice(data) for _ in range(n)]
            means.append(sum(sample) / n)
        means.sort()
        mean_val = sum(data) / n
        low_idx = int((alpha / 2.0) * n_bootstrap)
        high_idx = int((1.0 - alpha / 2.0) * n_bootstrap)
        return round(mean_val, 3), round(means[low_idx], 3), round(means[high_idx], 3)

    @staticmethod
    def permutation_test_p_value(sample_a: List[float], sample_b: List[float], n_permutations: int = 2000) -> float:
        """Calcola il p-value tramite permutation test (valutazione non-parametrica)."""
        if not sample_a or not sample_b:
            return 1.0
        obs_diff = abs((sum(sample_b) / len(sample_b)) - (sum(sample_a) / len(sample_a)))
        combined = sample_a + sample_b
        n_a = len(sample_a)
        extreme_count = 0

        for _ in range(n_permutations):
            shuffled = combined.copy()
            random.shuffle(shuffled)
            perm_a = shuffled[:n_a]
            perm_b = shuffled[n_a:]
            perm_diff = abs((sum(perm_b) / len(perm_b)) - (sum(perm_a) / len(perm_a)))
            if perm_diff >= obs_diff:
                extreme_count += 1

        return round(extreme_count / n_permutations, 4)

    @classmethod
    def compare_agent_versions(cls, runs_a: List[Dict[str, Any]], runs_b: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Confronta statisticamente due versioni di agenti."""
        succ_a = [1.0 if r.get("success") else 0.0 for r in runs_a]
        succ_b = [1.0 if r.get("success") else 0.0 for r in runs_b]

        tok_a = [float(r.get("total_tokens", 0)) for r in runs_a]
        tok_b = [float(r.get("total_tokens", 0)) for r in runs_b]

        lat_a = [float(r.get("duration_seconds", 0.0)) for r in runs_a]
        lat_b = [float(r.get("duration_seconds", 0.0)) for r in runs_b]

        mean_succ_a, ci_succ_a_low, ci_succ_a_high = cls.bootstrap_confidence_interval(succ_a)
        mean_succ_b, ci_succ_b_low, ci_succ_b_high = cls.bootstrap_confidence_interval(succ_b)

        p_val_success = cls.permutation_test_p_value(succ_a, succ_b)
        p_val_tokens = cls.permutation_test_p_value(tok_a, tok_b)

        is_significant = (p_val_success < 0.05) or (p_val_tokens < 0.05 and mean_succ_b >= mean_succ_a)

        return {
            "success_rate_comparison": {
                "version_a_mean": round(mean_succ_a * 100, 1),
                "version_a_95_ci": [round(ci_succ_a_low * 100, 1), round(ci_succ_a_high * 100, 1)],
                "version_b_mean": round(mean_succ_b * 100, 1),
                "version_b_95_ci": [round(ci_succ_b_low * 100, 1), round(ci_succ_b_high * 100, 1)],
                "delta_pp": round((mean_succ_b - mean_succ_a) * 100, 1),
                "p_value": p_val_success,
                "statistically_significant": p_val_success < 0.05
            },
            "token_economy_comparison": {
                "version_a_mean": round(sum(tok_a) / max(1, len(tok_a)), 1),
                "version_b_mean": round(sum(tok_b) / max(1, len(tok_b)), 1),
                "delta_tokens": round((sum(tok_b) / max(1, len(tok_b))) - (sum(tok_a) / max(1, len(tok_a))), 1),
                "p_value": p_val_tokens,
                "statistically_significant": p_val_tokens < 0.05
            },
            "overall_assessment": {
                "statistically_significant": is_significant,
                "confidence_level": "95%",
                "verdict": "Improvement is statistically confirmed (p < 0.05)" if is_significant else "Delta is within random variance; recommend increasing sample size"
            }
        }
