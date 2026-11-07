import json
import time
from typing import Dict, Any, List
from agentarena.core.storage import RunStorage

class StandaloneHtmlReportGenerator:
    """
    Genera un report HTML interattivo autocontenuto (single-file HTML)
    che può essere inviato via email, salvato su S3/Blob o aperto offline senza server attivo.
    """

    @classmethod
    def generate_html_report(cls, storage: RunStorage, version_a: str, version_b: str) -> str:
        s_a = storage.get_version_summary(version_a)
        s_b = storage.get_version_summary(version_b)
        runs_a = storage.load_runs_for_version(version_a)
        runs_b = storage.load_runs_for_version(version_b)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AgentArena Benchmark Audit Report: {version_a} vs {version_b}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ background: #0b0f19; color: #e2e8f0; font-family: system-ui, -apple-system, sans-serif; }}
    .card {{ background: rgba(18, 24, 38, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; }}
  </style>
</head>
<body class="p-8 max-w-5xl mx-auto space-y-6">
  <div class="flex items-center justify-between border-b border-slate-800 pb-4">
    <div>
      <h1 class="text-2xl font-bold text-white flex items-center gap-2">
        <span>🏟️ AgentArena Audit Report</span>
      </h1>
      <p class="text-xs text-slate-400 mt-1">Generated: {timestamp} &bull; Author: Franca Roscilli</p>
    </div>
    <span class="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
      A/B Trajectory Diff
    </span>
  </div>

  <!-- Summary Cards -->
  <div class="grid grid-cols-4 gap-4">
    <div class="card p-4">
      <div class="text-xs text-slate-400 uppercase font-bold">Success Rate</div>
      <div class="text-xl font-bold mt-2 text-white">{s_a['success_rate']}% &rarr; <span class="text-emerald-400">{s_b['success_rate']}%</span></div>
      <div class="text-xs text-emerald-400 mt-1">Delta: +{(s_b['success_rate'] - s_a['success_rate']):.1f}%</div>
    </div>
    <div class="card p-4">
      <div class="text-xs text-slate-400 uppercase font-bold">Avg Tokens</div>
      <div class="text-xl font-bold mt-2 text-white">{s_a['avg_tokens']} &rarr; <span class="text-cyan-400">{s_b['avg_tokens']}</span></div>
      <div class="text-xs text-cyan-400 mt-1">Delta: {(s_b['avg_tokens'] - s_a['avg_tokens']):.1f} tok</div>
    </div>
    <div class="card p-4">
      <div class="text-xs text-slate-400 uppercase font-bold">Avg Latency</div>
      <div class="text-xl font-bold mt-2 text-white">{s_a['avg_duration']}s &rarr; <span class="text-purple-400">{s_b['avg_duration']}s</span></div>
      <div class="text-xs text-purple-400 mt-1">Delta: {(s_b['avg_duration'] - s_a['avg_duration']):.2f}s</div>
    </div>
    <div class="card p-4">
      <div class="text-xs text-slate-400 uppercase font-bold">Cost USD</div>
      <div class="text-xl font-bold mt-2 text-white">${s_a['total_cost']:.4f} &rarr; <span class="text-amber-400">${s_b['total_cost']:.4f}</span></div>
      <div class="text-xs text-amber-400 mt-1">Diff: ${(s_b['total_cost'] - s_a['total_cost']):.4f}</div>
    </div>
  </div>

  <!-- Task Breakdown Table -->
  <div class="card p-5">
    <h2 class="text-sm font-bold uppercase text-slate-300 mb-3">Task Breakdown Comparison</h2>
    <table class="w-full text-xs text-left">
      <thead>
        <tr class="border-b border-slate-800 text-slate-400">
          <th class="py-2">Task ID</th>
          <th class="py-2 text-center">Version A ({version_a})</th>
          <th class="py-2 text-center">Version B ({version_b})</th>
          <th class="py-2 text-right">Tokens Delta</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-800">
"""
        task_map_a = {r["task_id"]: r for r in runs_a}
        task_map_b = {r["task_id"]: r for r in runs_b}
        all_tasks = sorted(list(set(list(task_map_a.keys()) + list(task_map_b.keys()))))

        for tid in all_tasks:
            ra = task_map_a.get(tid)
            rb = task_map_b.get(tid)
            sa = ra.get("success") if ra else False
            sb = rb.get("success") if rb else False
            tok_diff = (rb.get("total_tokens", 0) if rb else 0) - (ra.get("total_tokens", 0) if ra else 0)

            badge_a = '<span class="text-emerald-400 font-bold">PASS</span>' if sa else '<span class="text-rose-400 font-bold">FAIL</span>'
            badge_b = '<span class="text-emerald-400 font-bold">PASS</span>' if sb else '<span class="text-rose-400 font-bold">FAIL</span>'

            html_template += f"""
        <tr>
          <td class="py-2.5 font-mono text-slate-200">{tid}</td>
          <td class="py-2.5 text-center">{badge_a} ({ra.get('total_tokens', 0) if ra else '-'} tok)</td>
          <td class="py-2.5 text-center">{badge_b} ({rb.get('total_tokens', 0) if rb else '-'} tok)</td>
          <td class="py-2.5 text-right font-mono {'text-emerald-400' if tok_diff <= 0 else 'text-rose-400'}">{tok_diff:+d}</td>
        </tr>
"""

        html_template += """
      </tbody>
    </table>
  </div>
  <footer class="text-center text-xs text-slate-500 pt-4 border-t border-slate-900">
    AgentArena &copy; 2026 Franca Roscilli &bull; Automated Enterprise Benchmark Report
  </footer>
</body>
</html>
"""
        return html_template
