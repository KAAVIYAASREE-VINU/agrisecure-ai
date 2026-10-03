# Design Document

## Overview

AgriSecure AI is a single-process Streamlit app. The UI layer only displays results. All numbers come from pure functions in `core/`, which take pandas DataFrames or plain values and return plain values, so they can be tested with pytest without Streamlit. Text comes from `lang/*.json`. Assumptions come from `config.py`.

Principle: UI calls core, core never calls UI, and the LLM never calculates.

## Architecture

```
Farmer (phone browser)
        |
  Streamlit UI  (app.py + ui/ screens)
        |  reads text            |  calls functions
   lang/*.json             core/ (pure Python)
                                 |  reads
                    config.py   data/*.csv (cleaned)
        |
  optional: assistant/ (LLM + GuardrailChecker), voice/ (TTS, STT)
```

## Folder Structure

```
agrisecure-ai/
  app.py                 # entry point, screen routing
  config.py              # all assumptions + source notes + last-verified dates
  requirements.txt  README.md  .gitignore  .env.example
  core/
    data_loader.py       # load_csv (st.cache_data wrapper kept in ui), strip_season, validate_row
    costs.py             # CostEstimator
    crops.py             # CropAdvisor (filter, rank, scenarios, break-even)
    risk.py              # RiskEngine (CV colour, DSCR colour)
    loans.py             # LoanAnalyzer (gap, KCC limit, harvest dates)
    comparator.py        # MoneylenderComparator
    schemes.py           # eligibility checks for KCC, PM-KISAN, PMFBY
    formatting.py        # indian_format(), acres_cents()
    guardrail.py         # GuardrailChecker (STRETCH)
  ui/
    i18n.py              # t(key) with English fallback
    screens.py           # language, inputs, results, schemes
    components.py        # icon cards, risk badge, why-button
  assistant/             # STRETCH: llm.py, presets.py
  voice/                 # tts.py (cache), stt.py (STRETCH)
  lang/  en.json ta.json hi.json
  data/  raw/  clean_data.py  cost.csv  yield_price.csv  msp.csv
  tests/ test_costs.py test_crops.py test_risk.py test_loans.py ...
  docs/  phase-notes.md  assumptions.md  viva.md
```

## Data Design

| File | Columns (cleaned) | Purpose |
|---|---|---|
| `cost.csv` | state, season, crop, year, seed, fertilizer, labour, irrigation, other (all Rs per acre) | cost estimate |
| `yield_price.csv` | state, season, crop, year, yield_quintal_per_acre, price_per_quintal | profit, CV, percentiles |
| `msp.csv` | crop, year, msp_per_quintal | MSP comparison |

Rules: `Season` is stripped of whitespace on load. Estimated values are tagged `PLACEHOLDER – verify` in a `note` column. `validate_row` raises `ValueError` on null or negative numeric fields. Dataset candidates to verify before use: the Directorate of Economics and Statistics cost-of-cultivation portal, CACP MSP tables, and Agmarknet or data.gov.in prices. Confirm availability, year, and format first, because they can change.

## Core Interfaces

```python
# formatting.py
def indian_format(amount: float) -> str            # 125000 -> "₹1,25,000"
def acres_cents(acres: float) -> str               # 1.5 -> "1 acre 50 cents"

# crops.py
def available_crops(df, state, season) -> list[str]
def profit_scenarios(df, crop, state, season, total_cost) -> dict   # good/normal/bad or PLACEHOLDER
def profit_range_per_acre(df, crop, state, season, cost_per_acre) -> tuple[float, float] | None
def rank_top3(df, cost_df, state, season) -> list[dict]             # crop, range, risk
def break_even_price(total_cost, median_yield_total) -> float

# costs.py
def estimate_costs(cost_df, crop, state, season, acres, overrides=None) -> dict
# -> {"seed":..,"fertilizer":..,"labour":..,"irrigation":..,"other":..,"total":..,"placeholder":bool}

# risk.py
def cv_risk_colour(yields, prices, cfg) -> "green"|"yellow"|"red"
def dscr(expected_income, repayment_obligation) -> float | None
def dscr_colour(dscr_value, cfg) -> "green"|"yellow"|"red"|None

# loans.py
def funding_gap(total_cost, own_capital) -> float
def institutional_loan_limit(acres, crop, cfg) -> float
def residual_gap(need, loan_limit) -> float                         # never negative
def harvest_window(sowing_month, duration_weeks) -> tuple[int, int] | None

# comparator.py
def interest_costs(principal, months, rates) -> dict   # moneylender, bank, kcc

# guardrail.py (STRETCH)
def check_numbers(llm_reply, allowed_numbers, tolerance) -> tuple[bool, list[float]]
```

