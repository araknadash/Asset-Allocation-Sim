"""
tests.py - Systematic validation test suite

Each test targets ONE specific check and asserts the expected outcome.
Run with:  .venv/bin/python3 tests.py
"""

from validator import run_all_checks
from profiler import get_investor_profile

PASS = "PASS"
FAIL = "FAIL"

results = []

def check(label, expected_check_id, expected_pass, allocation, responses):
    """
    Run validation and assert whether a specific check passed or failed.
    expected_pass=False means we EXPECT that check to FAIL (i.e., flag something).
    """
    result  = get_investor_profile(responses)
    report  = run_all_checks(allocation, responses, result["profile"])

    check_result = next((r for r in report.results if r.check_id == expected_check_id), None)
    if check_result is None:
        status = FAIL
        detail = f"Check {expected_check_id} not found in report"
    elif check_result.passed == expected_pass:
        status = PASS
        detail = check_result.message
    else:
        status = FAIL
        detail = f"Expected passed={expected_pass}, got passed={check_result.passed} | {check_result.message}"

    results.append((status, label, expected_check_id, detail))
    icon = "✅" if status == PASS else "❌"
    print(f"  {icon} [{expected_check_id}] {label}")
    if status == FAIL:
        print(f"       → {detail}")


# Reusable clean baseline (no flags expected)
CLEAN = {
    "age": 40, "time_horizon": 20, "risk_comfort": 3,
    "loss_reaction": 3, "experience": 3, "income_stability": 3, "goal": "income",
}
MODERATE_ALLOC = {"Stocks": 50.0, "Bonds": 35.0, "Cash": 5.0, "Alternatives": 10.0}

# ===========================================================================
# A. MATHEMATICAL CHECKS
# ===========================================================================
print("\n── A. Mathematical Checks ─────────────────────────────────────────")

# A1 — sum to 100
check("Correct sum (100%) → passes",         "A1", True,
      {"Stocks": 50, "Bonds": 35, "Cash": 5, "Alternatives": 10}, CLEAN)

check("Sum = 97% → error",                   "A1", False,
      {"Stocks": 50, "Bonds": 35, "Cash": 5, "Alternatives": 7}, CLEAN)

check("Sum = 103% → error",                  "A1", False,
      {"Stocks": 55, "Bonds": 35, "Cash": 5, "Alternatives": 8}, CLEAN)

# A2 — no negatives
check("All positive → passes",               "A2", True,
      MODERATE_ALLOC, CLEAN)

check("Negative Alternatives → error",       "A2", False,
      {"Stocks": 110, "Bonds": 0, "Cash": 0, "Alternatives": -10}, CLEAN)

# ===========================================================================
# B. IPS POLICY CONSTRAINTS
# ===========================================================================
print("\n── B. IPS Policy Constraints ──────────────────────────────────────")

# B1 — cash limit
check("Cash 5% → passes B1",                 "B1", True,
      {"Stocks": 50, "Bonds": 35, "Cash": 5, "Alternatives": 10}, CLEAN)

check("Cash 25% → warns B1",                 "B1", False,
      {"Stocks": 40, "Bonds": 25, "Cash": 25, "Alternatives": 10}, CLEAN)

# B2 — alternatives limit
check("Alts 10% → passes B2",                "B2", True,
      MODERATE_ALLOC, CLEAN)

check("Alts 20% → warns B2",                 "B2", False,
      {"Stocks": 45, "Bonds": 30, "Cash": 5, "Alternatives": 20}, CLEAN)

# B3 — concentration (warn at 70, error at 90)
check("Max class 50% → passes B3",           "B3", True,
      MODERATE_ALLOC, CLEAN)

check("Stocks 72% → warns B3",               "B3", False,
      {"Stocks": 72, "Bonds": 20, "Cash": 5, "Alternatives": 3}, CLEAN)

check("Stocks 91% → errors B3",              "B3", False,
      {"Stocks": 91, "Bonds": 5, "Cash": 2, "Alternatives": 2}, CLEAN)

# B4 — minimum position (no dust)
check("All positions ≥5% → passes B4",       "B4", True,
      MODERATE_ALLOC, CLEAN)

check("Alternatives 2% → warns B4",          "B4", False,
      {"Stocks": 60, "Bonds": 33, "Cash": 5, "Alternatives": 2}, CLEAN)

# B5 — liquidity floor
check("Cash 5% ≥ 2% → passes B5",            "B5", True,
      MODERATE_ALLOC, CLEAN)

check("Cash 1% < 2% → warns B5",             "B5", False,
      {"Stocks": 74, "Bonds": 15, "Cash": 1, "Alternatives": 10}, CLEAN)

# B6 — diversification
check("4 classes ≥5% → passes B6",           "B6", True,
      MODERATE_ALLOC, CLEAN)

check("Only 1 class ≥5% → warns B6",         "B6", False,
      {"Stocks": 95, "Bonds": 3, "Cash": 1, "Alternatives": 1}, CLEAN)

