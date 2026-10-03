# Requirements Document

## Introduction

AgriSecure AI is a mobile-first Streamlit web app (Python only) that helps Indian smallholder farmers, especially low-literacy users in Tamil Nadu, decide what to grow and whether they can repay a crop loan safely. It uses icon-driven screens (max 4 taps to a result), shows figures as estimates or ranges, and never tells a farmer to take a loan. Every number comes from a plain Python function in `/core`. An optional LLM only rephrases numbers it is given.

**Priority tags:** MVP = must work by end of week 2. NEXT = weeks 3. STRETCH = only if time remains.
**Known limits (to state in the report):** Streamlit is heavy on 2G/3G and works best on 4G. Cost data is state-average and may be several years old. Free hosting may reset local files.

## Glossary

- **App**: the AgriSecure AI Streamlit application.
- **Farmer**: the user, possibly low-literacy.
- **CropAdvisor / CostEstimator / LoanAnalyzer / MoneylenderComparator / RiskEngine**: `/core` modules for recommendation, costs, loan and repayment, lender comparison, and risk colours.
- **GuardrailChecker**: `/core` function that checks every number in an LLM reply against the numbers supplied to it.
- **KCC**: Kisan Credit Card, the main institutional crop loan.
- **MSP**: Minimum Support Price. **KVK**: Krishi Vigyan Kendra.
- **Season**: exactly as it appears in the dataset (for example Kuruvai, Samba, Thaladi, Navarai for Tamil Nadu paddy), with leading and trailing whitespace stripped.
- **Acre / Cent**: 1 acre = 100 cents. **Quintal**: 100 kg.
- **PLACEHOLDER**: a value marked `PLACEHOLDER – verify` in the CSV and in the UI footer when real data is unavailable.
- **DSCR**: expected harvest income divided by total loan repayment obligation.
- **CV**: coefficient of variation (standard deviation divided by mean).

## Global Rules (apply to every requirement)

- G1. All UI text comes from `/lang/en.json`, `ta.json`, `hi.json`. No hardcoded UI strings. A missing key falls back to English and logs a warning.
- G2. All assumptions (rates, thresholds, loan limits, crop durations, tolerances) live in `config.py`, each with an inline source note and a `YYYY-MM-DD` last-verified date.
- G3. No numbers are invented. Missing data shows a PLACEHOLDER notice, never a guess.
- G4. Money uses Indian format (₹1,25,000). Wherever a loan figure appears, the App shows "Talk to your bank, agriculture office, or KVK before deciding" in the active language, and never advises a specific loan or lender.
- G5. Every key result has a "Why this number?" button explaining the formula in simple words from the language file, with no LLM involved.
- G6. Interactive elements are at least 48x48 px. The layout works at 360 px width without horizontal scrolling. Text meets WCAG AA contrast (4.5:1).

---

## Requirements

### Requirement 1: Language Selection [MVP]
**User Story:** As a Farmer, I want to pick my language first, so that I can use the whole app in it.

1. WHEN no language is stored in session state, THE App SHALL show a language screen first, with exactly three options, English, தமிழ், and हिन्दी, each in its own script.
2. WHEN the Farmer selects or changes language, THE App SHALL reload all text from the matching JSON file and rerun, preserving all other session state (inputs, selections).

### Requirement 2: Inputs by Tapping [MVP]
**User Story:** As a Farmer, I want to tap icons to set up my query, so that I can reach a result in at most 4 taps.

1. THE App SHALL require only four inputs: state, season, crop, land size. Defaults: Tamil Nadu, first season in the dataset for that state, 1.00 acre. A Farmer accepting defaults reaches a result in 2 taps (crop, then Calculate).
2. WHEN state and season are chosen, THE CropAdvisor SHALL list only crops present in the dataset for that combination.
3. THE App SHALL show each crop as an icon card with its local name in the active language, using a placeholder silhouette if the icon file is missing.
4. THE App SHALL provide a land-size stepper in acres and cents, minimum 0.10 acre, maximum 999.90 acres, step 0.10 acre (10 cents), always displaying the value as, for example, "1 acre 50 cents".
5. IF no crop is selected or land size is invalid, THEN THE App SHALL disable Calculate and show which input is missing.
6. THE data loader SHALL strip whitespace from Season names before matching or display.

