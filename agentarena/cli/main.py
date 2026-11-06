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

    # otel export command
    otel_parser = subparsers.add_parser("otel", help="Export version trajectories to OpenTelemetry OTel format")
    otel_parser.add_argument("--version", required=True, help="Agent version to export")
    otel_parser.add_argument("--out", default=None, help="Optional JSON file path to write spans to")

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

    elif args.command == "diff":
        from agentarena.evaluators.reporter import ReportExporter
        exporter = ReportExporter(storage)
        report = exporter.generate_markdown_diff(args.a, args.b)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"✅ Report salvato con successo in {args.out}")
        else:
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
