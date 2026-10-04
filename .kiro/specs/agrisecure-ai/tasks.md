# Implementation Plan

Run only the task I name. At the end, run `pytest -q` and stop. No phase notes, no summaries. Never invent data; unverified values stay tagged PLACEHOLDER – verify.

- [x] 1. Project setup
- [x] 2. Data preparation
- [x] 3. Core calculations
- [x] 4. Checkpoint
- [x] 5. Language files and i18n
- [x] 6.1 Language picker
- [x] 6.2 Input screen
- [x] 6.3 Results screen
- [x] 6.4 Lender chart, risk meter, profit scenarios, break-even

- [ ] 7. RUN A: finish MVP
  - [ ] 7.1 What-if buttons (cost +20%, income -20%, less land) with Reset and side-by-side view
  - [ ] 7.2 Mobile layout and big-button CSS (360 px)
  - [ ] 7.3 Move PLACEHOLDER_TAG into config.py and update imports
  - [ ] 7.4 estimate_costs raises NoDataError when no rows match; UI shows a "no data for this choice" message, never ₹0. Add a test.
  - [ ] 7.5 Season list depends on crop (Kuruvai, Samba, Thaladi are paddy only). Show only crops present in the CSVs.
  - [ ] 7.6 Cache CSV loading with st.cache_data

- [ ] 8. RUN B: schemes, presets, voice
  - [ ] 8.1 core/schemes.py eligibility rules (KCC, PM-KISAN, PMFBY) with tests; scheme text in language files
  - [ ] 8.2 Scheme cards UI, greyed when ineligible, with "Learn more" links
  - [ ] 8.3 Preset question buttons answered from session results
  - [ ] 8.4 voice/tts.py (cache, 10 s timeout, Tamil and Hindi codes) and a speaker button using st.audio with text fallback

<!-- NOT Kiro tasks (done by hand): real datasets, Tamil/Hindi review, docs/assumptions.md, 15 viva Q&As, deployment.
     STRETCH, only if everything works: WhatsApp export, feedback button, guardrail + LLM, voice input. -->