### Requirement 3: Crop Recommendation, "What should I grow?" [MVP]
**User Story:** As a Farmer, I want the top 3 crops for my state and season, so that I can choose well.

1. THE CropAdvisor SHALL return the top 3 crops by descending expected profit per acre, computed only by `/core` functions on the loaded dataset.
2. THE RiskEngine SHALL assign green, yellow or red per crop from the CV of yield and price, with thresholds in `config.py`. A crop with fewer than 3 historical records SHALL be red.
3. THE App SHALL show the risk as a colour icon plus a text label ("Low", "Medium", "High Risk") from the language file.
4. THE App SHALL show profit per acre as a range ("₹[low] to ₹[high] per acre", 25th to 75th percentile) labelled "estimate". WHERE a crop has fewer than 4 records, THE App SHALL show a PLACEHOLDER notice instead.
5. IF fewer than 3 crops exist for the selection, THE App SHALL show only those and a notice. IF no data exists or a calculation raises an exception, THE App SHALL show a localized message and exclude the failed crop(s).

### Requirement 4: Cost of Cultivation [MVP]
**User Story:** As a Farmer, I want to see and edit my expected costs, so that the numbers match my real situation.

1. THE CostEstimator SHALL return cost per acre as named components (seed, fertilizer, labour, irrigation, other) plus a total, from the dataset, scaled by land size.
2. THE App SHALL show each component with an icon and rupee value, and allow the Farmer to edit it within ₹0 to ₹99,99,999. IF the value is out of range, THEN THE App SHALL reject it and keep the previous value.
3. WHEN a cost is edited, THE App SHALL recalculate all downstream results automatically.
4. WHEN real cost data is unavailable, THE App SHALL use PLACEHOLDER values and show a PLACEHOLDER notice in the footer.

### Requirement 5: Funding Gap and Institutional Loan [MVP]
**User Story:** As a Farmer, I want to see how much I need, how much a crop loan could cover, and what is left, so that I can plan.

1. THE LoanAnalyzer SHALL compute: funding need = total cost minus the Farmer's own capital (default ₹0, editable between ₹0 and total cost).
2. THE LoanAnalyzer SHALL compute one institutional crop loan limit (KCC as the primary option) from land size and a per-acre scale-of-finance value in `config.py`. KCC and "bank loan" SHALL NOT be added together.
3. THE App SHALL show: total need, own capital, institutional loan coverage, and the residual gap (amount still needed). IF coverage meets or exceeds need, the residual gap is ₹0 and the App shows a label saying institutional loans can cover the need.
4. WHEN inputs change, THE App SHALL recompute within 1 second without a manual action.

### Requirement 6: Moneylender vs Institutional Loan Cost [MVP]
**User Story:** As a Farmer, I want to see how much extra a moneylender costs, so that I understand the true price of borrowing.

1. THE MoneylenderComparator SHALL compute total interest for the residual gap or loan amount at (a) a moneylender rate (editable by the Farmer, valid 1% to 200% per year), (b) the bank rate, and (c) the KCC rate, with rates in `config.py`.
2. THE App SHALL show a bar chart (moneylender red, bank amber, KCC green) and the rupee difference between moneylender and KCC above it, labelled with the "extra_moneylender_cost" key. IF the rate entered is invalid, THEN THE App SHALL show an error and not recompute.
3. THE App SHALL NOT recommend any lender.

### Requirement 7: Harvest-Based Repayment [MVP]
**User Story:** As a Farmer, I want the repayment time in harvest months, not EMIs, so that it matches when I earn.

1. THE LoanAnalyzer SHALL derive the harvest month range from the season's sowing month plus the crop duration in weeks (from `config.py` or the dataset).
2. THE App SHALL show the repayment time as a month range (for example "Repay between October and November after harvest"), with no mention of EMI. For KCC, THE App SHALL also show the deadline month and year as a separate labelled line.
3. IF duration data is missing, THEN THE App SHALL show a localized "cannot calculate repayment date" message and no placeholder month.

### Requirement 8: Repayment Risk Meter [MVP]
**User Story:** As a Farmer, I want a green/yellow/red signal on whether I can repay safely, so that I know the risk.

