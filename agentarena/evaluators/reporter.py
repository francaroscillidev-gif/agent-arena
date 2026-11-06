import json
import csv
import io
from typing import Dict, Any, List
from agentarena.core.storage import RunStorage

class ReportExporter:
    """Esporta i confronti di benchmark in Markdown o CSV per CI/CD o review."""
    def __init__(self, storage: RunStorage):
        self.storage = storage

    def generate_markdown_diff(self, version_a: str, version_b: str) -> str:
        s_a = self.storage.get_version_summary(version_a)
        s_b = self.storage.get_version_summary(version_b)

        runs_a = {r["task_id"]: r for r in self.storage.load_runs_for_version(version_a)}
        runs_b = {r["task_id"]: r for r in self.storage.load_runs_for_version(version_b)}
        all_tasks = sorted(list(set(list(runs_a.keys()) + list(runs_b.keys()))))

        md = []
        md.append(f"# 📊 AgentArena Benchmark Diff: `{version_a}` vs `{version_b}`\n")
        
        # Summary Table
        md.append("## 📈 KPI Aggregati\n")
        md.append("| Metrica | Baseline (A) | Candidate (B) | Delta |")
        md.append("| :--- | :---: | :---: | :---: |")
        
        s_delta = s_b["success_rate"] - s_a["success_rate"]
        s_sign = "+" if s_delta > 0 else ""
        md.append(f"| **Success Rate** | {s_a['success_rate']}% | {s_b['success_rate']}% | **{s_sign}{s_delta:.1f}%** |")

        t_delta = s_b["avg_tokens"] - s_a["avg_tokens"]
        t_sign = "+" if t_delta > 0 else ""
        md.append(f"| **Avg Tokens** | {s_a['avg_tokens']} | {s_b['avg_tokens']} | {t_sign}{t_delta:.1f} |")

        d_delta = s_b["avg_duration"] - s_a["avg_duration"]
        d_sign = "+" if d_delta > 0 else ""
        md.append(f"| **Avg Latency** | {s_a['avg_duration']}s | {s_b['avg_duration']}s | {d_sign}{d_delta:.2f}s |")

        st_delta = s_b["avg_steps"] - s_a["avg_steps"]
        st_sign = "+" if st_delta > 0 else ""
        md.append(f"| **Avg Steps** | {s_a['avg_steps']} | {s_b['avg_steps']} | {st_sign}{st_delta:.2f} |")

        md.append(f"| **Total Cost** | ${s_a['total_cost']:.4f} | ${s_b['total_cost']:.4f} | ${(s_b['total_cost'] - s_a['total_cost']):.4f} |\n")

        # Task-by-task breakdown
        md.append("## 📋 Dettaglio per Task\n")
        md.append("| Task ID | Risultato (A) | Risultato (B) | Delta Tokens | Durata (A vs B) |")
        md.append("| :--- | :---: | :---: | :---: | :---: |")

        for tid in all_tasks:
            ra = runs_a.get(tid)
            rb = runs_b.get(tid)
            res_a = "✅ PASS" if ra and ra.get("success") else "❌ FAIL"
            res_b = "✅ PASS" if rb and rb.get("success") else "❌ FAIL"
            tok_a = ra.get("total_tokens", 0) if ra else 0
            tok_b = rb.get("total_tokens", 0) if rb else 0
            dt = tok_b - tok_a
            dt_str = f"+{dt}" if dt > 0 else f"{dt}"
            dur_a = f"{ra.get('duration_seconds', 0)}s" if ra else "-"
            dur_b = f"{rb.get('duration_seconds', 0)}s" if rb else "-"
            md.append(f"| `{tid}` | {res_a} | {res_b} | {dt_str} | {dur_a} vs {dur_b} |")

        return "\n".join(md)
