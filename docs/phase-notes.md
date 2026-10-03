# Phase Notes

This file is updated at the end of every phase with:
- what was built
- why key decisions were made
- the pytest command used and its result

---

## Task 1.1 – Project scaffold

**Date completed:** 2025-10-03

### What was built

- Full folder structure: `core/`, `ui/`, `lang/`, `data/raw/`, `tests/`,
  `docs/`, `assistant/`, `voice/` — each Python package has an `__init__.py`.
- `tests/conftest.py` placeholder for shared fixtures.
- `requirements.txt` with exact pinned versions:
  streamlit 1.35.0, pandas 2.2.2, pytest 8.2.2, python-dotenv 1.0.1,
  gTTS 2.5.1, altair 5.3.0.
- `.gitignore` covering `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`,
  raw CSV files, `feedback.csv`, `audio_cache/`.
- `.env.example` documenting the optional `LLM_API_KEY`.
- `README.md` with setup steps, data-download instructions, run command,
  project structure, and known limits (network, data age, hosting, language
  accuracy).
- `app.py` placeholder (screen routing added in task 6.x).

### Why these decisions

- **Pinned versions** prevent subtle breakage when CI or a new machine runs
  `pip install`. Exact pins are easy to loosen later; floating pins are hard
  to pin down when something breaks.
- **`__init__.py` in every package** lets pytest discover tests without extra
  config and allows clean relative imports throughout the project.
- **`.env` in `.gitignore`** satisfies Requirement 19.3 — secrets must never
  reach the repository.
- **`data/raw/` ignored, cleaned CSVs tracked** reflects the design decision
  that raw source files are large, possibly licensed, and manually downloaded,
  while the cleaned artefacts are reproducible and small.

### pytest result

```
python3 -m pytest --tb=short -q
no tests ran in 0.00s
```

No test files exist yet (they are added from task 2.4 onward). Zero failures.

---

## Task 3.5 – `core/loans.py`: funding gap, loan limit, residual gap, harvest window

**Date completed:** 2025-10-03

### What was built

**`core/loans.py`** — four pure functions with no Streamlit imports:

| Function | Signature | Purpose |
|---|---|---|
| `funding_gap` | `(total_cost, own_funds) -> float` | How much the farmer must borrow (`max(0, total_cost - own_funds)`) |
| `institutional_loan_limit` | `(land_acres) -> float` | KCC loan ceiling: `KCC_SCALE_OF_FINANCE_PER_ACRE × acres`, capped at `KCC_MAX_LOAN` |
| `residual_gap` | `(funding_gap, loan_amount) -> float` | Moneylender shortfall (`max(0, gap - loan)`) — never negative |
| `harvest_window` | `(crop, season, df_cost) -> int | None` | Weeks-to-months conversion from `CROP_DURATION_WEEKS` in config.py; `None` for unknown crops |

**`tests/test_loans.py`** — 28 tests across 5 test classes:

- `TestFundingGap` — normal case, zero own funds, exact coverage, surplus own funds (clamped to 0)
- `TestInstitutionalLoanLimit` — normal, zero acres, scaling, KCC cap enforcement
- `TestResidualGap` — normal, exact cover, **loan larger than need → 0** (task key requirement)
- `TestHarvestWindow` — known crops, **missing/unknown crop → None without crash** (task key requirement), case-insensitivity, season parameter stability, specific month counts
- `TestLoanWorkflow` — end-to-end integration: full cover (no moneylender) and partial cover (moneylender needed)

### Why these decisions