1. THE RiskEngine SHALL compute DSCR using the normal-harvest expected income and map it to red (below `dscr_yellow_threshold`), yellow (between the thresholds), or green (at or above `dscr_green_threshold`), with thresholds in `config.py`.
2. THE App SHALL show the result as a 48x48 px or larger icon (green circle, yellow triangle, red diamond) with a one-sentence reason below it.
3. IF repayment obligation is zero or income is unavailable, THEN THE App SHALL show an "indeterminate" message and no colour.
4. THE App SHALL update the result automatically when any input changes.

### Requirement 9: Profit Scenarios and Break-Even [MVP]
**User Story:** As a Farmer, I want to see good, normal and bad harvest profits and the break-even price, so that I can judge the downside.

1. THE CropAdvisor SHALL compute income for three scenarios from the dataset (minimum 4 rows): good (75th percentile yield x 75th percentile price), normal (median x median), bad (25th x 25th). This combination is a documented simplifying assumption, recorded in `docs/assumptions.md`.
2. THE App SHALL show profit (income minus cost) for each scenario as an estimate with a one-line reason, labelled "good_harvest", "normal_harvest", "bad_harvest".
3. THE CropAdvisor SHALL compute break-even price per quintal = total cost divided by median expected yield, and THE App SHALL show it beside the MSP. IF break-even exceeds MSP, THE App SHALL show a warning. IF MSP is missing, THE App SHALL show a PLACEHOLDER notice and skip the comparison.
4. IF the dataset has fewer than 4 rows for the selection, THEN THE App SHALL show PLACEHOLDER notices instead of scenario values.

### Requirement 10: What-If Buttons [MVP]
**User Story:** As a Farmer, I want to test "what if" cases with one tap, so that I can stress-test my plan.

1. THE App SHALL provide exactly three buttons: Costs +20%, Income -20%, Less land (-0.5 acre), plus a Reset button.
2. WHEN a what-if button is tapped, THE App SHALL apply that single change to the baseline (not stacked on earlier taps), recompute all outputs within 2 seconds, and show the original and what-if results side by side.
3. IF a change would make an input invalid (for example land below the minimum), THEN THE App SHALL show an error and not recompute.

### Requirement 11: Government Scheme Cards [NEXT]
**User Story:** As a Farmer, I want to see KCC, PM-KISAN and PMFBY details, so that I know what help may exist.

1. THE App SHALL show a card per scheme (KCC, PM-KISAN, PMFBY) with name, one-sentence benefit, eligibility points, documents needed, and where to apply, all from the language file. Scheme rules SHALL be marked "verify on official site" with a last-verified date in `config.py`.
2. IF the Farmer's land or crop makes a scheme ineligible, THEN THE App SHALL grey the card and show a one-sentence reason.
3. THE App SHALL show a "Learn more" link from `config.py` (opening in a new tab) and hide it if the URL is missing. IF a text field is missing, THE App SHALL show "PLACEHOLDER – verify" for it.

### Requirement 12: Preset Question Buttons [NEXT]
**User Story:** As a Farmer, I want one-tap answers to common doubts, so that I do not need to type.

1. THE App SHALL provide three buttons: "Can I repay on time?", "What if rain fails?", and "Is moneylender worth it?" (labels from the language file).
2. WHEN tapped, THE App SHALL answer within 1 second using only `/core` results already computed in the session, with no LLM, prefixed by the "you_asked" key and the question.
3. THE answer to "Is moneylender worth it?" SHALL show the cost comparison only, with no recommendation.
4. IF the required results are not yet computed or a calculation fails, THEN THE App SHALL show a localized message naming the missing step, and no partial answer.

### Requirement 13: AI Assistant with Number Guardrail [STRETCH]
**User Story:** As a Farmer, I want to ask a typed question and get an answer in my language, so that I can ask about my own situation.

1. THE App SHALL provide a text box (up to 500 characters). Typing SHALL always remain available, even if voice input exists.
2. THE LLM API key SHALL be OPTIONAL. IF it is absent, THEN THE App SHALL disable the assistant and show preset questions only, and SHALL NOT crash.
3. THE Assistant SHALL pass computed results as named key-value pairs to the LLM, and the LLM SHALL only rephrase them. Every answer SHALL start with "You asked: [question]" from the language file.
4. THE GuardrailChecker SHALL be a standalone `/core` function `(llm_reply, allowed_numbers, tolerance) -> (is_safe, violating_numbers)`. It SHALL parse Indian formats (1,25,000), "lakh" and "crore", and Tamil and Devanagari digits. pytest SHALL cover each format. IF any number is not in the allowed set, THEN THE App SHALL discard the reply and show a preset answer.
5. IF the question mentions a crop or state not in the session data, or no results are computed yet, THEN THE Assistant SHALL show a localized message directing the Farmer to their local bank, agriculture office or KVK, without calling the LLM.

