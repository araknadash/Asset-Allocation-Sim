"""
validator.py - The Certification Engine

This is the most important file in the system. It moves the tool from
being a "calculator" to being a "certification layer" — the difference
between producing a number and standing behind it.

12 validation checks across 5 categories:
  A. Mathematical integrity  (2 checks)
  B. IPS policy constraints  (5 checks)
  C. Suitability flags       (3 checks)
  D. Conflict detection      (3 checks)
  E. Confidence scoring      (derived from A-D)
"""

from dataclasses import dataclass, field
from typing import Optional

from models import (
    ASSET_CLASSES,
    ALLOCATION_MODELS,
    RISK_THRESHOLDS,
    MIN_MEANINGFUL_PCT,
    LIQUIDITY_FLOOR_PCT,
    MAX_CASH_PCT,
    MAX_ALTERNATIVES_PCT,
    CONCENTRATION_WARN_PCT,
    CONCENTRATION_HARD_PCT,
    MAX_BONDS_PCT,
    MIN_DIVERSIFIED_CLASSES,
    MIN_SAFE_HAVEN_PCT,
)


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Immutable result from a single validation check."""
    check_id:    str
    category:    str          # "math" | "ips" | "suitability" | "conflict"
    severity:    str          # "error" | "warning" | "info"
    passed:      bool
    message:     str
    detail:      str = ""     # WHY this check matters
    emoji:       str = "✅"

    def __post_init__(self):
        if not self.passed:
            self.emoji = "🔴" if self.severity == "error" else "⚠️"


@dataclass
class ValidationReport:
    """Aggregated output from run_all_checks()."""
    results:          list[ValidationResult] = field(default_factory=list)
    errors:           list[ValidationResult] = field(default_factory=list)
    warnings:         list[ValidationResult] = field(default_factory=list)
    conflicts:        list[ValidationResult] = field(default_factory=list)
    confidence_score: float                  = 100.0
    confidence_tier:  str                    = "HIGH"
    action:           str                    = "Auto-approve"
    overall_pass:     bool                   = True

    def add(self, r: ValidationResult):
        self.results.append(r)
        if not r.passed:
            if r.severity == "error":
                self.errors.append(r)
            elif r.severity == "warning":
                if r.category == "conflict":
                    self.conflicts.append(r)
                else:
                    self.warnings.append(r)


# ---------------------------------------------------------------------------
# A. Mathematical checks
# ---------------------------------------------------------------------------

def check_sum_to_100(allocation: dict) -> ValidationResult:
    """
    CHECK A1: Allocations must sum to exactly 100%.
    This is the most basic mathematical requirement — any deviation means
    the portfolio is either over-invested or holding uninvested cash outside
    the model, which breaks attribution and rebalancing logic.
    """
    total = sum(allocation.values())
    passed = abs(total - 100.0) < 0.01
    return ValidationResult(
        check_id="A1",
        category="math",
        severity="error",
        passed=passed,
        message=f"Allocations sum to {total:.2f}%" if not passed else "Allocations sum to 100% ✓",
        detail="Portfolio weights must sum to exactly 100% for the model to be implementable.",
    )


def check_no_negatives(allocation: dict) -> ValidationResult:
    """
    CHECK A2: No negative allocations.
    Standard long-only portfolios cannot hold negative weights — that would
    imply short-selling, which requires separate mandate authority.
    """
    negatives = {k: v for k, v in allocation.items() if v < 0}
    passed = len(negatives) == 0
    msg = "No negative allocations ✓" if passed else f"Negative allocations found: {negatives}"
    return ValidationResult(
        check_id="A2",
        category="math",
        severity="error",
        passed=passed,
        message=msg,
        detail="Long-only mandates prohibit short positions; negative weights signal a modelling error.",
    )


# ---------------------------------------------------------------------------
# B. IPS Policy Constraints
# ---------------------------------------------------------------------------

def check_cash_limit(allocation: dict) -> ValidationResult:
    """
    CHECK B1: Cash ≤ 20%.
    Excessive cash is a drag on long-term returns (cash 'headwind'). IPS
    documents typically set a maximum cash band to ensure the manager
    stays invested. Cash above 20% is a red flag in most mandates.
    """
    cash = allocation.get("Cash", 0)
    passed = cash <= MAX_CASH_PCT
    return ValidationResult(
        check_id="B1",
        category="ips",
        severity="warning",
        passed=passed,
        message=f"Cash at {cash:.1f}% (limit {MAX_CASH_PCT}%)" if not passed else f"Cash {cash:.1f}% within limit ✓",
        detail=f"IPS constraint: Cash > {MAX_CASH_PCT}% indicates under-deployment and drag on returns.",
    )


def check_alternatives_limit(allocation: dict) -> ValidationResult:
    """
    CHECK B2: Alternatives ≤ 15%.
    Alternative assets (PE, hedge funds, real assets) are illiquid and
    complex. Regulators and best-practice IPS docs cap alternatives for
    retail and most institutional mandates to manage liquidity risk.
    """
    alts = allocation.get("Alternatives", 0)
    passed = alts <= MAX_ALTERNATIVES_PCT
    return ValidationResult(
        check_id="B2",
        category="ips",
        severity="warning",
        passed=passed,
        message=f"Alternatives at {alts:.1f}% (limit {MAX_ALTERNATIVES_PCT}%)" if not passed else f"Alternatives {alts:.1f}% within limit ✓",
        detail=f"IPS constraint: Alternatives > {MAX_ALTERNATIVES_PCT}% creates illiquidity and valuation risk.",
    )


def check_concentration(allocation: dict) -> ValidationResult:
    """
    CHECK B3: No single asset class > 70% (warn) or > 90% (error).
    Concentration risk is the primary source of portfolio blow-ups.
    A 90%+ allocation to any single class is essentially a single-asset
    bet, which violates diversification principles in any IPS.
    """
    max_class = max(allocation, key=allocation.get)
    max_pct = allocation[max_class]

    if max_pct >= CONCENTRATION_HARD_PCT:
        return ValidationResult(
            check_id="B3",
            category="ips",
            severity="error",
            passed=False,
            message=f"{max_class} at {max_pct:.1f}% — extreme concentration (>{CONCENTRATION_HARD_PCT}%)",
            detail="A >90% position in any asset class effectively eliminates diversification.",
        )
    elif max_pct >= CONCENTRATION_WARN_PCT:
        return ValidationResult(
            check_id="B3",
            category="ips",
            severity="warning",
            passed=False,
            message=f"{max_class} at {max_pct:.1f}% — high concentration (>{CONCENTRATION_WARN_PCT}%)",
            detail=f"Single-class exposure >{CONCENTRATION_WARN_PCT}% indicates insufficient diversification.",
        )
    return ValidationResult(
        check_id="B3", category="ips", severity="warning", passed=True,
        message=f"Max concentration {max_pct:.1f}% ({max_class}) — acceptable ✓",
        detail="No single asset class dominates the portfolio.",
    )


def check_minimum_position(allocation: dict) -> ValidationResult:
    """
    CHECK B4: No non-zero position below 5%.
    Positions below 5% ("dust") add complexity without meaningful return
    contribution and are often the result of rounding or modelling errors.
    They also impose disproportionate transaction costs to maintain.
    """
    dust = {k: v for k, v in allocation.items() if 0 < v < MIN_MEANINGFUL_PCT}
    passed = len(dust) == 0
    return ValidationResult(
        check_id="B4",
        category="ips",
        severity="warning",
        passed=passed,
        message=f"Dust positions found: {dust}" if not passed else "No dust positions ✓",
        detail=f"Positions 0-{MIN_MEANINGFUL_PCT}% are noise — they cost more to maintain than they contribute.",
    )


def check_liquidity_floor(allocation: dict) -> ValidationResult:
    """
    CHECK B5: Cash ≥ 2%.
    A minimum cash floor ensures the investor can meet near-term obligations
    (distributions, fees, rebalancing) without forced selling of illiquid assets.
    This is a liquidity management requirement, not a return driver.
    """
    cash = allocation.get("Cash", 0)
    passed = cash >= LIQUIDITY_FLOOR_PCT
    return ValidationResult(
        check_id="B5",
        category="ips",
        severity="warning",
        passed=passed,
        message=f"Cash {cash:.1f}% below liquidity floor ({LIQUIDITY_FLOOR_PCT}%)" if not passed else f"Liquidity floor {cash:.1f}% ≥ {LIQUIDITY_FLOOR_PCT}% ✓",
        detail=f"Minimum {LIQUIDITY_FLOOR_PCT}% cash ensures distributions and rebalancing can occur without forced sales.",
    )


def check_diversification(allocation: dict) -> ValidationResult:
    """
    CHECK B6: At least 2 asset classes with ≥ 5% allocation.
    True diversification requires meaningful exposure to multiple uncorrelated
    assets. A portfolio with only one meaningful position is not diversified
    regardless of what it's called.
    """
    meaningful = [k for k, v in allocation.items() if v >= MIN_MEANINGFUL_PCT]
    passed = len(meaningful) >= MIN_DIVERSIFIED_CLASSES
    return ValidationResult(
        check_id="B6",
        category="ips",
        severity="warning",
        passed=passed,
        message=f"Only {len(meaningful)} asset class(es) ≥5%: {meaningful}" if not passed else f"Diversified across {len(meaningful)} classes ✓",
        detail=f"At least {MIN_DIVERSIFIED_CLASSES} meaningful positions required for diversification benefit.",
    )


# ---------------------------------------------------------------------------
# C. Suitability Checks
# ---------------------------------------------------------------------------

def check_elderly_aggressive(allocation: dict, responses: dict) -> ValidationResult:
    """
    CHECK C1: Elderly (>70) + high equity → suitability flag.
    Investors over 70 have a short time horizon to recover from market losses
    and typically have reduced human capital. An aggressive equity allocation
    for this cohort is a major suitability concern under most regulatory regimes
    (MiFID II, SEC suitability rules).
    """
    age = int(responses.get("age", 0))
    stocks = allocation.get("Stocks", 0)
    flagged = age > 70 and stocks > 50

    return ValidationResult(
        check_id="C1",
        category="suitability",
        severity="warning",
        passed=not flagged,
        message=f"Elderly investor (age {age}) with {stocks:.0f}% equities — suitability concern" if flagged else "Elderly suitability check passed ✓",
        detail="Investors >70 typically cannot sustain large equity drawdowns; high equity requires explicit justification.",
    )


def check_short_horizon_equity(allocation: dict, responses: dict) -> ValidationResult:
    """
    CHECK C2: Short horizon (≤3 years) + high equity → suitability flag.
    Equity markets require at least a 5-7 year horizon to have historically
    positive expected returns with high probability. A 3-year horizon with
    high equity allocation means the investor could be forced to sell at a loss.
    """
    horizon = int(responses.get("time_horizon", 100))
    stocks  = allocation.get("Stocks", 0)
    flagged = horizon <= 3 and stocks > 40

    return ValidationResult(
        check_id="C2",
        category="suitability",
        severity="warning",
        passed=not flagged,
        message=f"Short horizon ({horizon}yr) with {stocks:.0f}% equities — sequence-of-returns risk" if flagged else "Horizon/equity suitability check passed ✓",
        detail="Short horizons (<3yr) with high equity exposure creates sequence-of-returns risk — a bad early year can be unrecoverable.",
    )


def check_young_ultra_conservative(allocation: dict, responses: dict) -> ValidationResult:
    """
    CHECK C3: Young (<25) + ultra-conservative → opportunity cost flag.
    This is the mirror suitability issue: an 18-year-old with 100% bonds
    is leaving enormous long-term compounding returns on the table. While
    not a 'harm' in the traditional sense, it represents a failure of the
    profiling system to serve the investor's best interest.
    """
    age    = int(responses.get("age", 50))
    stocks = allocation.get("Stocks", 0)
    bonds  = allocation.get("Bonds", 0)
    flagged = age < 25 and stocks < 20 and bonds > 60

    return ValidationResult(
        check_id="C3",
        category="suitability",
        severity="warning",
        passed=not flagged,
        message=f"Young investor (age {age}) with only {stocks:.0f}% equities — opportunity cost risk" if flagged else "Young investor suitability check passed ✓",
        detail="Young investors (<25) with ultra-conservative allocations forego decades of compounding; requires strong justification.",
    )


# ---------------------------------------------------------------------------
# D. Conflict Detection
# ---------------------------------------------------------------------------

def check_comfort_vs_reaction(responses: dict) -> ValidationResult:
    """
    CHECK D1: Low risk comfort but high loss reaction → behavioural mismatch.
    Risk comfort (stated preference) and loss reaction (behavioural response)
    should be correlated. A large gap suggests the investor either misunderstood
    a question or has inconsistent self-knowledge — both require advisor review.
    """
    comfort  = int(responses.get("risk_comfort", 3))
    reaction = int(responses.get("loss_reaction", 3))
    conflict = comfort <= 2 and reaction >= 4

    return ValidationResult(
        check_id="D1",
        category="conflict",
        severity="warning",
        passed=not conflict,
        message=f"Conflict: Low risk comfort ({comfort}/5) but high loss reaction ({reaction}/5)" if conflict else "Comfort/reaction alignment ✓",
        detail="Comfort vs. reaction mismatch indicates inconsistent risk self-assessment; needs advisor clarification.",
    )


def check_growth_goal_short_horizon(responses: dict) -> ValidationResult:
    """
    CHECK D2: Growth goal with ≤3 year horizon → strategic conflict.
    Growth objectives require accepting short-term volatility in exchange for
    long-term gains. A 1-3 year horizon makes this strategy incoherent —
    the investor cannot hold through the inevitable drawdowns needed to
    achieve growth returns.
    """
    goal    = responses.get("goal", "income")
    horizon = int(responses.get("time_horizon", 10))
    conflict = goal == "growth" and horizon <= 3

    return ValidationResult(
        check_id="D2",
        category="conflict",
        severity="warning",
        passed=not conflict,
        message=f"Conflict: Growth goal with only {horizon}-year horizon" if conflict else "Goal/horizon alignment ✓",
        detail="Growth strategies require 5+ year horizons to statistically recover from equity drawdowns.",
    )


def check_preservation_vs_comfort(responses: dict) -> ValidationResult:
    """
    CHECK D3: Preservation goal but high risk comfort → objective mismatch.
    If an investor states a preservation goal but has very high risk comfort,
    either they misunderstand what 'preservation' means or they've stated an
    overly conservative objective. Either way, the stated goal doesn't match
    their psychological profile — a financial advisor needs to resolve this.
    """
    goal    = responses.get("goal", "income")
    comfort = int(responses.get("risk_comfort", 3))
    conflict = goal == "preservation" and comfort >= 4

    return ValidationResult(
        check_id="D3",
        category="conflict",
        severity="warning",
        passed=not conflict,
        message=f"Conflict: Preservation goal but high risk comfort ({comfort}/5)" if conflict else "Goal/comfort alignment ✓",
        detail="Preservation goals with high risk comfort suggest the stated objective may not reflect true preferences.",
    )


# ---------------------------------------------------------------------------
# E. Confidence Scoring
# ---------------------------------------------------------------------------

def calculate_confidence(results: list[ValidationResult], responses: dict) -> tuple[float, str, str]:
    """
    Translate validation results into an actionable confidence tier.

    Deductions (from 100%):
      -20% per hard conflict (D1, D2, D3)
      -10% if experience ≤ 1 (investor may not understand what they're agreeing to)
      -15% if comfort/reaction mismatch is significant
      -10% per suitability failure (C1, C2, C3)
      -5%  per IPS warning

    Tiers:
      HIGH   (≥80%): Auto-approve — methodology is coherent
      MEDIUM (60-80%): Advisor review — red flags present but not disqualifying
      LOW    (<60%): Human intervention required — material conflicts or errors
    """
    score = 100.0

    for r in results:
        if not r.passed:
            if r.category == "conflict":
                score -= 20.0
            elif r.category == "suitability":
                score -= 10.0
            elif r.category == "ips":
                score -= 5.0
            elif r.category == "math":
                score -= 30.0  # Math errors are disqualifying

    # Extra deduction for low investment experience
    exp = int(responses.get("experience", 3))
    if exp <= 1:
        score -= 10.0

    # Behavioural mismatch deduction
    comfort  = int(responses.get("risk_comfort", 3))
    reaction = int(responses.get("loss_reaction", 3))
    if abs(comfort - reaction) >= 3:
        score -= 15.0

    score = max(0.0, min(100.0, score))

    if score >= 80:
        tier   = "HIGH"
        action = "Auto-approve"
    elif score >= 60:
        tier   = "MEDIUM"
        action = "Advisor review recommended"
    else:
        tier   = "LOW"
        action = "Human intervention required"

    return round(score, 1), tier, action


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_all_checks(allocation: dict, responses: dict, profile: str) -> ValidationReport:
    """
    Run all 12 validation checks and produce a complete ValidationReport.

    Parameters
    ----------
    allocation : dict   Asset class → weight (should sum to 100)
    responses  : dict   Raw investor questionnaire responses
    profile    : str    Assigned risk profile name

    Returns
    -------
    ValidationReport with errors, warnings, conflicts, confidence score, and action
    """
    report = ValidationReport()

    # A. Mathematical
    report.add(check_sum_to_100(allocation))
    report.add(check_no_negatives(allocation))

    # B. IPS Policy
    report.add(check_cash_limit(allocation))
    report.add(check_alternatives_limit(allocation))
    report.add(check_concentration(allocation))
    report.add(check_minimum_position(allocation))
    report.add(check_liquidity_floor(allocation))
    report.add(check_diversification(allocation))

    # C. Suitability
    report.add(check_elderly_aggressive(allocation, responses))
    report.add(check_short_horizon_equity(allocation, responses))
    report.add(check_young_ultra_conservative(allocation, responses))

    # D. Conflicts
    report.add(check_comfort_vs_reaction(responses))
    report.add(check_growth_goal_short_horizon(responses))
    report.add(check_preservation_vs_comfort(responses))

    # E. Confidence scoring
    score, tier, action = calculate_confidence(report.results, responses)
    report.confidence_score = score
    report.confidence_tier  = tier
    report.action           = action
    report.overall_pass     = len(report.errors) == 0

    return report
