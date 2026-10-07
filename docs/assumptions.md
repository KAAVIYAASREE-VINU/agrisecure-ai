# AgriSecure AI — Documented Assumptions

This file records every simplifying assumption in the model. Each entry states
what was assumed, why, and what the limitation is. Written for the viva.

---

## 1. Profit scenario logic (P25 × P25, median × median, P75 × P75)

**What:** The three scenarios (bad / normal / good harvest) use the 25th, 50th,
and 75th percentile of yield **and** price together from historical data.

**Why:** It is a practical simplification that produces three clearly separated
outcomes without needing a joint probability model.

**Limitation:** This exaggerates the spread. In reality, a bad-yield year does
not always coincide with a low-price year (and vice versa). The true worst case
is less bad and the true best case is less good than the model shows. Users are
told these are estimates.

---

## 2. Cost basis: A2+FL (not C2)

**What:** The DES Cost of Cultivation data provides multiple cost concepts. This
app uses the **A2+FL** concept (all paid-out costs plus imputed value of family
labour), not C2 (full economic cost including land rent and depreciation).

**Why:** A2+FL is the standard basis recommended by CACP for farm-level
decision-making and is the figure most farmers recognise as their "out of pocket"
cost plus family labour.

**Limitation:** A2+FL understates the true economic cost. A farmer who owns land
does not see rent as a cash expense, but it is a real opportunity cost. Viva
note: mention that moving to C2 would lower the DSCR and make risk assessments
more conservative.

---

## 3. Rice-to-paddy conversion factor: 0.67

**What:** The TN Season and Crop Report publishes yield as **milled rice**
(kg/ha). The app stores and uses **paddy** (unhusked grain), consistent with
MSP announcements and cost data which are also in paddy terms.

Conversion: `paddy_kg = rice_kg / 0.67`  (equivalently, milling outturn = 67 %).

**Source:** Standard milling outturn figure widely cited in CACP and DES
publications. Actual outturn varies by variety (typically 65–70 %).

**Limitation:** A fixed 67 % is an average. Improved varieties can yield higher
outturn; older varieties lower. Recorded in `data/build_yield_price.py`.

---

## 4. Ranking weight: 80 % profit, 20 % risk (CV)

**What:** `rank_top3` scores each crop as
`0.80 × normalised_mean_profit + 0.20 × (1 − normalised_CV)`.
Both signals are min-max normalised across the candidate crops for the chosen
state/season before combining.

**Why:** The 80/20 split prioritises financial return while still penalising
highly volatile crops. It is a calibrated assumption, not derived from survey
data.

**Limitation:** The weights have not been validated with farmer preferences. A
risk-averse farmer might prefer 50/50. The weights are in `config.py` and can
be changed; recalibration would require a farmer survey.

---

## 5. KCC interest rate: 4 % effective vs 7 % base

**What:** The app shows a KCC rate of **4 % per year** (effective), which is the
rate a farmer pays after the Government of India's 3 % interest subvention.

**Condition:** The subvention applies only when (a) the loan is repaid on time
and (b) the loan amount is up to ₹3 lakh.

**Base rate:** 7 % per year (before subvention). Late repayment forfeits the
subvention and the full 7 % applies.

**Source:** GoI KCC scheme circular 2023-24. Values in `config.py` with
`last_verified` date. The app states the condition in the UI and in
`lang/en.json` key `scheme_kcc_benefit`.

---

## 6. Cost data: DES 2020-21, season assumed

**What:** The cost figures in `data/cost.csv` come from the DES Cost of
Cultivation survey for Tamil Nadu, 2020-21 triennium.

**Season assumed:** The DES source does not break costs down by season within
a state. The Kuruvai season was assigned to paddy and maize based on the Tamil
Nadu crop calendar; Rabi was assigned to groundnut. This assumption is recorded
in the `note` column of `cost.csv`.

**Limitation:** Costs for Samba or Thaladi seasons may differ from Kuruvai.
The 2020-21 data is several years old; input costs (especially labour and
fertiliser) have risen since then. The UI shows a caption noting the data year
and that current costs may be higher.

---

## 7. MSP 2018-19 and 2019-20: secondary source

**What:** MSP values for 2018 and 2019 (kharif seasons 2018-19 and 2019-20)
were sourced from Plantix blog, a secondary (non-government) source.

**Why:** The specific PIB press releases for those years were not located during
data preparation.

**Limitation:** These values have been cross-checked against CACP year-on-year
percentage increases but are not verified against an official PIB or CACP
document. They are noted as `secondary source` in `msp.csv`. Replace with the
official PIB press releases if time permits before the viva.

---

## 8. All prices and costs in ₹ per quintal (100 kg) / per acre

**What:** The app uses two units consistently:
- Prices: **₹ per quintal** (100 kg), matching MSP and market price publications.
- Costs: **₹ per acre**, matching DES cost tables (after dividing hectare figures
  by 2.47105).
- Yield: **quintals per acre** (derived from kg/ha ÷ 100 ÷ 2.47105).

**Why:** This is the unit convention used by CACP, DES, and Agmarknet. Farmers
in Tamil Nadu also quote prices per quintal or per bag (75 kg for paddy).

**Limitation:** No per-kg or per-bag conversion is performed in the UI. If a
farmer quotes a price in a different unit, they must convert before entering it.

---

*Last updated: 2026-10-07*
