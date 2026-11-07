import math
from typing import List, Dict, Any, Tuple

class EloRatingSystem:
    """
    Sistema di Elo Rating (stile LMSYS Chatbot Arena / Chess) adattato per agenti autonomi.
    Permette di stilare una Leaderboard globale multi-versione basata su matchup diretti task-per-task.
    """
    DEFAULT_RATING = 1200.0
    K_FACTOR = 32.0

    @classmethod
    def calculate_expected_score(cls, rating_a: float, rating_b: float) -> float:
        """Formula di probabilità logistica attesa Elo."""
        return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))

    @classmethod
    def update_ratings(cls, rating_a: float, rating_b: float, actual_score_a: float) -> Tuple[float, float]:
        """Aggiorna i rating Elo dopo uno scontro diretto."""
        expected_a = cls.calculate_expected_score(rating_a, rating_b)
        expected_b = 1.0 - expected_a
        actual_score_b = 1.0 - actual_score_a

        new_a = rating_a + cls.K_FACTOR * (actual_score_a - expected_a)
        new_b = rating_b + cls.K_FACTOR * (actual_score_b - expected_b)
        return round(new_a, 1), round(new_b, 1)

    @classmethod
    def compute_leaderboard(cls, version_runs_map: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Calcola la classifica Elo su tutte le versioni registrate facendo scontri a coppie su ogni task comune.
        Criteri di vittoria nel match:
        - Se uno passa e l'altro fallisce: vittoria netta (1.0 vs 0.0)
        - Se entrambi passano: vince chi ha consumato meno token / minor tempo (0.75 vs 0.25 o 0.5 per pareggio)
        - Se entrambi falliscono: pareggio (0.5 vs 0.5)
        """
        versions = list(version_runs_map.keys())
        ratings = {v: cls.DEFAULT_RATING for v in versions}
        matches_played = {v: 0 for v in versions}
        wins = {v: 0 for v in versions}
        losses = {v: 0 for v in versions}
        draws = {v: 0 for v in versions}

        # Organizza i task per ID
        task_by_version = {}
        for v, runs in version_runs_map.items():
            task_by_version[v] = {r["task_id"]: r for r in runs}

        # Esegui simulazione matchup a gironi (round-robin)
        for i in range(len(versions)):
            for j in range(i + 1, len(versions)):
                v_a = versions[i]
                v_b = versions[j]
                tasks_a = task_by_version[v_a]
                tasks_b = task_by_version[v_b]

                common_tasks = set(tasks_a.keys()).intersection(set(tasks_b.keys()))
                for tid in common_tasks:
                    ra = tasks_a[tid]
                    rb = tasks_b[tid]

                    sa = 1 if ra.get("success") else 0
                    sb = 1 if rb.get("success") else 0

                    if sa > sb:
                        score_a = 1.0
                    elif sb > sa:
                        score_a = 0.0
                    else:
                        # Pareggio sull'esito: spareggio su efficienza token
                        ta = ra.get("total_tokens", 0)
                        tb = rb.get("total_tokens", 0)
                        if ta < tb * 0.85: # A ha usato 15% in meno token
                            score_a = 0.75
                        elif tb < ta * 0.85:
                            score_a = 0.25
                        else:
                            score_a = 0.5

                    new_ra, new_rb = cls.update_ratings(ratings[v_a], ratings[v_b], score_a)
                    ratings[v_a] = new_ra
                    ratings[v_b] = new_rb

                    matches_played[v_a] += 1
                    matches_played[v_b] += 1

                    if score_a >= 0.75:
                        wins[v_a] += 1
                        losses[v_b] += 1
                    elif score_a <= 0.25:
                        wins[v_b] += 1
                        losses[v_a] += 1
                    else:
                        draws[v_a] += 1
                        draws[v_b] += 1

        leaderboard = []
        for v in versions:
            leaderboard.append({
                "version": v,
                "elo_rating": ratings[v],
                "matches": matches_played[v],
                "record": f"{wins[v]}W - {losses[v]}L - {draws[v]}D",
                "win_rate": round((wins[v] / max(1, matches_played[v])) * 100, 1)
            })

        leaderboard.sort(key=lambda x: x["elo_rating"], reverse=True)
        return leaderboard
