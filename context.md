# Asset Allocation Profiling Simulator - Project Context

## Project Overview
Build a Python Streamlit web application that demonstrates methodology validation and certification thinking for financial asset allocation profiling.

## Tech Stack
- Python 3.9+
- Streamlit (web interface)
- Matplotlib (visualizations)
- Pandas (data manipulation)

## Project Structure
```
asset-allocation-profiler/
├── requirements.txt
├── README.md
├── models.py              # Allocation models and risk thresholds
├── profiler.py           # Risk scoring logic
├── validator.py          # Validation layer (THE KEY PIECE)
├── visualizations.py     # Charts and graphs
├── edge_cases.py         # Edge case testing
├── main.py              # CLI entry point
└── app.py               # Streamlit web app
```

## Core Functionality

### 1. Risk Profiling (profiler.py)
- Collect investor inputs: age, time_horizon, risk_comfort, loss_reaction, experience, income_stability, goal
- Calculate risk score (0-100) based on weighted inputs
- Classify into risk profiles: Conservative, Moderately Conservative, Moderate, Moderately Aggressive, Aggressive

### 2. Asset Allocation Models (models.py)
Define 5 risk profile models with allocations across: Stocks, Bonds, Cash, Alternatives

Example:
- Conservative: 20% Stocks, 60% Bonds, 15% Cash, 5% Alternatives
- Aggressive: 85% Stocks, 5% Bonds, 5% Cash, 5% Alternatives

### 3. Validation Layer (validator.py) - THIS IS THE MOST IMPORTANT
Implements 12 different validation checks:

**Mathematical Checks:**
- Sum to 100%
- No negative values

**Policy Constraints (IPS-based):**
- Cash: 0-20% typical maximum
- Alternatives: 0-15% typical maximum
- Concentration warnings: >70% in single asset
- Minimum position size: 5% (avoid "dust")
- Liquidity floor: minimum 2% cash
- Minimum diversification: at least 2 asset classes >5%

**Suitability Checks:**
- Elderly (>70) + aggressive allocation → flag
- Short horizon (≤3 years) + high equity → flag
- Young (<25) + ultra conservative → flag

**Conflict Detection:**
- Low risk comfort but aggressive loss reaction
- Growth goal with <3 year horizon
- Preservation goal but high risk comfort

**Confidence Scoring:**
- Start at 100%
- Deduct 20% per conflict
- Deduct 10% for low experience
- Deduct 15% for behavioral mismatch
- Output: HIGH (80%+), MEDIUM (60-80%), LOW (<60%)
- Action: Auto-approve, Advisor review, or Human intervention

### 4. Streamlit App Features (app.py)

**Core Features:**
1. Interactive questionnaire (sidebar sliders)
2. Risk profile calculation
3. Asset allocation display (progress bars + pie chart)
4. Validation results with warnings
5. Confidence scoring
6. Suitability flags

**Advanced Features:**
1. **What-If Scenario Analyzer**: 
   - Change one input, see impact on score/profile/allocation
   - Side-by-side comparison with baseline
   - Allocation delta visualization

2. **Batch Testing Mode**:
   - Upload CSV of investor profiles
   - Validate at scale
   - Aggregate statistics
   - Profile distribution chart

3. **Session State Management**:
   - Preserve baseline calculation
   - Enable scenario comparisons

## Key Constants (Use These)
```python
# Validation thresholds
MIN_MEANINGFUL_PCT = 5.0   # Minimum position size
LIQUIDITY_FLOOR_PCT = 2.0  # Minimum cash
MAX_BONDS_PCT = 90
CONCENTRATION_WARN_PCT = 70
CONCENTRATION_HARD_PCT = 90
MIN_DIVERSIFIED_CLASSES = 2
MIN_SAFE_HAVEN_PCT = 50    # For conservative profiles

# Risk score thresholds
RISK_THRESHOLDS = {
    "Conservative": (0, 20),
    "Moderately Conservative": (20, 40),
    "Moderate": (40, 60),
    "Moderately Aggressive": (60, 80),
    "Aggressive": (80, 100)
}
```

## Scoring Logic (profiler.py)
```python
def calculate_risk_score(responses):
    score = 0
    
    # Age (0-25 points)
    if age < 30: score += 25
    elif age < 45: score += 20
    elif age < 60: score += 10
    else: score += 5
    
    # Time horizon (0-25 points)
    if horizon > 20: score += 25
    elif horizon > 10: score += 20
    elif horizon > 5: score += 10
    else: score += 5
    
    # Risk comfort (0-25 points): rating * 5
    score += risk_comfort * 5
    
    # Loss reaction (0-25 points): rating * 5
    score += loss_reaction * 5
    
    # Experience (0-15 points): rating * 3
    score += experience * 3
    
    # Income stability (0-10 points): rating * 2
    score += income_stability * 2
    
    # Goal adjustment (+5 growth, -5 preservation)
    
    return min(100, max(0, score))
```

