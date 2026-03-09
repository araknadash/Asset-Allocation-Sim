"""
models.py - Asset Allocation Models and Risk Profile Definitions

Defines the five risk profiles with their target allocations,
acceptable ranges, and metadata used throughout the system.
"""

# ---------------------------------------------------------------------------
# Color palette (used by visualizations and app)
# ---------------------------------------------------------------------------
COLORS = {
    'primary': '#2E86AB',    # Blue
    'secondary': '#A23B72',  # Purple
    'accent': '#F18F01',     # Orange
    'warning': '#C73E1D',    # Red
    'success': '#5FA8D3',    # Light blue
    'highlight': '#FFBE0B',  # Yellow
    'stocks': '#2E86AB',
    'bonds': '#5FA8D3',
    'cash': '#FFBE0B',
    'alternatives': '#A23B72',
}

# ---------------------------------------------------------------------------
# Validation thresholds (IPS-based policy constants)
# ---------------------------------------------------------------------------
MIN_MEANINGFUL_PCT = 5.0        # Any position below this is "dust" — no signal
LIQUIDITY_FLOOR_PCT = 2.0       # Minimum cash — ensures investor can meet obligations
MAX_CASH_PCT = 20.0             # Holding too much cash destroys long-term returns
MAX_ALTERNATIVES_PCT = 15.0     # Alts are illiquid/complex; regulators cap them
CONCENTRATION_WARN_PCT = 70.0   # One asset >70% → undiversified, flag it
CONCENTRATION_HARD_PCT = 90.0   # One asset >90% → essentially single-asset, error
MAX_BONDS_PCT = 90              # Even conservative profiles keep some equity
MIN_DIVERSIFIED_CLASSES = 2     # At least 2 classes >5% to call it "diversified"
MIN_SAFE_HAVEN_PCT = 50.0       # Conservative profiles: bonds+cash must be ≥50%

# ---------------------------------------------------------------------------
# Risk score band → profile name
# ---------------------------------------------------------------------------
RISK_THRESHOLDS = {
    "Conservative":           (0,  20),
    "Moderately Conservative": (20, 40),
    "Moderate":               (40, 60),
    "Moderately Aggressive":  (60, 80),
    "Aggressive":             (80, 100),
}

# ---------------------------------------------------------------------------
# Five canonical allocation models
# Each entry: target allocation + acceptable min/max band per asset class
# ---------------------------------------------------------------------------
ALLOCATION_MODELS = {
    "Conservative": {
        "description": "Capital preservation focus. Suitable for short horizons or low risk tolerance.",
        "target": {
            "Stocks":       20.0,
            "Bonds":        60.0,
            "Cash":         15.0,
            "Alternatives":  5.0,
        },
        "min": {"Stocks": 10, "Bonds": 50, "Cash": 5,  "Alternatives": 0},
        "max": {"Stocks": 30, "Bonds": 75, "Cash": 20, "Alternatives": 10},
    },
    "Moderately Conservative": {
        "description": "Income focus with modest growth. Suits medium-short horizons.",
        "target": {
            "Stocks":       35.0,
            "Bonds":        45.0,
            "Cash":         12.0,
            "Alternatives":  8.0,
        },
        "min": {"Stocks": 25, "Bonds": 35, "Cash": 5,  "Alternatives": 0},
        "max": {"Stocks": 45, "Bonds": 60, "Cash": 20, "Alternatives": 15},
    },
    "Moderate": {
        "description": "Balanced growth and income. Classic 60/40 variant.",
        "target": {
            "Stocks":       50.0,
            "Bonds":        35.0,
            "Cash":         5.0,
            "Alternatives": 10.0,
        },
        "min": {"Stocks": 40, "Bonds": 25, "Cash": 2,  "Alternatives": 0},
        "max": {"Stocks": 60, "Bonds": 45, "Cash": 15, "Alternatives": 15},
    },
    "Moderately Aggressive": {
        "description": "Growth focus, some downside buffer. Long horizon investors.",
        "target": {
            "Stocks":       70.0,
            "Bonds":        20.0,
            "Cash":         5.0,
            "Alternatives":  5.0,
        },
        "min": {"Stocks": 60, "Bonds": 10, "Cash": 2,  "Alternatives": 0},
        "max": {"Stocks": 80, "Bonds": 30, "Cash": 10, "Alternatives": 15},
    },
    "Aggressive": {
        "description": "Maximum growth. Accepts high volatility; very long horizon required.",
        "target": {
            "Stocks":       85.0,
            "Bonds":         5.0,
            "Cash":          5.0,
            "Alternatives":  5.0,
        },
        "min": {"Stocks": 75, "Bonds": 0, "Cash": 2,  "Alternatives": 0},
        "max": {"Stocks": 95, "Bonds": 15, "Cash": 10, "Alternatives": 15},
    },
}

ASSET_CLASSES = ["Stocks", "Bonds", "Cash", "Alternatives"]
RISK_PROFILES = list(ALLOCATION_MODELS.keys())


def get_allocation(profile_name: str) -> dict:
    """Return the target allocation dict for a given profile name."""
    if profile_name not in ALLOCATION_MODELS:
        raise ValueError(f"Unknown profile: {profile_name}")
    return ALLOCATION_MODELS[profile_name]["target"].copy()


def get_profile_for_score(score: float) -> str:
    """Map a numeric risk score (0-100) to a profile name."""
    for profile, (low, high) in RISK_THRESHOLDS.items():
        if low <= score < high:
            return profile
    return "Aggressive"  # score == 100 edge case
