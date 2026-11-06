import sys
import argparse
from agentarena.core.storage import RunStorage

def check_regression(
    baseline_version: str,
    candidate_version: str,
    max_success_drop: float = 0.0,
    max_token_increase_pct: float = 25.0
) -> bool:
    storage = RunStorage()
    s_a = storage.get_version_summary(baseline_version)
    s_b = storage.get_version_summary(candidate_version)

    print("=" * 60)
    print(f"🔍 AGENTARENA CI/CD REGRESSION GUARD")
    print(f"Comparing Baseline [{baseline_version}] vs Candidate [{candidate_version}]")
    print("=" * 60)

    failed = False

    # Check 1: Success Rate Drop
    success_delta = s_b["success_rate"] - s_a["success_rate"]
    print(f"• Success Rate: {s_a['success_rate']}% -> {s_b['success_rate']}% (Delta: {success_delta:+.1f}%)")
    if success_delta < -max_success_drop:
        print(f"  ❌ REGRESSION DETECTED: Success rate dropped by {-success_delta:.1f}% (tolerated: {max_success_drop}%)")
        failed = True
    else:
        print(f"  ✅ Success Rate check passed.")

    # Check 2: Token Inflation
    tok_a = s_a["avg_tokens"] or 1.0
    tok_b = s_b["avg_tokens"] or 0.0
    tok_increase_pct = ((tok_b - tok_a) / tok_a) * 100.0
    print(f"• Avg Tokens: {s_a['avg_tokens']} -> {s_b['avg_tokens']} (Inflation: {tok_increase_pct:+.1f}%)")
    if tok_increase_pct > max_token_increase_pct:
        print(f"  ❌ TOKEN SPIKE DETECTED: Consuming {tok_increase_pct:.1f}% more tokens (max allowed: {max_token_increase_pct}%)")
        failed = True
    else:
        print(f"  ✅ Token economy check passed.")

    print("=" * 60)
    return not failed

def main():
    parser = argparse.ArgumentParser(description="AgentArena CI/CD Regression Gate")
    parser.add_argument("--baseline", required=True, help="Baseline agent version (e.g. v1.0.0-baseline)")
    parser.add_argument("--candidate", required=True, help="Candidate agent version (e.g. v2.0.0-optimized)")
    parser.add_argument("--max-success-drop", type=float, default=0.0, help="Max percentage drop in success rate before blocking CI (default 0.0)")
    parser.add_argument("--max-token-increase", type=float, default=25.0, help="Max percent increase in token consumption (default 25%)")
    args = parser.parse_args()

    passed = check_regression(
        baseline_version=args.baseline,
        candidate_version=args.candidate,
        max_success_drop=args.max_success_drop,
        max_token_increase_pct=args.max_token_increase
    )

    if not passed:
        print("🚨 BUILD FAILED: Agent performance regressed beyond threshold.\n")
        sys.exit(1)
    else:
        print("🎉 BUILD PASSED: Candidate agent meets or exceeds performance criteria.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