- **All three gap functions clamp to `max(0, …)`** — financial logic forbids a negative "debt"; a farmer with more funds than they need has a zero gap, not a negative one. This is the correct behaviour for `loan larger than need`.
- **`harvest_window` returns `None`, not 0 or an exception** — the UI can gracefully hide the harvest countdown instead of showing "0 months" or crashing when a crop like "millet" isn't in the config yet. This satisfies the "missing duration" task requirement.
- **Duration from `config.py`, not the cost CSV** — the cost CSV has no duration column. Putting durations in `config.py` keeps them with the other agricultural assumptions, gives them source notes, and makes them easy to update. The `df_cost` parameter is retained in the signature for future per-CSV overrides and API stability.
- **Weeks → months via `round(weeks / 4.333)`** — the standard average weeks-per-month (365.25/12 ÷ 7 ≈ 4.348; 4.333 is the common approximation). Floor of 1 prevents "0 months" for very short crops.
- **`institutional_loan_limit` uses both `KCC_SCALE_OF_FINANCE_PER_ACRE` and `KCC_MAX_LOAN`** from config.py — both are marked PLACEHOLDER; the cap ensures the function never overstates eligibility for large farms before the constants are verified.

### pytest result

```
python3 -m pytest tests/test_loans.py -v
28 passed in 0.26s

python3 -m pytest --tb=short -q
249 passed in 0.35s
```

All 249 tests pass; no regressions.

---

## Phase 3 – Core Calculation Modules

**Date completed:** 2025-10-03

### What was built

Phase 3 delivered four pure-Python calculation modules in `core/`, each with no Streamlit imports and all constants sourced from `config.py`.

#### `core/crops.py`

| Function | Signature | Purpose |
|---|---|---|
| `available_crops` | `(state, season, df_yield, df_msp) -> list[str]` | Returns crops grown in a given state/season with sufficient historical data |
| `profit_scenarios` | `(crop, state, season, total_cost_per_acre, df_yield, df_msp) -> dict` | Bad/normal/good profit per acre using 10th/50th/90th yield percentiles × latest MSP |
| `profit_range_per_acre` | `(crop, state, season, df_yield, df_msp) -> tuple[float, float]` | (min, max) profit from worst and best historical yield |
| `break_even_price` | `(total_cost_per_acre, yield_per_acre) -> float` | Minimum price needed to cover costs at a given yield |
| `rank_top3` | `(state, season, total_cost_per_acre, df_yield, df_msp, df_cost) -> list[dict]` | Scores crops by combining normal profit and CV-based risk; returns top 3 with colour |

#### `core/risk.py`

| Function | Signature | Purpose |
|---|---|---|
| `cv_risk_colour` | `(cv: float) -> str` | Maps coefficient of variation to "green" / "yellow" / "red" using `CV_GREEN_THRESHOLD` and `CV_RED_THRESHOLD` from config.py |
| `dscr` | `(annual_income, total_annual_debt_obligation) -> float` | Computes Debt Service Coverage Ratio; returns `math.inf` when obligation is zero |
| `dscr_colour` | `(dscr_value: float) -> str \| None` | Maps DSCR to "green" / "yellow" / "red" / `None` (indeterminate) using config thresholds |

#### `core/loans.py`

| Function | Signature | Purpose |
|---|---|---|
| `funding_gap` | `(total_cost, own_funds) -> float` | How much the farmer must borrow (`max(0, cost − own_funds)`) |
| `institutional_loan_limit` | `(land_acres) -> float` | KCC ceiling: `KCC_SCALE_OF_FINANCE_PER_ACRE × acres`, capped at `KCC_MAX_LOAN` |
| `residual_gap` | `(funding_gap, loan_amount) -> float` | Moneylender shortfall after institutional loan, clamped to zero |
| `harvest_window` | `(crop, season, df_cost) -> int \| None` | Duration in months from `CROP_DURATION_WEEKS` in config.py; `None` for unknown crops |

#### `core/comparator.py`

| Function | Signature | Purpose |
|---|---|---|
| `interest_costs` | `(principal, months, moneylender_rate=None) -> dict` | Simple interest cost for moneylender, bank, and KCC for the same principal and term |

---

### Why each module exists (for the viva)

**`crops.py`** — The central "crop advisor" module. `available_crops` filters the yield CSV to crops with enough historical records in a given state/season; `profit_scenarios` quantifies expected profit under bad/normal/good harvests using the 10th, 50th, and 90th yield percentile against the most recent MSP price, so farmers can see downside risk in rupees. `rank_top3` combines profit score and CV-based risk into a single ranked list, letting farmers see which crop is both profitable *and* stable — this is the core output of the recommendation screen.

