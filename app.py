"""
app.py - Streamlit Web Application

Asset Allocation Profiling Simulator
  • Interactive questionnaire
  • Risk profiling & allocation
  • Validation certification layer
  • What-If scenario analyzer
  • Batch CSV testing mode
"""

import io
import streamlit as st
import pandas as pd

from models import ALLOCATION_MODELS, ASSET_CLASSES, RISK_PROFILES, COLORS
from profiler import get_investor_profile, validate_responses
from validator import run_all_checks
from visualizations import (
    plot_allocation_pie,
    plot_comparison_bars,
    plot_allocation_delta,
    plot_profile_distribution,
    plot_confidence_gauge,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Asset Allocation Profiler",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.metric-card {
    background: #1a1a2e;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.profile-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 1.1em;
}
.section-header {
    border-left: 4px solid #2E86AB;
    padding-left: 10px;
    margin-top: 20px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar – investor questionnaire
# ---------------------------------------------------------------------------
def render_sidebar() -> dict:
    st.sidebar.header("📋 Investor Questionnaire")

    age = st.sidebar.slider("Age", 18, 80, 35,
        help="Investor's current age. Younger investors can accept more risk.")
    time_horizon = st.sidebar.slider("Investment Horizon (years)", 1, 50, 15,
        help="Number of years before the funds are needed.")
    risk_comfort = st.sidebar.slider("Risk Comfort (1=Very Low, 5=Very High)", 1, 5, 3,
        help="How comfortable are you with investment risk?")
    loss_reaction = st.sidebar.slider("Loss Reaction (1=Sell All, 5=Buy More)", 1, 5, 3,
        help="How would you react to a 20% portfolio drop?")
    experience = st.sidebar.slider("Investment Experience (1=None, 5=Expert)", 1, 5, 2,
        help="Years / depth of investment experience.")
    income_stability = st.sidebar.slider("Income Stability (1=Unstable, 5=Very Stable)", 1, 5, 4,
        help="How stable and reliable is your income?")
    goal = st.sidebar.selectbox(
        "Primary Goal",
        ["income", "growth", "preservation"],
        index=0,
        help="What is the main objective of this portfolio?",
    )

    return {
        "age":              age,
        "time_horizon":     time_horizon,
        "risk_comfort":     risk_comfort,
        "loss_reaction":    loss_reaction,
        "experience":       experience,
        "income_stability": income_stability,
        "goal":             goal,
    }


# ---------------------------------------------------------------------------
# Edge-case presets
# ---------------------------------------------------------------------------
PRESETS = {
    "— Select preset —":    None,
    "🎰 YOLO Grandma":       {"age": 78, "time_horizon": 2,  "risk_comfort": 5, "loss_reaction": 5, "experience": 5, "income_stability": 5, "goal": "growth"},
    "😨 Terrified 18yr":    {"age": 18, "time_horizon": 50, "risk_comfort": 1, "loss_reaction": 1, "experience": 1, "income_stability": 1, "goal": "preservation"},
    "🎯 Perfect Moderate":  {"age": 40, "time_horizon": 25, "risk_comfort": 3, "loss_reaction": 3, "experience": 3, "income_stability": 3, "goal": "income"},
    "🤯 Contradictory":     {"age": 30, "time_horizon": 30, "risk_comfort": 1, "loss_reaction": 5, "experience": 2, "income_stability": 3, "goal": "growth"},
}


# ---------------------------------------------------------------------------
# Confidence tier badges
# ---------------------------------------------------------------------------
TIER_COLORS = {"HIGH": "#5FA8D3", "MEDIUM": "#FFBE0B", "LOW": "#C73E1D"}
ACTION_ICONS = {"HIGH": "✅", "MEDIUM": "⚠️", "LOW": "🔴"}


def confidence_badge(tier: str, score: float) -> str:
    color = TIER_COLORS.get(tier, "#888")
    return (
        f'<span class="profile-badge" style="background:{color};color:white;">'
        f'{tier} — {score:.0f}%</span>'
    )


# ---------------------------------------------------------------------------
# Result display helpers
# ---------------------------------------------------------------------------
def render_allocation_bars(allocation: dict):
    for asset in ASSET_CLASSES:
        pct = allocation.get(asset, 0)
        st.progress(int(pct), text=f"**{asset}**: {pct:.1f}%")


def render_validation_results(report):
    if report.errors:
        st.error(f"**{len(report.errors)} Error(s) found — allocation cannot be certified**")
        for r in report.errors:
            st.error(f"{r.emoji} [{r.check_id}] {r.message}")
            st.caption(f"   ↳ *{r.detail}*")

    if report.warnings:
        st.warning(f"**{len(report.warnings)} Warning(s)**")
        for r in report.warnings:
            st.warning(f"{r.emoji} [{r.check_id}] {r.message}")
            st.caption(f"   ↳ *{r.detail}*")

    if report.conflicts:
        st.error(f"**{len(report.conflicts)} Conflict(s) detected**")
        for r in report.conflicts:
            st.error(f"{r.emoji} [{r.check_id}] {r.message}")
            st.caption(f"   ↳ *{r.detail}*")

    passed_checks = [r for r in report.results if r.passed]
    if passed_checks:
        with st.expander(f"✅ {len(passed_checks)} checks passed", expanded=False):
            for r in passed_checks:
                st.success(f"✅ [{r.check_id}] {r.message}")


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
def tab_profile(responses: dict):
    st.markdown('<h2 class="section-header">Risk Profile & Allocation</h2>', unsafe_allow_html=True)

    errors = validate_responses(responses)
    if errors:
        for e in errors:
            st.error(e)
        return

    result = get_investor_profile(responses)
    report = run_all_checks(result["allocation"], responses, result["profile"])

    # Store baseline in session state
    if "baseline" not in st.session_state:
        st.session_state.baseline = {"result": result, "responses": responses, "report": report}

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Risk Score", f"{result['score']:.0f} / 100")
    with col2:
        st.metric("Profile", result["profile"])
    with col3:
        st.metric("Confidence", f"{report.confidence_score:.0f}%")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("#### Allocation Breakdown")
        render_allocation_bars(result["allocation"])

        st.markdown("#### Confidence Tier")
        st.markdown(confidence_badge(report.confidence_tier, report.confidence_score),
                    unsafe_allow_html=True)
        st.markdown(
            f"**{ACTION_ICONS.get(report.confidence_tier, '')} Action:** {report.action}",
        )
        st.pyplot(plot_confidence_gauge(report.confidence_score, report.confidence_tier))

    with col_right:
        st.pyplot(plot_allocation_pie(result["allocation"], f"{result['profile']} Allocation"))

    st.markdown("---")
    st.markdown("### 🔍 Validation Report")
    render_validation_results(report)

    # Save baseline button
    if st.button("💾 Save as Baseline (for What-If)"):
        st.session_state.baseline = {"result": result, "responses": responses, "report": report}
        st.success("Baseline saved! Go to the What-If tab to explore scenarios.")


def tab_whatif(responses: dict):
    st.markdown('<h2 class="section-header">What-If Scenario Analyzer</h2>', unsafe_allow_html=True)

    if "baseline" not in st.session_state:
        st.info("Run the Risk Profile tab first and click 'Save as Baseline'.")
        return

    baseline = st.session_state.baseline
    base_result = baseline["result"]

    st.markdown("#### Baseline")
    b1, b2, b3 = st.columns(3)
    b1.metric("Profile", base_result["profile"])
    b2.metric("Score",   f"{base_result['score']:.0f}")
    b3.metric("Confidence", f"{baseline['report'].confidence_score:.0f}%")

    st.markdown("---")
    st.markdown("#### Adjust one input to see impact")

    scenario_field = st.selectbox(
        "Field to change",
        ["age", "time_horizon", "risk_comfort", "loss_reaction", "experience", "income_stability", "goal"],
    )

    if scenario_field == "goal":
        new_val = st.selectbox("New value", ["income", "growth", "preservation"])
    else:
        cur = baseline["responses"][scenario_field]
        if scenario_field == "age":
            new_val = st.slider("New value", 18, 80, int(cur))
        elif scenario_field == "time_horizon":
            new_val = st.slider("New value", 1, 50, int(cur))
        else:
            new_val = st.slider("New value", 1, 5, int(cur))

    scenario_responses = {**baseline["responses"], scenario_field: new_val}
    scen_result = get_investor_profile(scenario_responses)
    scen_report = run_all_checks(scen_result["allocation"], scenario_responses, scen_result["profile"])

    s1, s2, s3 = st.columns(3)
    delta_score = scen_result["score"] - base_result["score"]
    s1.metric("Profile", scen_result["profile"],
              delta=None if scen_result["profile"] == base_result["profile"] else "changed")
    s2.metric("Score",   f"{scen_result['score']:.0f}", delta=f"{delta_score:+.0f}")
    s3.metric("Confidence", f"{scen_report.confidence_score:.0f}%",
              delta=f"{scen_report.confidence_score - baseline['report'].confidence_score:+.0f}%")

    col_left, col_right = st.columns(2)
    with col_left:
        st.pyplot(plot_comparison_bars(
            base_result["allocation"], scen_result["allocation"],
            "Baseline", "Scenario"
        ))
    with col_right:
        st.pyplot(plot_allocation_delta(base_result["allocation"], scen_result["allocation"]))

    with st.expander("Scenario validation details"):
        render_validation_results(scen_report)


def tab_batch():
    st.markdown('<h2 class="section-header">Batch Testing Mode</h2>', unsafe_allow_html=True)
    st.markdown("Upload a CSV of investor profiles to validate at scale.")
    st.code(
        "age,time_horizon,risk_comfort,loss_reaction,experience,income_stability,goal\n"
        "25,40,5,5,3,4,growth\n"
        "65,5,2,2,4,5,preservation\n"
        "40,20,3,3,3,3,income",
        language="csv",
    )

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is None:
        st.info("Upload a CSV to get started.")
        return

    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Could not parse CSV: {e}")
        return

    required = ["age", "time_horizon", "risk_comfort", "loss_reaction", "experience", "income_stability", "goal"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing columns: {missing}")
        return

    st.success(f"Loaded {len(df)} profiles.")

    results_rows = []
    for _, row in df.iterrows():
        resp = row.to_dict()
        errs = validate_responses(resp)
        if errs:
            results_rows.append({
                "age": resp["age"], "goal": resp["goal"],
                "profile": "INVALID", "score": None,
                "confidence": None, "tier": "ERROR",
                "action": "; ".join(errs),
                "errors": len(errs), "warnings": 0, "conflicts": 0,
            })
            continue

        r      = get_investor_profile(resp)
        report = run_all_checks(r["allocation"], resp, r["profile"])
        results_rows.append({
            "age":        resp["age"],
            "goal":       resp["goal"],
            "profile":    r["profile"],
            "score":      r["score"],
            "confidence": report.confidence_score,
            "tier":       report.confidence_tier,
            "action":     report.action,
            "errors":     len(report.errors),
            "warnings":   len(report.warnings),
            "conflicts":  len(report.conflicts),
        })

    results_df = pd.DataFrame(results_rows)
    st.dataframe(results_df, use_container_width=True)

    # Aggregate stats
    st.markdown("### Aggregate Statistics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Profiles", len(results_df))
    c2.metric("Auto-approve", (results_df["tier"] == "HIGH").sum())
    c3.metric("Advisor Review", (results_df["tier"] == "MEDIUM").sum())
    c4.metric("Human Required", (results_df["tier"] == "LOW").sum())

    profile_counts = results_df["profile"].value_counts().to_dict()
    st.pyplot(plot_profile_distribution(profile_counts))

    # Download
    csv_out = results_df.to_csv(index=False).encode()
    st.download_button("⬇ Download Results CSV", csv_out, "validation_results.csv", "text/csv")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main():
    st.title("📊 Asset Allocation Profiling Simulator")
    st.caption("Methodology validation and certification layer for financial risk profiling.")

    # Preset selector in sidebar
    preset_name = st.sidebar.selectbox("Load preset scenario", list(PRESETS.keys()))
    responses = render_sidebar()
    if PRESETS.get(preset_name):
        responses = PRESETS[preset_name]
        st.sidebar.info(f"Preset loaded: {preset_name}")

    tab1, tab2, tab3 = st.tabs(["🎯 Risk Profile", "🔄 What-If Analyzer", "📁 Batch Testing"])

    with tab1:
        tab_profile(responses)
    with tab2:
        tab_whatif(responses)
    with tab3:
        tab_batch()


if __name__ == "__main__":
    main()
