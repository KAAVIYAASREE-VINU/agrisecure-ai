# AgriSecure AI – project rules

- Language: Python only. UI: Streamlit. Data: pandas + CSV. Tests: pytest.
- Calculation logic lives in /core as plain functions, never inside UI code.
- All UI text comes from /lang/en.json, ta.json, hi.json. No hardcoded text.
- All assumptions (interest rates, moneylender rate, risk thresholds, loan
  limits) live in config.py with a source note and "last verified" date.
- NEVER invent numbers. Every figure comes from a /core function. The LLM
  only explains numbers it is given. A guardrail function checks the reply.
- If real data is missing, use clearly labelled placeholder values marked
  "PLACEHOLDER – verify" in the CSV and in the UI footer. Never present
  placeholders as real data.
- API keys only from environment variables. .env is in .gitignore.
- Mobile-first: 360px width, big buttons, icons, high contrast, no login.
- After each phase: run pytest, run the app, fix errors, then summarize
  what was built and WHY (for my viva) in docs/phase-notes.md.