### Requirement 14: Voice Output [NEXT]
**User Story:** As a low-literacy Farmer, I want the key result read aloud, so that I can understand without reading.

1. THE App SHALL generate speech (gTTS or edge-tts, pinned in `requirements.txt`, using the Tamil or Hindi language code when active) for: the top crop and its profit range, the risk label and reason, and any preset answer.
2. THE App SHALL cache audio by hash of text plus language code (max 50 entries, least-recently-used eviction) and play it with Streamlit's built-in audio player.
3. IF TTS fails or exceeds 10 seconds, THEN THE App SHALL show the text result and a localized notice. The Farmer can always read the result.
4. IF the audio is not ready within 2 seconds of tapping, THE App SHALL show a loading indicator from the language file.

### Requirement 15: Voice Input [STRETCH]
**User Story:** As a Farmer who cannot type well, I want to ask by voice, so that I can use the assistant easily.

1. THE App MAY accept recorded audio (Streamlit audio input plus Whisper or a speech API) and transcribe it, always showing "You asked: ..." so the Farmer can correct it.
2. IF transcription fails, THEN THE App SHALL fall back to typing. Tamil and Hindi accuracy SHALL be tested before demo.

### Requirement 16: Summary Export [STRETCH]
**User Story:** As a Farmer, I want a one-page summary to share with a bank officer or family.

1. THE App SHALL export, in the active language and from session results only (no `/core` calls inside the export), these sections in order: crop, land size, costs, profit scenarios, risk result, repayment date, and the G4 disclaimer.
2. THE default format SHALL be WhatsApp-ready text. PDF is optional and SHALL bundle Noto Sans Tamil and Devanagari fonts so the text does not show as boxes. `export_format` in `config.py` is `"whatsapp_text"` or `"pdf"`.
3. THE footer SHALL include dataset name, year, "estimate, not financial advice", and a PLACEHOLDER notice if any placeholder was used. IF sections are incomplete, THE App SHALL list them and not export.

### Requirement 17: Feedback Button [STRETCH]
**User Story:** As a Farmer, I want a "my result looks wrong" button, so that I can flag problems simply.

1. THE App SHALL show the button on every results screen. WHEN tapped, THE App SHALL log timestamp, crop, season, state, land size and risk colour (no personal data) to a local file, ignore repeat taps within 2 seconds, and show a thank-you message from the language file.
2. IF the file cannot be written, THEN THE App SHALL show an error. Note: on free hosting the file may reset, so export or copy the log during testing.

### Requirement 18: Performance and Accessibility [NEXT]
**User Story:** As a Farmer on a cheap phone, I want the app to load and respond quickly.

1. THE App SHALL load CSV files once using `st.cache_data` and not re-read them during a session.
2. THE App SHALL show a loading indicator (from the language file) during any computation or TTS that takes more than 500 ms.
3. THE App SHALL meet G6 on every screen. Streamlit's weight on slow networks is documented as a known limit.

### Requirement 19: Project Structure, Config and Data Integrity [MVP]
**User Story:** As a developer, I want a clear structure and labelled data, so that the project is auditable and safe.

1. THE project SHALL have: `core/`, `lang/`, `data/`, `config.py`, `app.py`, `tests/`, `docs/`, `requirements.txt`, `README.md`, `.gitignore`.
2. WHEN a CSV row is used, THE `/core` function SHALL check that required numeric fields are non-null and not negative, and otherwise raise `ValueError` naming the field, row and problem.
3. Secrets SHALL come only from environment variables. `.env` SHALL be in `.gitignore`. A missing OPTIONAL key (the LLM key) SHALL NOT stop the App from starting.
4. `data/clean_data.py` SHALL document each dataset's name, URL and year in a header comment, strip whitespace from Season names, and tag any estimated value `PLACEHOLDER – verify`.
5. AFTER each phase, `pytest` SHALL pass with zero failures, and a summary (components, reasons for decisions, pytest command and result) SHALL be added to `docs/phase-notes.md`.
6. IF a `/core` function uses a `config.py` key that is not defined, THEN THE App SHALL raise a configuration error naming the key.