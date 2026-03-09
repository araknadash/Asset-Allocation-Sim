# Asset Allocation Profiling Simulator

A Python + Streamlit web application that demonstrates **methodology validation and certification thinking** for financial asset allocation profiling. Built to mirror how production compliance systems triage investor recommendations — not just calculate them.

---

## What This Is

Most allocation tools stop at producing a number. This system goes further: it **validates**, **flags**, and **certifies** every recommendation through a multi-layer engine modelled on real Investment Policy Statement (IPS) constraints and suitability regulations (MiFID II, SEC suitability rules).

The key question this app answers isn't *"what profile is this investor?"* — it's *"should we trust this recommendation, and if not, why?"*

---

## Live Demo

```bash
streamlit run app.py
```

---

## Features

### 1. Risk Profiling Engine
- Weighted multi-factor scoring across **6 inputs**: age, time horizon, risk comfort, loss reaction, investment experience, income stability
- Goal adjustment modifier (+5 growth / -5 preservation)
- Outputs a **0–100 risk score** mapped to one of 5 profiles

| Score | Profile |
|---|---|
| 0–20 | Conservative |
| 20–40 | Moderately Conservative |
| 40–60 | Moderate |
| 60–80 | Moderately Aggressive |
| 80–100 | Aggressive |

---

### 2. Certification & Validation Layer (14 Checks)

The core of the system. Every allocation is run through 14 checks across 5 categories before it can be approved.

#### A — Mathematical Integrity
| ID | Check | Severity |
|---|---|---|
| A1 | Allocations sum to exactly 100% | Error |
| A2 | No negative allocations | Error |

#### B — IPS Policy Constraints
| ID | Check | Severity |
|---|---|---|
| B1 | Cash ≤ 20% (return drag prevention) | Warning |
| B2 | Alternatives ≤ 15% (liquidity/complexity cap) | Warning |
| B3 | No single asset class > 70% (warn) or > 90% (error) | Warning / Error |
| B4 | No "dust" positions — minimum 5% per holding | Warning |
| B5 | Cash ≥ 2% liquidity floor (obligation coverage) | Warning |
| B6 | At least 2 asset classes ≥ 5% (diversification) | Warning |

#### C — Suitability Flags
| ID | Check | Severity |
|---|---|---|
| C1 | Elderly investor (>70) with >50% equities | Warning |
| C2 | Short horizon (≤3yr) with >40% equities | Warning |
| C3 | Young investor (<25) with <20% equities + >60% bonds | Warning |

#### D — Conflict Detection
| ID | Check | Severity |
|---|---|---|
| D1 | Low risk comfort (≤2) but high loss reaction (≥4) — behavioural mismatch | Warning |
| D2 | Growth goal with ≤3 year horizon — strategic incoherence | Warning |
| D3 | Preservation goal but high risk comfort (≥4) — objective mismatch | Warning |

---

### 3. Confidence Scoring & Triage

Every recommendation receives a confidence score (0–100%) that routes it to one of three operational lanes:

| Score | Tier | Action |
|---|---|---|
| ≥ 80% | HIGH | ✅ Auto-approve |
| 60–80% | MEDIUM | ⚠️ Advisor review recommended |
| < 60% | LOW | 🔴 Human intervention required |

**Deduction logic:**
- −30% per mathematical error
- −20% per conflict (D1/D2/D3)
- −15% for large comfort/reaction gap (≥3 apart)
- −10% per suitability failure (C1/C2/C3)
- −10% for low investment experience (≤1)
- −5% per IPS policy warning

---

### 4. What-If Scenario Analyzer

Change any single input and see in real time how the recommendation changes:
- Profile and score delta
- Confidence score delta
- Side-by-side allocation bar chart
- Allocation delta chart (changes per asset class)

Useful for stress-testing a model before certifying it.

---

### 5. Batch Testing Mode

Upload a CSV of investor profiles and validate at scale:
- Runs all 14 checks per profile
- Outputs a results table with profile, score, confidence, tier, and action
- Aggregate statistics (auto-approve / advisor review / intervention counts)
- Profile distribution chart
- Downloadable results CSV

**CSV format:**
```csv
age,time_horizon,risk_comfort,loss_reaction,experience,income_stability,goal
25,40,5,5,3,4,growth
65,5,2,2,4,5,preservation
40,20,3,3,3,3,income
```

---

## Project Structure

```
asset-allocation-profiler/
├── app.py              # Streamlit web app (3 tabs: Profile, What-If, Batch)
├── models.py           # Allocation models, IPS constants, risk thresholds
├── profiler.py         # Risk scoring logic + input validation
├── validator.py        # 14-check certification engine (the core)
├── visualizations.py   # Matplotlib chart generators
├── edge_cases.py       # 4 canonical edge case scenarios + test runner
├── tests.py            # 34 automated tests (all passing)
├── main.py             # CLI entry point
└── requirements.txt    # Dependencies
```

---

## Setup

### Prerequisites
- Python 3.9+

### Install

```bash
# Clone the repo
git clone https://github.com/araknadash/Asset-Allocation-Sim.git
cd Asset-Allocation-Sim

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the CLI

```bash
# Run all 4 edge case scenarios
python main.py

# Profile a single investor
python main.py --age 35 --horizon 20 --comfort 4 --reaction 3 \
               --experience 3 --income 4 --goal growth
```

### Run the test suite

```bash
python tests.py
# Expected: 34/34 passed
```

---

## Edge Case Presets

Four built-in scenarios that stress-test the system's boundary conditions (accessible in the app sidebar):

| Preset | Setup | Expected Outcome |
|---|---|---|
| 🎰 YOLO Grandma | Age 78, 2yr horizon, all max, growth goal | Aggressive profile, LOW confidence, Human intervention |
| 😨 Terrified 18yr | Age 18, 50yr horizon, all min, preservation | Conservative inputs, opportunity-cost warning |
| 🎯 Perfect Moderate | Age 40, 25yr horizon, all mid, income | HIGH confidence, Auto-approve |
| 🤯 Contradictory | Comfort=1, Reaction=5, growth + long horizon | Conflict detected, MEDIUM confidence, Advisor review |

---

## Asset Allocation Models

| Profile | Stocks | Bonds | Cash | Alternatives |
|---|---|---|---|---|
| Conservative | 20% | 60% | 15% | 5% |
| Moderately Conservative | 35% | 45% | 12% | 8% |
| Moderate | 50% | 35% | 5% | 10% |
| Moderately Aggressive | 70% | 20% | 5% | 5% |
| Aggressive | 85% | 5% | 5% | 5% |

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.9+ | Core language |
| Streamlit | Web interface |
| Matplotlib | Charts and visualizations |
| Pandas | Batch CSV processing |
| NumPy | Numerical operations |

---

## Key Design Decisions

**Why 14 checks instead of just math?**
Mathematical correctness is necessary but not sufficient for certification. A portfolio can sum to 100% and still be completely unsuitable for an investor. The suitability and conflict layers catch what the numbers can't.

**Why confidence scoring instead of pass/fail?**
A binary pass/fail forces human review of every borderline case. A confidence score lets the system triage automatically — only genuinely risky recommendations require escalation.

**Why keep validator.py separate?**
The validation logic is the most important and most testable part of the system. Keeping it isolated means it can be unit tested exhaustively (34 tests), reused in batch mode and CLI, and extended without touching the UI.

---

## License

MIT