## Color Scheme (Use These)
```python
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#A23B72',    # Purple
    'accent': '#F18F01',       # Orange
    'warning': '#C73E1D',      # Red
    'success': '#5FA8D3',      # Light blue
    'highlight': '#FFBE0B'     # Yellow
}
```

## Edge Test Cases

Include these preset scenarios:
1. **YOLO Grandma**: age=78, horizon=2, all 5s, goal=growth
2. **Terrified 18yr**: age=18, horizon=50, all 1s, goal=preservation
3. **Perfect Moderate**: age=40, horizon=25, all 3s, goal=income
4. **Contradictory**: age=30, horizon=30, comfort=1, reaction=5, goal=growth

## Key Interview Talking Points to Embed

1. **IPS Constraints**: "I didn't just validate math—I implemented actual Investment Policy Statement constraints"
2. **Suitability Layer**: "The system checks if allocations are mathematically correct AND appropriate for the investor"
3. **Conflict Detection**: "Real profiling systems need to catch when investors contradict themselves"
4. **Confidence Scoring**: "Triages allocations for auto-approve vs. human review"
5. **Sensitivity Analysis**: "The What-If analyzer shows how methodology changes propagate"
6. **Production Scale**: "Batch testing simulates validating at scale, not one-off"

## Development Notes

- Use Streamlit session state for baseline preservation
- All warnings should have emoji prefixes (⚠️, 🔴, 🟡, ✅)
- Validation errors vs warnings: errors = breaks rules, warnings = unusual but valid
- Keep code modular: separate profiler logic from validation from visualization
- Add comments explaining WHY each validation check matters (IPS compliance, suitability, etc.)

## Visual Design Guidelines

- Use st.columns() for metrics display
- Progress bars for allocation breakdown
- Pie chart for allocation visualization
- Bar chart for profile comparison
- Side-by-side bar chart for what-if scenario comparison
- Clean, minimal UI with clear section headers

## CSV Format for Batch Testing
```csv
age,time_horizon,risk_comfort,loss_reaction,experience,income_stability,goal
25,40,5,5,3,4,growth
65,5,2,2,4,5,preservation
40,20,3,3,3,3,income
```

## Error Handling

- Validate all inputs (age 18-80, horizon 1-50, ratings 1-5)
- Show user-friendly error messages
- Never crash on invalid input
- Provide helpful guidance when validation fails

## Performance Notes

- Session state prevents recalculation on every interaction
- Batch mode should handle 1000+ profiles efficiently
- Matplotlib figures should be cached where possible

---

## PRIORITY BUILD ORDER

1. models.py (30 min) - Foundation
2. profiler.py (45 min) - Core logic
3. validator.py (2 hours) - THE MOST IMPORTANT PIECE
4. visualizations.py (1 hour) - Charts
5. app.py basic version (1 hour) - Get it working
6. app.py advanced features (2 hours) - What-if, batch, etc.
7. edge_cases.py (30 min) - Testing
8. main.py (30 min) - CLI wrapper

Total: ~8-9 hours of focused work

---

## CRITICAL: The Validator Must Do All This

✅ Mathematical validation (sum, non-negative)
✅ IPS policy constraints (cash limits, alternatives limits, concentration)
✅ Minimum position sizes (no dust)
✅ Liquidity floor checks
✅ Diversification requirements
✅ Risk profile alignment
✅ Conservative safe-haven minimums
✅ Suitability flags (age + allocation mismatch)
✅ Input conflict detection
✅ Confidence score calculation
✅ Multi-tier warnings (errors, warnings, conflicts)

The validator is what makes this a CERTIFICATION tool, not just a calculator.

---

Use this context to rebuild the entire project. Focus on the validator.py file—that's where the magic happens.
```

---

## **🚀 INSTRUCTIONS FOR CLAUDE IN VSCODE**

1. **Open VSCode**
2. **Install Claude AI extension** (if not already)
3. **Create new folder:** `asset-allocation-profiler`
4. **Save the context above as:** `CONTEXT.md`
5. **Open Claude chat in VSCode**
6. **Paste this prompt:**

---
```
I need to rebuild a Python Streamlit asset allocation profiling simulator. 
I have the complete context in CONTEXT.md in this workspace.

Please read CONTEXT.md and then:

1. Create requirements.txt
2. Create models.py with the allocation models
3. Create profiler.py with the risk scoring logic
4. Create validator.py with ALL 12 validation checks (this is the most important file)
5. Create visualizations.py with the matplotlib charts
6. Create app.py with the Streamlit interface including what-if analyzer and batch testing
7. Create edge_cases.py with test scenarios
8. Create main.py as CLI wrapper
9. Create README.md with setup instructions

Focus especially on validator.py - it needs to implement:
- All mathematical checks
- IPS policy constraints
- Suitability flags
- Conflict detection
- Confidence scoring

Make sure the code is production-quality with proper comments explaining 
WHY each validation check matters (not just what it does).

Start with requirements.txt and models.py, then ask me to confirm before 
continuing to the next files.