# ===========================================================================
# C. SUITABILITY CHECKS
# ===========================================================================
print("\n── C. Suitability Checks ──────────────────────────────────────────")

# C1 — elderly + aggressive
check("Age 50, 60% stocks → passes C1",      "C1", True,
      {"Stocks": 60, "Bonds": 30, "Cash": 5, "Alternatives": 5},
      {**CLEAN, "age": 50})

check("Age 75, 70% stocks → warns C1",       "C1", False,
      {"Stocks": 70, "Bonds": 20, "Cash": 5, "Alternatives": 5},
      {**CLEAN, "age": 75})

check("Age 78, 85% stocks → warns C1",       "C1", False,
      {"Stocks": 85, "Bonds": 5, "Cash": 5, "Alternatives": 5},
      {**CLEAN, "age": 78})

# C2 — short horizon + high equity
check("Horizon 15yr, 50% stocks → passes C2","C2", True,
      MODERATE_ALLOC, CLEAN)

check("Horizon 2yr, 60% stocks → warns C2",  "C2", False,
      {"Stocks": 60, "Bonds": 30, "Cash": 5, "Alternatives": 5},
      {**CLEAN, "time_horizon": 2})

# C3 — young + ultra conservative
check("Age 22, 50% stocks → passes C3",      "C3", True,
      {"Stocks": 50, "Bonds": 35, "Cash": 5, "Alternatives": 10},
      {**CLEAN, "age": 22})

check("Age 20, 10% stocks, 75% bonds → warns C3", "C3", False,
      {"Stocks": 10, "Bonds": 75, "Cash": 10, "Alternatives": 5},
      {**CLEAN, "age": 20})

# ===========================================================================
# D. CONFLICT DETECTION
# ===========================================================================
print("\n── D. Conflict Detection ──────────────────────────────────────────")

# D1 — comfort vs reaction mismatch
check("Comfort 3, reaction 3 → passes D1",   "D1", True,
      MODERATE_ALLOC, CLEAN)

check("Comfort 1, reaction 5 → conflicts D1","D1", False,
      MODERATE_ALLOC,
      {**CLEAN, "risk_comfort": 1, "loss_reaction": 5})

# D2 — growth goal + short horizon
check("Growth, 15yr horizon → passes D2",    "D2", True,
      MODERATE_ALLOC,
      {**CLEAN, "goal": "growth"})

check("Growth, 2yr horizon → conflicts D2",  "D2", False,
      MODERATE_ALLOC,
      {**CLEAN, "goal": "growth", "time_horizon": 2})

# D3 — preservation + high comfort
check("Preservation, comfort 2 → passes D3", "D3", True,
      MODERATE_ALLOC,
      {**CLEAN, "goal": "preservation", "risk_comfort": 2})

check("Preservation, comfort 5 → conflicts D3", "D3", False,
      MODERATE_ALLOC,
      {**CLEAN, "goal": "preservation", "risk_comfort": 5})

# ===========================================================================
# E. CONFIDENCE / TIER TESTS
# ===========================================================================
print("\n── E. Confidence Tier Tests ───────────────────────────────────────")

def check_tier(label, expected_tier, allocation, responses):
    result = get_investor_profile(responses)
    report = run_all_checks(allocation, responses, result["profile"])
    ok = report.confidence_tier == expected_tier
    results.append((PASS if ok else FAIL, label, "TIER", report.confidence_tier))
    icon = "✅" if ok else "❌"
    print(f"  {icon} [TIER] {label}")
    if not ok:
        print(f"       → Expected {expected_tier}, got {report.confidence_tier} ({report.confidence_score:.0f}%)")
    else:
        print(f"       → {report.confidence_tier} ({report.confidence_score:.0f}%) — {report.action}")

# Should be HIGH — no flags, clean profile
check_tier("Clean moderate investor → HIGH",
    "HIGH", MODERATE_ALLOC, CLEAN)

# Two conflicts → score drops significantly → LOW or MEDIUM
check_tier("Comfort/reaction mismatch + preservation/comfort conflict → LOW or MEDIUM",
    "LOW",
    MODERATE_ALLOC,
    {**CLEAN, "risk_comfort": 1, "loss_reaction": 5,
     "goal": "growth", "time_horizon": 2})  # D1 + D2 + behavioral mismatch

# One conflict, no suitability → MEDIUM
check_tier("Growth goal + 2yr horizon (one conflict) → MEDIUM",
    "MEDIUM",
    MODERATE_ALLOC,
    {**CLEAN, "goal": "growth", "time_horizon": 2})

# ===========================================================================
# SUMMARY
# ===========================================================================
print("\n" + "="*60)
total  = len(results)
passed = sum(1 for r in results if r[0] == PASS)
failed = total - passed
print(f"  RESULTS: {passed}/{total} passed   ({failed} failed)")
print("="*60)
if failed:
    print("\nFAILED TESTS:")
    for status, label, cid, detail in results:
        if status == FAIL:
            print(f"  ❌ [{cid}] {label}")
            print(f"     {detail}")
