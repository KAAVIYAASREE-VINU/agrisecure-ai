# Implementation Plan

MVP tasks come first. At the end of each top-level task, run pytest -q. Do not write phase notes or summaries.

- [x] 1. Project setup [MVP]
  - [x] 1.1 Create folder structure, `requirements.txt` (streamlit, pandas, pytest), `.gitignore` (include `.env`), `.env.example`, `README.md`
    - _Requirements: 19.1, 19.3_
  - [x] 1.2 Create `config.py` with all assumptions, each with a source note and last-verified date
    - _Requirements: G2, 19.6_

- [x] 2. Data preparation [MVP]
  - [x] 2.1 Document dataset sources in `data/clean_data.py` header and list the files I must download manually
    - _Requirements: 19.4_
  - [x] 2.2 Write cleaning script: strip Season whitespace, standardise crop names, tag estimates as `PLACEHOLDER – verify`, output `cost.csv`, `yield_price.csv`, `msp.csv`
    - _Requirements: 2.6, 19.4_
  - [x] 2.3 Write `core/data_loader.py` with `validate_row` (raise `ValueError` for null or negative)
    - _Requirements: 19.2_
  - [x] 2.4 Write tests for cleaning and validation
    - _Requirements: 19.5_

- [x] 3. Core calculations [MVP]
  - [x] 3.1 `core/formatting.py`: `indian_format`, `acres_cents`, with tests
    - _Requirements: 2.4, G4_
  - [x] 3.2 `core/costs.py`: `estimate_costs` with overrides and range checks, with tests
    - _Requirements: 4.1, 4.2, 4.4_
  - [x] 3.3 `core/crops.py`: `available_crops`, `profit_scenarios`, `profit_range_per_acre`, `break_even_price`, with tests (fewer than 4 rows, missing MSP)
    - _Requirements: 2.2, 3.4, 9.1, 9.3, 9.4_
  - [x] 3.4 `core/risk.py`: `cv_risk_colour`, `dscr`, `dscr_colour`, with tests (zero obligation, thresholds)
    - _Requirements: 3.2, 8.1, 8.3_
  - [x] 3.5 `core/loans.py`: `funding_gap`, `institutional_loan_limit`, `residual_gap`, `harvest_window`, with tests (loan larger than need, missing duration)
    - _Requirements: 5.1, 5.2, 5.3, 7.1, 7.3_
  - [x] 3.6 `core/comparator.py`: `interest_costs` for moneylender, bank, KCC, with rate range validation and tests
    - _Requirements: 6.1, 6.2_
  - [x] 3.7 `core/crops.py`: `rank_top3` combining profit and risk
    - _Requirements: 3.1, 3.5_

- [x] 4. Checkpoint: run `pytest`, fix failures, write phase note

- [x] 5. Language files and i18n [MVP]
  - [x] 5.1 Create `lang/en.json` with all keys from design.md, then `ta.json` and `hi.json`
    - _Requirements: 1.1, 1.2, G1_
  - [x] 5.2 `ui/i18n.py`: `t(key)` with English fallback and warning, with tests
    - _Requirements: G1_

- [ ] 6. Streamlit UI, MVP screens [MVP]
  - [x] 6.1 Language picker screen with session state
    - _Requirements: 1.1, 1.2_
  - [x] 6.2 Input screen: state, season, crop icon cards, land stepper, Calculate enable and disable
    - _Requirements: 2.1 to 2.5_
  - [ x] 6.3 Results screen: top-3 crops with risk badges, cost breakdown with editable fields, funding gap, repayment window
    - _Requirements: 3, 4, 5, 7_
  - [x] 6.4 Lender comparison chart, risk meter, profit scenarios, break-even vs MSP, "Why this number?" expanders, loan disclaimer
    - _Requirements: 6, 8, 9, G4, G5_
  - [ ] 6.5 What-if buttons and Reset with side-by-side view
    - _Requirements: 10_
  - [ ] 6.6 Mobile layout and big-button CSS, check at 360 px
    - _Requirements: G6, 18.3_

- [ ] 7. Checkpoint: run app and `pytest`, test with 2 realistic scenarios, write phase note

- [ ] 8. Schemes and presets [NEXT]
  - [ ] 8.1 `core/schemes.py` eligibility rules and scheme text in language files
    - _Requirements: 11_
  - [ ] 8.2 Scheme cards UI with greyed ineligible cards and "Learn more" links
    - _Requirements: 11.1 to 11.3_
  - [ ] 8.3 Preset question buttons answered from session results
    - _Requirements: 12_

- [ ] 9. Voice output [NEXT]
  - [ ] 9.1 `voice/tts.py` with cache, 10-second timeout, language codes for Tamil and Hindi
    - _Requirements: 14.1 to 14.3_
  - [ ] 9.2 Speaker button using `st.audio`, text fallback on failure
    - _Requirements: 14.3, 14.4_

- [ ] 10. Performance polish [NEXT]
  - [ ] 10.1 `st.cache_data` for CSV loading, loading indicators
    - _Requirements: 18.1, 18.2_

- [ ] 11. Checkpoint: write 5 farmer test scenarios with expected outputs in `docs/phase-notes.md`

- [ ] 12. Assistant with guardrail [STRETCH]
  - [ ] 12.1 `core/guardrail.py` `check_numbers` handling Indian formats, lakh/crore, Tamil and Devanagari digits, with tests
    - _Requirements: 13.4_
  - [ ] 12.2 LLM wrapper with optional API key and preset fallback, typed input only
    - _Requirements: 13.1 to 13.3, 13.5_

- [ ] 13. Export, feedback, voice input [STRETCH]
  - [ ] 13.1 WhatsApp text export from session results
    - _Requirements: 16_
  - [ ] 13.2 Feedback logging button
    - _Requirements: 17_
  - [ ] 13.3 Voice input with transcript confirmation and typing fallback
    - _Requirements: 15_

- [ ] 14. Deployment and documentation
  - [ ] 14.1 Deploy to a free host (verify current free-tier limits), set secrets in host settings
  - [ ] 14.2 Write `docs/assumptions.md`, architecture diagram, 15 viva questions with answers, field-test sheet
    - _Requirements: 19.5_