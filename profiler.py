"""
profiler.py - Risk Scoring and Profile Classification

Translates investor questionnaire responses into a numeric risk score
(0-100) and a profile name. Scoring weights mirror common IPS practice:
time horizon and age together dominate because they constrain how much
volatility an investor can *afford*, while comfort/loss reaction capture
how much volatility they can *stomach*.
"""

from models import RISK_THRESHOLDS, get_allocation, get_profile_for_score, ASSET_CLASSES


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_risk_score(responses: dict) -> float:
    """
    Convert questionnaire responses to a risk score 0-100.

    Parameters
    ----------
    responses : dict with keys:
        age              int   18-80
        time_horizon     int   1-50  (years)
        risk_comfort     int   1-5   (1=very low, 5=very high)
        loss_reaction    int   1-5   (1=sell everything, 5=buy more)
        experience       int   1-5   (1=none, 5=expert)
        income_stability int   1-5   (1=unstable, 5=very stable)
        goal             str   "growth" | "income" | "preservation"
    """
    age              = int(responses["age"])
    horizon          = int(responses["time_horizon"])
    risk_comfort     = int(responses["risk_comfort"])
    loss_reaction    = int(responses["loss_reaction"])
    experience       = int(responses["experience"])
    income_stability = int(responses["income_stability"])
    goal             = str(responses.get("goal", "income")).lower()

    score = 0

    # --- Age component (0-25 pts) -------------------------------------------
    # Younger investors have more time to recover from losses.
    if age < 30:
        score += 25
    elif age < 45:
        score += 20
    elif age < 60:
        score += 10
    else:
        score += 5

    # --- Time horizon (0-25 pts) ---------------------------------------------
    # The single strongest determinant: can the portfolio survive a drawdown?
    if horizon > 20:
        score += 25
    elif horizon > 10:
        score += 20
    elif horizon > 5:
        score += 10
    else:
        score += 5

    # --- Risk comfort (0-25 pts): self-reported comfort, 5 pts per level -----
    score += risk_comfort * 5

    # --- Loss reaction (0-25 pts): behavioural resilience --------------------
    # Investors who panic-sell in downturns effectively cannot hold high equity.
    score += loss_reaction * 5

    # --- Experience (0-15 pts): sophisticated investors tolerate complexity ---
    score += experience * 3

    # --- Income stability (0-10 pts): stable income = bigger risk buffer -----
    score += income_stability * 2

    # --- Goal adjustment -----------------------------------------------------
    if goal == "growth":
        score += 5
    elif goal == "preservation":
        score -= 5

    return float(min(100, max(0, score)))


def get_investor_profile(responses: dict) -> dict:
    """
    Full profiling result: score, profile name, and target allocation.

    Returns
    -------
    dict with keys: score, profile, allocation
    """
    score   = calculate_risk_score(responses)
    profile = get_profile_for_score(score)
    alloc   = get_allocation(profile)

    return {
        "score":      score,
        "profile":    profile,
        "allocation": alloc,
    }


def validate_responses(responses: dict) -> list[str]:
    """
    Basic input validation. Returns a list of error strings (empty = OK).
    """
    errors = []
    age = responses.get("age")
    horizon = responses.get("time_horizon")

    if not (18 <= int(age) <= 80):
        errors.append("Age must be between 18 and 80.")
    if not (1 <= int(horizon) <= 50):
        errors.append("Time horizon must be between 1 and 50 years.")
    for field in ["risk_comfort", "loss_reaction", "experience", "income_stability"]:
        val = responses.get(field)
        if not (1 <= int(val) <= 5):
            errors.append(f"{field} must be between 1 and 5.")
    if responses.get("goal") not in ("growth", "income", "preservation"):
        errors.append("Goal must be one of: growth, income, preservation.")

    return errors
