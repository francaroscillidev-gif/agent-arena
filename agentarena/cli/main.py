#!/usr/bin/env python3
import sys
import argparse
from agentarena.core.harness import AgentHarness
from agentarena.core.storage import RunStorage
from agentarena.core.mock_agents import MockLegacyAgent, MockOptimizedAgent
from agentarena.tasks.benchmarks import get_standard_tasks
from agentarena.web.server import serve

def main():
    parser = argparse.ArgumentParser(description="AgentArena - Autonomous Agent Evaluation Harness")
    subparsers = parser.add_subparsers(dest="command")

    # benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmark suite on agent versions")
    bench_parser.add_argument("--agent", choices=["baseline", "optimized", "both"], default="both", help="Which agent to benchmark")
    bench_parser.add_argument("--chaos", action="store_true", help="Enable Chaos Engineering fault injection on tools")

    # generate synthetic tasks command
    synth_parser = subparsers.add_parser("synth", help="Generate synthetic benchmark tasks")
    synth_parser.add_argument("--domain", choices=["ecommerce", "devops", "finance"], default="ecommerce")
    synth_parser.add_argument("--count", type=int, default=5, help="Number of tasks to generate")
    synth_parser.add_argument("--out", default=None, help="Optional output JSON filepath")

    # ui command
    ui_parser = subparsers.add_parser("ui", help="Launch interactive comparison web dashboard")
    ui_parser.add_argument("--port", type=int, default=8080, help="Port to serve dashboard on")

    # summary command
    sum_parser = subparsers.add_parser("summary", help="Show CLI summary comparison")

    # diff / export report command
    diff_parser = subparsers.add_parser("diff", help="Generate Markdown diff report between two versions")
    diff_parser.add_argument("--a", required=True, help="Baseline version (e.g. v1.0.0-baseline)")
    diff_parser.add_argument("--b", required=True, help="Candidate version (e.g. v2.0.0-optimized)")
    diff_parser.add_argument("--out", default=None, help="Optional output file path (.md)")
    diff_parser.add_argument("--html", default=None, help="Export as self-contained standalone HTML report (.html)")

    # otel export command
    otel_parser = subparsers.add_parser("otel", help="Export version trajectories to OpenTelemetry OTel format")
    otel_parser.add_argument("--version", required=True, help="Agent version to export")
    otel_parser.add_argument("--out", default=None, help="Optional JSON file path to write spans to")

    # gate command for CI
    gate_parser = subparsers.add_parser("gate", help="Run CI/CD regression guard check")
    gate_parser.add_argument("--baseline", required=True, help="Baseline agent version")
    gate_parser.add_argument("--candidate", required=True, help="Candidate agent version")
    gate_parser.add_argument("--max-success-drop", type=float, default=0.0)
    gate_parser.add_argument("--max-token-increase", type=float, default=25.0)

    # leaderboard command
    subparsers.add_parser("leaderboard", help="Display global multi-agent Elo leaderboard")

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Compute statistical significance & bootstrap 95% CIs")
    stats_parser.add_argument("--a", required=True, help="Baseline agent version")
    stats_parser.add_argument("--b", required=True, help="Candidate agent version")

    # pricing / cost estimation command
    cost_parser = subparsers.add_parser("cost", help="Calculate exact API costs for a benchmark run across models")
    cost_parser.add_argument("--version", required=True, help="Agent version")
    cost_parser.add_argument("--model", default="gpt-4o-mini", help="Target model pricing (e.g. gpt-4o, claude-3-5-sonnet, gemini-1.5-flash)")

    args = parser.parse_args()

    storage = RunStorage()
    harness = AgentHarness(storage=storage)

    if args.command == "benchmark":
        tasks = get_standard_tasks()
        agents = []
        if args.agent in ["baseline", "both"]:
            agents.append(MockLegacyAgent())
        if args.agent in ["optimized", "both"]:
            agents.append(MockOptimizedAgent())

        if args.chaos:
            print("⚡ ATTIVAZIONE CHAOS ENGINEERING: Simulazione di fallimenti di rete e tool latenti abilitata!\n")

        print(f"🎯 Avvio benchmark su {len(tasks)} compiti standard...\n")
        for ag in agents:
            print(f"▶ Esecuzione benchmark per: {ag.name} ({ag.version})...")
            trajectories = harness.run_benchmark(ag, tasks)
            successes = sum(1 for t in trajectories if t.success)
            print(f"  ✓ Completati {len(trajectories)} task. Successi: {successes}/{len(trajectories)} ({int(successes/len(trajectories)*100)}%)\n")
        print("Tutte le traiettorie salvate nella directory 'runs/'.")

    elif args.command == "ui":
        print(f"Avvio AgentArena Web Interface sulla porta {args.port}...")
        serve(port=args.port)

    elif args.command == "summary":
        versions = storage.list_versions()
        print("\n=== AGENTARENA BENCHMARK SUMMARY ===")
        for v in versions:
            s = storage.get_version_summary(v)
            print(f"\n[Version: {v}]")
            print(f"  • Success Rate : {s['success_rate']}% ({s['successes']}/{s['total_tasks']})")
            print(f"  • Avg Latency  : {s['avg_duration']}s")
            print(f"  • Avg Tokens   : {s['avg_tokens']}")
            print(f"  • Avg Steps    : {s['avg_steps']}")
            print(f"  • Total Cost   : ${s['total_cost']}")

    elif args.command == "synth":
        from agentarena.synthetic.generator import SyntheticTaskGenerator
        from agentarena.tasks.loader import DatasetLoader
        tasks = SyntheticTaskGenerator.generate_suite(domain=args.domain, count=args.count)
        if args.out:
            DatasetLoader.save_to_json(tasks, args.out)
            print(f"✅ Generati con successo {len(tasks)} compiti sintetici in {args.out}")
        else:
            import json
            print(json.dumps([t.__dict__ for t in tasks], indent=2, ensure_ascii=False))

    elif args.command == "diff":
        from agentarena.evaluators.reporter import ReportExporter
        exporter = ReportExporter(storage)
        report = exporter.generate_markdown_diff(args.a, args.b)

        if args.html:
            from agentarena.reports.html_report import StandaloneHtmlReportGenerator
            html_content = StandaloneHtmlReportGenerator.generate_html_report(storage, args.a, args.b)
            with open(args.html, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"✅ Report HTML standalone salvato in {args.html}")

        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"✅ Report salvato con successo in {args.out}")
        elif not args.html:
            print("\n" + report)

    elif args.command == "otel":
        from agentarena.export.otel import OpenTelemetryOTelExporter
        runs = storage.load_runs_for_version(args.version)
        if not runs:
            print(f"Nessuna esecuzione trovata per versione {args.version}")
            return
        
        all_otel_traces = []
        for r in runs:
            # Reconstruct model
            from agentarena.core.models import TaskTrajectory, AgentStepRecord, ToolCallRecord
            traj = TaskTrajectory(
                task_id=r["task_id"],
                run_id=r["run_id"],
                agent_id=r["agent_id"],
                agent_version=r["agent_version"],
                prompt_version=r["prompt_version"],
                started_at=r["started_at"],
                ended_at=r.get("ended_at"),
                duration_seconds=r.get("duration_seconds", 0.0),
                total_tokens=r.get("total_tokens", 0),
                cost_usd=r.get("cost_usd", 0.0),
                success=r.get("success", False),
                final_output=r.get("final_output")
            )
            for s in r.get("steps", []):
                tcs = [ToolCallRecord(**tc) for tc in s.get("tool_calls", [])]
                step = AgentStepRecord(
                    step_number=s["step_number"],
                    thought=s.get("thought"),
                    tool_calls=tcs,
                    output=s.get("output"),
                    prompt_tokens=s.get("prompt_tokens", 0),
                    completion_tokens=s.get("completion_tokens", 0),
                    latency_ms=s.get("latency_ms", 0.0)
                )
                traj.steps.append(step)

            otel_dict = OpenTelemetryOTelExporter.trajectory_to_otel_spans(traj)
            all_otel_traces.append(otel_dict)

        import json
        output_data = json.dumps(all_otel_traces, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(output_data)
            print(f"✅ Esportate {len(all_otel_traces)} tracce OTel in {args.out}")
        else:
            print(output_data[:600] + f"\n... [Truncated: {len(all_otel_traces)} traces available. Use --out to save.]")

    elif args.command == "gate":
        from agentarena.ci.gate import check_regression
        passed = check_regression(
            baseline_version=args.baseline,
            candidate_version=args.candidate,
            max_success_drop=args.max_success_drop,
            max_token_increase_pct=args.max_token_increase
        )
        if not passed:
            sys.exit(1)
        else:
            sys.exit(0)

    elif args.command == "leaderboard":
        from agentarena.leaderboard.elo import EloRatingSystem
        versions = storage.list_versions()
        version_runs = {v: storage.load_runs_for_version(v) for v in versions}
        board = EloRatingSystem.compute_leaderboard(version_runs)

        print("\n" + "=" * 65)
        print("🏆 AGENTARENA GLOBAL ELO LEADERBOARD")
        print("=" * 65)
        print(f"{'Rank':<6}{'Agent Version':<25}{'Elo Rating':<14}{'Record':<14}{'Win Rate':<10}")
        print("-" * 65)
        for idx, row in enumerate(board, 1):
            print(f"#{idx:<5}{row['version']:<25}{row['elo_rating']:<14}{row['record']:<14}{row['win_rate']}%")
        print("=" * 65 + "\n")

    elif args.command == "stats":
        from agentarena.stats.significance import StatisticalSignificanceAnalyzer
        runs_a = storage.load_runs_for_version(args.a)
        runs_b = storage.load_runs_for_version(args.b)
        res = StatisticalSignificanceAnalyzer.compare_agent_versions(runs_a, runs_b)

        print("\n" + "=" * 65)
        print(f"📊 STATISTICAL SIGNIFICANCE & BOOTSTRAP 95% CI")
        print(f"Baseline: {args.a} | Candidate: {args.b}")
        print("=" * 65)
        s = res["success_rate_comparison"]
        print(f"• Success Rate Delta: {s['delta_pp']:+.1f}%")
        print(f"  - Version A Mean: {s['version_a_mean']}% (95% CI: [{s['version_a_95_ci'][0]}%, {s['version_a_95_ci'][1]}%])")
        print(f"  - Version B Mean: {s['version_b_mean']}% (95% CI: [{s['version_b_95_ci'][0]}%, {s['version_b_95_ci'][1]}%])")
        print(f"  - p-value (Permutation test): {s['p_value']} ({'Significant p < 0.05' if s['statistically_significant'] else 'Not significant'})")

        t = res["token_economy_comparison"]
        print(f"\n• Token Economy Delta: {t['delta_tokens']:+.1f} tokens")
        print(f"  - p-value: {t['p_value']}")

        print(f"\n📢 Verdict: {res['overall_assessment']['verdict']}")
        print("=" * 65 + "\n")

    elif args.command == "cost":
        from agentarena.cost.pricing import MultiModelCostEngine
        runs = storage.load_runs_for_version(args.version)
        if not runs:
            print(f"Nessuna esecuzione trovata per {args.version}")
            return
        
        tot_prompt = sum(r.get("prompt_tokens", 0) for r in runs)
        tot_comp = sum(r.get("completion_tokens", 0) for r in runs)
        total_tokens = tot_prompt + tot_comp

        models_to_compare = [args.model, "gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet", "gemini-1.5-flash"]
        unique_models = list(dict.fromkeys(models_to_compare))

        print("\n" + "=" * 65)
        print(f"💰 AGENTARENA MULTI-MODEL COST ESTIMATOR: [{args.version}]")
        print(f"Tokens: {tot_prompt} Prompt + {tot_comp} Completion = {total_tokens} Total")
        print("=" * 65)
        print(f"{'Model Provider':<25}{'Estimated Cost (USD)':<20}{'Cost per 1k Tasks':<20}")
        print("-" * 65)
        for m in unique_models:
            cost = MultiModelCostEngine.calculate_cost(m, tot_prompt, tot_comp)
            cost_per_1k = (cost / max(1, len(runs))) * 1000
            print(f"{m:<25}${cost:<19.5f}${cost_per_1k:.3f}")
        print("=" * 65 + "\n")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