**`risk.py`** — Turns abstract statistics into actionable colours. `cv_risk_colour` translates a raw coefficient of variation (a dimensionless volatility measure) into a traffic-light colour that a farmer without a maths background can immediately understand. `dscr` and `dscr_colour` do the same for loan repayment risk: DSCR < 1.0 is red because the farmer's expected income cannot cover their debt obligation; DSCR ≥ 1.5 is green because there is a comfortable buffer. All thresholds come from `config.py` with source notes, so an agronomist can revise them without touching the logic.

**`loans.py`** — Breaks the funding problem into three layers: total need → institutional loan (KCC/bank) → residual moneylender gap. This matters because the farmer's *cheapest available credit* (KCC at 4% effective, 7% nominal) covers only part of the need for large farms; showing the residual gap explicitly tells the farmer exactly how much they still need from a moneylender and at what cost. `harvest_window` converts weeks to months so the UI can show a harvest countdown without crop-specific UI logic.

**`comparator.py`** — The "cost of credit" module. By computing simple interest for the same principal and term at moneylender, bank, and KCC rates, `interest_costs` lets a farmer see in rupees — not percentages — how much they save by accessing formal credit. This directly supports Requirement 6.2 (interest cost comparison chart) and provides the quantitative foundation for the financial inclusion argument in the app.

---

### Design decisions worth noting for the viva

1. **All constants in `config.py`, never in calculation files.** Moneylender rate default (36% pa, RBI FI Survey 2021), KCC rate (4% effective after subvention), CV thresholds (0.20/0.40), DSCR thresholds (1.0/1.5) — every figure has a source comment and "last verified" date. Changing an assumption requires editing exactly one file.

2. **Percentile-based profit scenarios instead of point estimates.** Using the 10th/50th/90th percentile of historical district yield data gives a distribution-aware bad/normal/good range, which is more honest than a single "expected yield" figure and better communicates agricultural risk to the farmer.

3. **`rank_top3` scoring formula: `(normal_profit / max_profit) × (1 − cv_penalty)`.** This composite score penalises high-CV crops even if their expected profit is high, reflecting the reality that a volatile crop is riskier for a smallholder who cannot absorb a bad year.

4. **`math.inf` for zero debt obligation, `None` for indeterminate DSCR colour.** Returning `math.inf` from `dscr()` avoids `ZeroDivisionError` and signals "no debt" cleanly. `dscr_colour` then returns `None` instead of a colour, so the UI can show "indeterminate" rather than misrepresenting the farmer's situation as either safe or risky.

5. **`harvest_window` returns `None` for unknown crops, not 0.** A "0 months to harvest" display would mislead; `None` tells the UI to hide the countdown gracefully, which is safer for future crop additions.

6. **`interest_costs` validates `moneylender_rate` against `[MONEYLENDER_RATE_MIN, MONEYLENDER_RATE_MAX]`.** This prevents both typos (e.g., 360 instead of 36) and obviously implausible rates from producing misleading comparison charts. The range itself is stored in `config.py`.

---

### Test summary

```
pytest --tb=short
285 passed in 0.45s
```

| Test file | Tests | Covers |
|---|---|---|
| `test_cleaning.py` | 11 | CSV cleaning helpers |
| `test_comparator.py` | 23 | `interest_costs` incl. edge cases and rate validation |
| `test_config.py` | 44 | All config keys, types, and sentinel checks |
| `test_costs.py` | 25 | `core/costs.py` labour/input cost functions |
| `test_crops.py` | 59 | `available_crops`, `profit_scenarios`, `profit_range_per_acre`, `break_even_price`, `rank_top3` |
| `test_data_loader.py` | 32 | CSV loaders, placeholder detection |
| `test_formatting.py` | 32 | Number/currency/percentage formatting |
| `test_loans.py` | 28 | `funding_gap`, `institutional_loan_limit`, `residual_gap`, `harvest_window` |
| `test_risk.py` | 31 | `cv_risk_colour`, `dscr`, `dscr_colour` |
| **Total** | **285** | **No failures** |
