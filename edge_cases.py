"""
edge_cases.py - Canonical Test Scenarios

Defines and runs the four edge-case investor profiles from the spec.
These double as documentation: they show the range of inputs the
validation system must handle and the expected certification outcomes.
"""

from profiler import get_investor_profile, validate_responses
from validator import run_all_checks


EDGE_CASES = {
    "YOLO Grandma": {
        "desc": "Age 78, 2yr horizon, max risk comfort, growth goal. "
                "Expected: Aggressive profile flagged with elderly+short-horizon suitability warnings.",
        "responses": {
            "age": 78, "time_horizon": 2,
            "risk_comfort": 5, "loss_reaction": 5,
            "experience": 5, "income_stability": 5,
            "goal": "growth",
        },
    },
    "Terrified 18yr": {
        "desc": "Age 18, 50yr horizon, minimum risk comfort, preservation goal. "
                "Expected: Conservative profile with young+ultra-conservative opportunity-cost warning.",
        "responses": {
            "age": 18, "time_horizon": 50,
            "risk_comfort": 1, "loss_reaction": 1,
            "experience": 1, "income_stability": 1,
            "goal": "preservation",
        },
    },
    "Perfect Moderate": {
        "desc": "Age 40, 25yr horizon, all mid ratings, income goal. "
                "Expected: Moderate profile, high confidence, auto-approve.",
        "responses": {
            "age": 40, "time_horizon": 25,
            "risk_comfort": 3, "loss_reaction": 3,
            "experience": 3, "income_stability": 3,
            "goal": "income",
        },
    },
    "Contradictory": {
        "desc": "Age 30, 30yr horizon, low comfort but high loss reaction, growth goal. "
                "Expected: Conflicts detected, MEDIUM/LOW confidence, advisor review.",
        "responses": {
            "age": 30, "time_horizon": 30,
            "risk_comfort": 1, "loss_reaction": 5,
            "experience": 2, "income_stability": 3,
            "goal": "growth",
        },
    },
}


def run_all_edge_cases(verbose: bool = True) -> list[dict]:
    """Run all edge cases and return results."""
    results = []

    for name, case in EDGE_CASES.items():
        resp   = case["responses"]
        result = get_investor_profile(resp)
        report = run_all_checks(result["allocation"], resp, result["profile"])

        summary = {
            "case":       name,
            "profile":    result["profile"],
            "score":      result["score"],
            "confidence": report.confidence_score,
            "tier":       report.confidence_tier,
            "action":     report.action,
            "errors":     len(report.errors),
            "warnings":   len(report.warnings),
            "conflicts":  len(report.conflicts),
        }
        results.append(summary)

        if verbose:
            print(f"\n{'='*60}")
            print(f"CASE: {name}")
            print(f"  {case['desc']}")
            print(f"  Profile:    {result['profile']} (score {result['score']:.0f})")
            print(f"  Allocation: {result['allocation']}")
            print(f"  Confidence: {report.confidence_score:.0f}% [{report.confidence_tier}]")
            print(f"  Action:     {report.action}")
            if report.errors:
                print(f"  ERRORS ({len(report.errors)}):")
                for e in report.errors:
                    print(f"    🔴 [{e.check_id}] {e.message}")
            if report.warnings:
                print(f"  WARNINGS ({len(report.warnings)}):")
                for w in report.warnings:
                    print(f"    ⚠️  [{w.check_id}] {w.message}")
            if report.conflicts:
                print(f"  CONFLICTS ({len(report.conflicts)}):")
                for c in report.conflicts:
                    print(f"    ⚠️  [{c.check_id}] {c.message}")

    return results


if __name__ == "__main__":
    results = run_all_edge_cases(verbose=True)
    print("\n\n=== SUMMARY ===")
    print(f"{'Case':<22} {'Profile':<24} {'Score':>5} {'Confidence':>11} {'Action'}")
    print("-" * 85)
    for r in results:
        print(
            f"{r['case']:<22} {r['profile']:<24} {r['score']:>5.0f}"
            f" {r['confidence']:>10.0f}%  {r['action']}"
        )
