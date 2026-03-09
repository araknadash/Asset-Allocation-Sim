"""
main.py - CLI Entry Point

Provides a simple command-line interface for running edge-case tests
and profiling individual investors without launching Streamlit.

Usage:
    python main.py                    # Run all edge cases
    python main.py --age 35 ...       # Profile a single investor
"""

import argparse
import sys

from profiler import get_investor_profile, validate_responses
from validator import run_all_checks
from edge_cases import run_all_edge_cases


def profile_single(args):
    responses = {
        "age":              args.age,
        "time_horizon":     args.horizon,
        "risk_comfort":     args.comfort,
        "loss_reaction":    args.reaction,
        "experience":       args.experience,
        "income_stability": args.income,
        "goal":             args.goal,
    }

    errors = validate_responses(responses)
    if errors:
        for e in errors:
            print(f"INPUT ERROR: {e}")
        sys.exit(1)

    result = get_investor_profile(responses)
    report = run_all_checks(result["allocation"], responses, result["profile"])

    print(f"\n{'='*55}")
    print(f"  INVESTOR PROFILE RESULT")
    print(f"{'='*55}")
    print(f"  Risk Score  : {result['score']:.0f} / 100")
    print(f"  Profile     : {result['profile']}")
    print(f"\n  ALLOCATION:")
    for asset, pct in result["allocation"].items():
        bar = "█" * int(pct / 2)
        print(f"    {asset:<14} {pct:>5.1f}%  {bar}")
    print(f"\n  CONFIDENCE  : {report.confidence_score:.0f}% [{report.confidence_tier}]")
    print(f"  ACTION      : {report.action}")

    if report.errors:
        print(f"\n  🔴 ERRORS ({len(report.errors)}):")
        for r in report.errors:
            print(f"    [{r.check_id}] {r.message}")
    if report.warnings:
        print(f"\n  ⚠️  WARNINGS ({len(report.warnings)}):")
        for r in report.warnings:
            print(f"    [{r.check_id}] {r.message}")
    if report.conflicts:
        print(f"\n  ⚠️  CONFLICTS ({len(report.conflicts)}):")
        for r in report.conflicts:
            print(f"    [{r.check_id}] {r.message}")

    passed = [r for r in report.results if r.passed]
    print(f"\n  ✅ {len(passed)} checks passed, {len(report.errors)} errors, "
          f"{len(report.warnings)} warnings, {len(report.conflicts)} conflicts.")


def main():
    parser = argparse.ArgumentParser(
        description="Asset Allocation Profiling Simulator — CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                            # run all edge cases
  python main.py --age 35 --horizon 20 \\
    --comfort 4 --reaction 3 --experience 3 \\
    --income 4 --goal growth               # profile one investor
        """,
    )
    parser.add_argument("--age",        type=int,   help="Investor age (18-80)")
    parser.add_argument("--horizon",    type=int,   help="Time horizon in years (1-50)")
    parser.add_argument("--comfort",    type=int,   help="Risk comfort (1-5)")
    parser.add_argument("--reaction",   type=int,   help="Loss reaction (1-5)")
    parser.add_argument("--experience", type=int,   help="Investment experience (1-5)")
    parser.add_argument("--income",     type=int,   help="Income stability (1-5)")
    parser.add_argument("--goal",       type=str,   choices=["growth","income","preservation"],
                        help="Primary goal")

    args = parser.parse_args()

    if args.age is None:
        print("Running all edge cases...\n")
        run_all_edge_cases(verbose=True)
    else:
        required = [args.age, args.horizon, args.comfort, args.reaction, args.experience, args.income, args.goal]
        if any(v is None for v in required):
            parser.error("When profiling a single investor, all fields are required.")
        profile_single(args)


if __name__ == "__main__":
    main()