## Key Calculations (explain these in the viva)

- **Funding need** = total cost - own capital. **Residual gap** = max(0, need - institutional loan limit).
- **Interest (simple)** = principal x annual rate x months / 12. The comparator uses the same formula for all three lenders, so only the rate differs.
- **Break-even price** = total cost / median total yield (quintals).
- **Profit scenarios**: good = P75 yield x P75 price, normal = median x median, bad = P25 x P25, each minus cost. Assumption: yield and price extremes occur together, which exaggerates extremes. This is documented in `docs/assumptions.md`.
- **Crop risk (CV)** = std / mean for yield and price. Green below the low threshold, red above the high one, thresholds in `config.py`.
- **DSCR** = normal-harvest income / (loan principal + interest). Below `dscr_yellow_threshold` is red, below `dscr_green_threshold` is yellow, otherwise green.
- **Harvest window** = sowing month + duration weeks, converted to a month range.

## UI Design

Screens (one scrolling page after setup, mobile first): (1) language picker; (2) inputs: state, season, crop icon cards, land stepper, Calculate; (3) results: top-3 crops with risk badges, cost breakdown with icons and editable fields, funding gap, lender chart, repayment window, risk meter, profit scenarios and break-even, what-if side-by-side, scheme cards, footer with dataset note and feedback.

Session state keys: `lang`, `state`, `season`, `crop`, `acres`, `cost_overrides`, `own_capital`, `moneylender_rate`, `baseline`, `whatif`, `results`.

Every result block has a "Why this number?" expander using strings from the language file. Chart uses Streamlit's built-in `st.bar_chart` or Altair (already bundled with Streamlit), so no extra library is needed.

## Language Files

Flat keys, identical across the three files, for example: `app_title`, `lang_picker`, `crop_paddy`, `risk_low`, `risk_medium`, `risk_high`, `why_breakeven`, `you_asked`, `extra_moneylender_cost`, `good_harvest`, `normal_harvest`, `bad_harvest`, `disclaimer_loans`, `disclaimer_estimate`, `placeholder_notice`, `error_rate_range`. `i18n.t(key)` falls back to English and logs a warning when a key is missing. A native speaker should review the Tamil and Hindi text.

## Optional and Stretch Components

- **Assistant**: preset answers are built from `results` in session state. If an API key exists, the LLM receives named numbers and rephrases them. `check_numbers` extracts numbers (Indian commas, lakh/crore, Tamil and Devanagari digits) and compares them with the allowed set. On failure, show the preset answer. With no key, the assistant is disabled.
- **Voice output**: `tts.speak(text, lang)` with a hash-keyed LRU cache (50 entries), 10-second timeout, played via `st.audio`.
- **Voice input**: `st.audio_input` plus Whisper or a speech API, always showing "You asked: ...". Typing stays as fallback.
- **Export**: WhatsApp text by default, built only from session results.
- **Feedback**: append a row to `feedback.csv` with no personal data.

## Error Handling

Data errors raise `ValueError` in core, and the UI catches them and shows a localized message. Missing data shows PLACEHOLDER notices. Missing config keys raise a configuration error. Missing optional API key disables only the assistant.

## Testing Strategy

pytest on `core/` only: normal cases, edge cases (zero land, loan larger than need, fewer than 4 rows, missing MSP, whitespace in season, negative or null values), and format tests (`indian_format`, guardrail with Tamil and Devanagari digits). Run `pytest` at the end of every phase. Manual testing: 5 farmer scenarios plus one non-technical user, recorded in `docs/phase-notes.md`.

## Requirement Traceability

| Area | Requirements |
|---|---|
| Language and inputs | 1, 2 |
| Recommendation, costs, loans, comparison, repayment, risk, profit, what-if | 3 to 10 |
| Schemes, presets | 11, 12 |
| Assistant, voice, export, feedback | 13 to 17 |
| Performance, structure, data | 18, 19 |