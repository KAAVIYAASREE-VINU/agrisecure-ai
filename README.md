# AgriSecure AI

A mobile-first Streamlit app that helps Indian smallholder farmers decide what
to grow and whether they can safely repay a crop loan. It works in English,
தமிழ் (Tamil), and हिन्दी (Hindi), and requires at most 4 taps to reach a
result.

Every number is computed by a plain Python function in `core/`. An optional
LLM only rephrases numbers it is given — it never invents figures.

---

## Setup

### 1 — Clone and install dependencies

```bash
git clone <repo-url>
cd agrisecure-ai
pip install -r requirements.txt
```

### 2 — Configure secrets (optional)

```bash
cp .env.example .env
# Edit .env and add your LLM_API_KEY if you want the AI assistant.
# The app works fine without it.
```

### 3 — Add data files

The cleaned CSV files are **not** included in the repository because the
source datasets require manual download and verification:

| File | Source |
|---|---|
| `data/cost.csv` | Directorate of Economics and Statistics – cost-of-cultivation portal |
| `data/yield_price.csv` | Agmarknet / data.gov.in price and yield tables |
| `data/msp.csv` | CACP MSP tables |

Run `python data/clean_data.py` after placing the raw files in `data/raw/`
to produce the cleaned CSVs. Until then the app uses `PLACEHOLDER – verify`
values and shows a notice in the footer.

### 4 — Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Run tests

```bash
pytest
```

Tests live in `tests/` and cover all `core/` functions. See
`docs/phase-notes.md` for phase-by-phase test results.

---

## Project structure

```
agrisecure-ai/
  app.py              Entry point, screen routing
  config.py           All assumptions (rates, thresholds, limits) with source notes
  requirements.txt
  .env.example
  core/               Pure Python calculation functions (no Streamlit)
  ui/                 Streamlit screens and components
  lang/               en.json, ta.json, hi.json – all UI text
  data/               raw/  clean_data.py  cost.csv  yield_price.csv  msp.csv
  tests/              pytest test files for core/
  docs/               phase-notes.md, assumptions.md, viva.md
  assistant/          Optional LLM wrapper (STRETCH)
  voice/              TTS and STT helpers (NEXT/STRETCH)
```

---

## Known limits

- **Network**: Streamlit works best on 4G. 2G/3G connections may be slow to
  load the initial page.
- **Cost data**: CSV figures are state-level averages and may be one or more
  years old. Always check with your local KVK or agriculture office.
- **Hosted file persistence**: free hosting tiers (e.g. Streamlit Community
  Cloud) reset local files on restart, so `feedback.csv` and audio cache may
  be lost between sessions.
- **Language accuracy**: Tamil and Hindi text should be reviewed by a native
  speaker before use in the field.
- **Disclaimer**: all outputs are estimates, not financial advice.
