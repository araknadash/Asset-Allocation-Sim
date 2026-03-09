"""
visualizations.py - Matplotlib Chart Generators

All chart functions return a matplotlib Figure. Streamlit renders them
via st.pyplot(fig). Keeping charts in a separate module lets us test
them independently and reuse them in the CLI (main.py).
"""

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for Streamlit compatibility
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from models import COLORS, ASSET_CLASSES, ALLOCATION_MODELS, RISK_PROFILES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _asset_colors() -> list[str]:
    return [
        COLORS["stocks"],
        COLORS["bonds"],
        COLORS["cash"],
        COLORS["alternatives"],
    ]


def _style_fig(fig):
    fig.patch.set_facecolor("#0e1117")  # match Streamlit dark bg
    return fig


# ---------------------------------------------------------------------------
# 1. Pie chart — single allocation
# ---------------------------------------------------------------------------

def plot_allocation_pie(allocation: dict, title: str = "Asset Allocation") -> plt.Figure:
    labels  = list(allocation.keys())
    sizes   = list(allocation.values())
    colors  = _asset_colors()

    # Filter out zero slices
    filtered = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
    labels, sizes, colors = zip(*filtered) if filtered else ([], [], [])

    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.75,
        wedgeprops=dict(edgecolor="white", linewidth=1.5),
    )
    for t in texts:
        t.set_color("white")
        t.set_fontsize(10)
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")

    ax.set_title(title, color="white", fontsize=13, pad=12)
    return fig


# ---------------------------------------------------------------------------
# 2. Bar chart — side-by-side comparison (what-if)
# ---------------------------------------------------------------------------

def plot_comparison_bars(
    baseline_alloc: dict,
    scenario_alloc: dict,
    baseline_label: str = "Baseline",
    scenario_label: str = "Scenario",
) -> plt.Figure:

    x      = np.arange(len(ASSET_CLASSES))
    width  = 0.35
    b_vals = [baseline_alloc.get(a, 0) for a in ASSET_CLASSES]
    s_vals = [scenario_alloc.get(a, 0) for a in ASSET_CLASSES]

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#1a1a2e")

    bars1 = ax.bar(x - width/2, b_vals, width, label=baseline_label,
                   color=COLORS["primary"], alpha=0.85, edgecolor="white", linewidth=0.5)
    bars2 = ax.bar(x + width/2, s_vals, width, label=scenario_label,
                   color=COLORS["accent"], alpha=0.85, edgecolor="white", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(ASSET_CLASSES, color="white")
    ax.set_ylabel("Allocation (%)", color="white")
    ax.set_ylim(0, 100)
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444")
    ax.legend(facecolor="#1a1a2e", labelcolor="white")

    # Value labels
    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 1, f"{h:.0f}%",
                    ha="center", va="bottom", color="white", fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 1, f"{h:.0f}%",
                    ha="center", va="bottom", color="white", fontsize=8)

    ax.set_title("Allocation Comparison", color="white", fontsize=12)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 3. Delta bar chart — show +/- changes
# ---------------------------------------------------------------------------

def plot_allocation_delta(
    baseline_alloc: dict,
    scenario_alloc: dict,
) -> plt.Figure:
    deltas = [scenario_alloc.get(a, 0) - baseline_alloc.get(a, 0) for a in ASSET_CLASSES]
    bar_colors = [COLORS["success"] if d >= 0 else COLORS["warning"] for d in deltas]

    fig, ax = plt.subplots(figsize=(7, 3))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#1a1a2e")

    bars = ax.bar(ASSET_CLASSES, deltas, color=bar_colors, edgecolor="white", linewidth=0.5)
    ax.axhline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)

    for bar, d in zip(bars, deltas):
        va = "bottom" if d >= 0 else "top"
        offset = 0.3 if d >= 0 else -0.3
        ax.text(bar.get_x() + bar.get_width()/2, d + offset,
                f"{d:+.1f}%", ha="center", va=va, color="white", fontsize=9)

    ax.set_ylabel("Change (%)", color="white")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444")
    ax.set_title("Allocation Delta (Scenario − Baseline)", color="white", fontsize=11)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 4. Profile distribution bar chart (batch mode)
# ---------------------------------------------------------------------------

def plot_profile_distribution(profile_counts: dict) -> plt.Figure:
    profiles = RISK_PROFILES
    counts   = [profile_counts.get(p, 0) for p in profiles]
    colors   = [
        COLORS["success"],
        COLORS["primary"],
        COLORS["highlight"],
        COLORS["accent"],
        COLORS["warning"],
    ]

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#1a1a2e")

    bars = ax.bar(profiles, counts, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_ylabel("Count", color="white")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#444")
    plt.xticks(rotation=20, ha="right", color="white")

    for bar, c in zip(bars, counts):
        if c > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    str(c), ha="center", va="bottom", color="white", fontsize=10)

    ax.set_title("Profile Distribution", color="white", fontsize=12)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 5. Confidence gauge (simple horizontal bar)
# ---------------------------------------------------------------------------

def plot_confidence_gauge(score: float, tier: str) -> plt.Figure:
    color = (
        COLORS["success"]  if tier == "HIGH"   else
        COLORS["highlight"] if tier == "MEDIUM" else
        COLORS["warning"]
    )

    fig, ax = plt.subplots(figsize=(6, 1.2))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    # Background track
    ax.barh(0, 100, color="#333", height=0.5)
    # Filled bar
    ax.barh(0, score, color=color, height=0.5)

    ax.set_xlim(0, 100)
    ax.set_yticks([])
    ax.set_xlabel("Confidence Score (%)", color="white")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#333")

    ax.text(score / 2, 0, f"{score:.0f}%", ha="center", va="center",
            color="white", fontweight="bold", fontsize=11)

    fig.tight_layout()
    return fig
