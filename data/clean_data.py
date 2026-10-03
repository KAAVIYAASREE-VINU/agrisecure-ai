"""
clean_data.py — AgriSecure AI  Data Preparation
================================================

PURPOSE
-------
This script cleans and standardises raw government datasets into the three CSV
files consumed by the AgriSecure AI app.  It also generates minimal placeholder
CSVs so the app can start and be tested before real data is downloaded.

WARNING
-------
Until the real source files are downloaded and placed in ``data/raw/``, running
this script generates PLACEHOLDER values only.  Every placeholder row is tagged
``PLACEHOLDER – verify`` in the ``note`` column.  NEVER present placeholder
values to end users as real figures.

=============================================================================
FILES YOU MUST DOWNLOAD MANUALLY
=============================================================================

1. COST OF CULTIVATION DATA
---------------------------
  Save as        : data/raw/cost_raw.csv   (or .xlsx — convert to CSV first)
  Dataset name   : Cost of Cultivation / Production of Principal Crops in India
  Description    : State- and crop-wise cultivation cost broken down into A2,
                   A2+FL, B1, B2, C1, C2 cost components per acre / hectare.
  Source URL     : https://eands.dacnet.nic.in/Cost_of_Cultivation.htm
                   (PLACEHOLDER – verify: page layout and file names change
                   periodically; check the "Cost of Cultivation" section of the
                   Directorate of Economics and Statistics, MoAFW portal)
  Organisation   : Directorate of Economics and Statistics (DES), Ministry of
                   Agriculture & Farmers Welfare, Government of India
  Year / release : Latest available triennium (typically 2018-19 to 2020-21);
                   PLACEHOLDER – verify year on download page
  Format         : XLS / XLSX (convert to CSV after download)
  Key columns
  needed         : State, Crop, Season/Year, Seed cost (₹/acre or ₹/ha),
                   Fertiliser & manure cost, Human labour cost, Irrigation
                   charges, Other costs.  Map to schema below.
  Access notes   : Free to download; no registration required.  Files are
                   sometimes split by crop group — download all relevant files
                   and concatenate before cleaning.

  Expected output schema after cleaning (→ data/cost.csv):
    state, season, crop, year, seed, fertilizer, labour, irrigation, other, note

  Mapping guide:
    • Costs are typically in ₹/hectare — divide by 2.47105 to get ₹/acre.
    • Use "A2+FL" (paid-out costs including family labour) as the cost basis,
      or C2 if you want full economic cost.  Document the choice in
      docs/assumptions.md.
    • If a season column is absent, assign from known crop calendars and mark
      the note column "PLACEHOLDER – verify season".

-----------------------------------------------------------------------------

2. YIELD AND PRICE DATA
-----------------------
  Save as        : data/raw/yield_price_raw.csv
  Dataset name   : Crop-wise Area, Production and Yield Statistics (or
                   Agmarknet wholesale price arrivals data)
  Description    : Season- and state-wise crop yield per acre and average
                   wholesale price per quintal across multiple years.
  Source URLs    :
    (a) data.gov.in — search for "crop production statistics India"
        URL: https://data.gov.in  (use the search box; direct dataset URLs
        change — PLACEHOLDER – verify)
        Typical dataset: "District/State-wise Season and Crop Production
        Statistics" published by DES or ICAR.
    (b) Agmarknet — for wholesale price data
        URL: https://agmarknet.gov.in
        Navigate: Prices → State-wise → Download; select crop, state, year.
  Organisation   : data.gov.in (National Data & Analytics Platform, NIC) /
                   Agmarknet (Directorate of Marketing & Inspection, MoAFW)
  Year / release : Aim for at least 5 years (e.g. 2018-19 to 2022-23) to get
                   meaningful CV and percentile calculations; PLACEHOLDER –
                   verify available years on download
  Format         : CSV (data.gov.in); CSV / XLS (Agmarknet)
  Key columns
  needed         : State, Season, Crop, Year, Production (tonnes or quintals),
                   Area (hectares or acres), Price per quintal.
                   Compute yield_quintal_per_acre = production / area (after
                   unit conversion).
  Access notes   : data.gov.in — free, no registration for most datasets;
                   Agmarknet — free, daily/monthly price downloads available.

  Expected output schema after cleaning (→ data/yield_price.csv):
    state, season, crop, year, yield_quintal_per_acre, price_per_quintal, note

  Mapping guide:
    • Convert area from hectares to acres (* 2.47105) and recalculate yield.
    • Average prices across all mandis in the state for the season, or take the
      modal arrival month price.  Document the choice in docs/assumptions.md.
    • Mark any interpolated or state-average estimate as "PLACEHOLDER – verify"
      in the note column.

-----------------------------------------------------------------------------

3. MINIMUM SUPPORT PRICE (MSP) DATA
-------------------------------------
  Save as        : data/raw/msp_raw.csv
  Dataset name   : MSP for Kharif and Rabi Crops
  Description    : Annual Minimum Support Price (₹ per quintal) announced by
                   the Government of India for major crops.
  Source URL     : https://cacp.dacnet.nic.in/ViewContents.aspx?Input=1&PageId=36&KeyId=0
                   (PLACEHOLDER – verify: CACP pages are occasionally
                   restructured; also available from the CACP annual report PDFs
                   at https://cacp.dacnet.nic.in)
                   Also mirrored at: https://agricoop.nic.in  and  data.gov.in
                   (search "MSP crops India")
  Organisation   : Commission for Agricultural Costs and Prices (CACP),
                   Ministry of Agriculture & Farmers Welfare, GoI
  Year / release : 2019-20 to 2024-25 (latest available); PLACEHOLDER – verify
  Format         : PDF tables (copy to CSV) or XLS download where available
  Key columns
  needed         : Crop name, Year/Season, MSP (₹ per quintal)
  Access notes   : Free to download.  MSP tables are usually published as PDF
                   annexures in the "Price Policy" reports — use a PDF-to-CSV
                   tool or copy-paste the table.  Some years are available as
                   XLS on data.gov.in.

  Expected output schema after cleaning (→ data/msp.csv):
    crop, year, msp_per_quintal, note

=============================================================================
OUTPUT FILES PRODUCED BY THIS SCRIPT
=============================================================================

  data/cost.csv
    Schema : state, season, crop, year, seed, fertilizer, labour,
             irrigation, other, note
    Source : data/raw/cost_raw.csv  (after cleaning)

  data/yield_price.csv
    Schema : state, season, crop, year, yield_quintal_per_acre,
             price_per_quintal, note
    Source : data/raw/yield_price_raw.csv  (after cleaning)

  data/msp.csv
    Schema : crop, year, msp_per_quintal, note
    Source : data/raw/msp_raw.csv  (after cleaning)

=============================================================================
HOW TO USE
=============================================================================

Step 1 — Download the raw files listed above and place them in data/raw/.
         Rename them exactly as shown ("cost_raw.csv", "yield_price_raw.csv",
         "msp_raw.csv").

Step 2 — Review the COLUMN MAPPING sections above and edit the cleaning
         functions below (clean_cost, clean_yield_price, clean_msp) to match
         the actual column names in the downloaded files.

Step 3 — From the project root, run:
             python3 data/clean_data.py
         The script detects whether raw files are present.  If they are, it
         cleans and writes the output CSVs.  If not, it writes placeholder CSVs
         so the app can start.

Step 4 — Open each output CSV and verify a sample of rows look sensible.

Step 5 — Remove or update any rows tagged "PLACEHOLDER – verify" once you
         have confirmed real values.

Step 6 — Run pytest from the project root to confirm validation passes:
             pytest tests/

=============================================================================
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(_HERE, "raw")

COST_RAW = os.path.join(RAW_DIR, "cost_raw.csv")
YIELD_PRICE_RAW = os.path.join(RAW_DIR, "yield_price_raw.csv")
MSP_RAW = os.path.join(RAW_DIR, "msp_raw.csv")

COST_OUT = os.path.join(_HERE, "cost.csv")
YIELD_PRICE_OUT = os.path.join(_HERE, "yield_price.csv")
MSP_OUT = os.path.join(_HERE, "msp.csv")

# Tag applied to every row that carries an estimated / unverified value.
PLACEHOLDER_TAG = "PLACEHOLDER – verify"


# ---------------------------------------------------------------------------
# Cleaning functions (edit column names here once real files are available)
# ---------------------------------------------------------------------------

def clean_cost(raw_path: str) -> pd.DataFrame:
    """
    Read *raw_path* (cost of cultivation CSV) and return a cleaned DataFrame
    with columns: state, season, crop, year, seed, fertilizer, labour,
    irrigation, other, note.

    Edit the column-name mapping inside this function to match the actual
    downloaded file.  All cost values must be in ₹ per acre.
    """
    df = pd.read_csv(raw_path)

    # ------------------------------------------------------------------
    # EDIT THIS SECTION to match actual column names in cost_raw.csv
    # ------------------------------------------------------------------
    # Example mapping (adjust as needed):
    # df = df.rename(columns={
    #     "State_Name":   "state",
    #     "Season":       "season",
    #     "Crop_Name":    "crop",
    #     "Year":         "year",
    #     "Seed_Cost":    "seed",        # ₹/acre (convert from ₹/ha if needed)
    #     "Fert_Cost":    "fertilizer",
    #     "Labour_Cost":  "labour",
    #     "Irrigation":   "irrigation",
    #     "Other_Cost":   "other",
    # })
    # ------------------------------------------------------------------

    # Strip whitespace from Season (Requirement 2.6 / 19.4)
    if "season" in df.columns:
        df["season"] = df["season"].str.strip()

    # Standardise crop names to lowercase
    if "crop" in df.columns:
        df["crop"] = df["crop"].str.strip().str.lower()

    # Ensure a note column exists
    if "note" not in df.columns:
        df["note"] = ""

    required = ["state", "season", "crop", "year",
                "seed", "fertilizer", "labour", "irrigation", "other"]
    _check_columns(df, required, raw_path)

    numeric_cols = ["seed", "fertilizer", "labour", "irrigation", "other"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[required + ["note"]]


def clean_yield_price(raw_path: str) -> pd.DataFrame:
    """
    Read *raw_path* and return a cleaned DataFrame with columns:
    state, season, crop, year, yield_quintal_per_acre, price_per_quintal, note.

    Edit the column-name mapping to match the downloaded file.
    """
    df = pd.read_csv(raw_path)

    # ------------------------------------------------------------------
    # EDIT THIS SECTION to match actual column names in yield_price_raw.csv
    # ------------------------------------------------------------------
    # Example mapping:
    # df = df.rename(columns={
    #     "State":                   "state",
    #     "Season":                  "season",
    #     "Crop":                    "crop",
    #     "Year":                    "year",
    #     "Yield_Quintal_Per_Acre":  "yield_quintal_per_acre",
    #     "Price_Per_Quintal":       "price_per_quintal",
    # })
    # ------------------------------------------------------------------

    if "season" in df.columns:
        df["season"] = df["season"].str.strip()
    if "crop" in df.columns:
        df["crop"] = df["crop"].str.strip().str.lower()
    if "note" not in df.columns:
        df["note"] = ""

    required = ["state", "season", "crop", "year",
                "yield_quintal_per_acre", "price_per_quintal"]
    _check_columns(df, required, raw_path)

    for col in ["yield_quintal_per_acre", "price_per_quintal"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[required + ["note"]]


def clean_msp(raw_path: str) -> pd.DataFrame:
    """
    Read *raw_path* and return a cleaned DataFrame with columns:
    crop, year, msp_per_quintal, note.
    """
    df = pd.read_csv(raw_path)

    # ------------------------------------------------------------------
    # EDIT THIS SECTION to match actual column names in msp_raw.csv
    # ------------------------------------------------------------------
    # Example mapping:
    # df = df.rename(columns={
    #     "Crop":           "crop",
    #     "Year":           "year",
    #     "MSP_Quintal":    "msp_per_quintal",
    # })
    # ------------------------------------------------------------------

    if "crop" in df.columns:
        df["crop"] = df["crop"].str.strip().str.lower()
    if "note" not in df.columns:
        df["note"] = ""

    required = ["crop", "year", "msp_per_quintal"]
    _check_columns(df, required, raw_path)

    df["msp_per_quintal"] = pd.to_numeric(df["msp_per_quintal"], errors="coerce")

    return df[required + ["note"]]


# ---------------------------------------------------------------------------
# Placeholder generation (used when raw files are absent)
# ---------------------------------------------------------------------------

def generate_placeholders() -> None:
    """
    Write placeholder CSVs to data/ so the app can start and be tested
    before real data is downloaded.

    Every row carries ``PLACEHOLDER – verify`` in the ``note`` column.
    Values are rough illustrative figures for Tamil Nadu crops only —
    DO NOT use them for any financial advice.

    Row counts are chosen so that profit_scenarios (which requires >= 4
    rows per state/season/crop) has enough data: paddy/Kuruvai/Tamil Nadu
    has 5 years of data (2018–2022).
    """
    _ensure_raw_dir()

    # ------------------------------------------------------------------ #
    # cost.csv  — ₹ per acre, illustrative figures for Tamil Nadu        #
    # 10 rows: paddy/Kuruvai 2018–2022 (5 rows), maize/Kuruvai 2020–2022 #
    # (3 rows), groundnut/Rabi 2020–2022 (2 rows)                        #
    # ------------------------------------------------------------------ #
    cost_rows = [
        # state,        season,    crop,        year,  seed,  fert,  labour, irrig, other
        # paddy – Kuruvai – Tamil Nadu (5 years, slight year-on-year cost growth)
        ("Tamil Nadu", "Kuruvai", "paddy",      2018,  1350,  3100,  5500,  2200,   900),
        ("Tamil Nadu", "Kuruvai", "paddy",      2019,  1380,  3200,  5700,  2300,   930),
        ("Tamil Nadu", "Kuruvai", "paddy",      2020,  1420,  3350,  5850,  2400,   960),
        ("Tamil Nadu", "Kuruvai", "paddy",      2021,  1460,  3450,  5950,  2450,   980),
        ("Tamil Nadu", "Kuruvai", "paddy",      2022,  1500,  3500,  6000,  2500,  1000),
        # maize – Kuruvai – Tamil Nadu (3 years)
        ("Tamil Nadu", "Kuruvai", "maize",      2020,  1150,  2850,  4300,  1700,   850),
        ("Tamil Nadu", "Kuruvai", "maize",      2021,  1180,  2950,  4400,  1750,   870),
        ("Tamil Nadu", "Kuruvai", "maize",      2022,  1200,  3000,  4500,  1800,   900),
        # groundnut – Rabi – Tamil Nadu (2 rows — not enough for percentiles; PLACEHOLDER)
        ("Tamil Nadu", "Rabi",    "groundnut",  2021,  1950,  2400,  4900,  1950,   780),
        ("Tamil Nadu", "Rabi",    "groundnut",  2022,  2000,  2500,  5000,  2000,   800),
    ]
    cost_df = pd.DataFrame(
        cost_rows,
        columns=["state", "season", "crop", "year",
                 "seed", "fertilizer", "labour", "irrigation", "other"],
    )
    # Strip whitespace from Season (Requirement 2.6) and normalise crop names
    cost_df["season"] = cost_df["season"].str.strip()
    cost_df["crop"] = cost_df["crop"].str.strip().str.lower()
    cost_df["note"] = PLACEHOLDER_TAG
    cost_df.to_csv(COST_OUT, index=False)
    print(f"  ✓ Written {COST_OUT}  ({len(cost_df)} placeholder rows)")

    # ------------------------------------------------------------------ #
    # yield_price.csv — illustrative figures matching cost rows          #
    # 10 rows with realistic year-on-year variation                      #
    # ------------------------------------------------------------------ #
    yp_rows = [
        # state,        season,    crop,        year,  yield_q_ac,  price_q
        # paddy – Kuruvai – Tamil Nadu (5 years)
        ("Tamil Nadu", "Kuruvai", "paddy",      2018,  14.0,        1720.0),
        ("Tamil Nadu", "Kuruvai", "paddy",      2019,  15.5,        1780.0),
        ("Tamil Nadu", "Kuruvai", "paddy",      2020,  16.0,        1840.0),
        ("Tamil Nadu", "Kuruvai", "paddy",      2021,  15.0,        1950.0),
        ("Tamil Nadu", "Kuruvai", "paddy",      2022,  17.5,        2050.0),
        # maize – Kuruvai – Tamil Nadu (3 years)
        ("Tamil Nadu", "Kuruvai", "maize",      2020,  12.0,        1360.0),
        ("Tamil Nadu", "Kuruvai", "maize",      2021,  14.5,        1420.0),
        ("Tamil Nadu", "Kuruvai", "maize",      2022,  15.5,        1480.0),
        # groundnut – Rabi – Tamil Nadu (2 rows)
        ("Tamil Nadu", "Rabi",    "groundnut",  2021,   9.0,        4850.0),
        ("Tamil Nadu", "Rabi",    "groundnut",  2022,  10.5,        5050.0),
    ]
    yp_df = pd.DataFrame(
        yp_rows,
        columns=["state", "season", "crop", "year",
                 "yield_quintal_per_acre", "price_per_quintal"],
    )
    # Strip whitespace from Season (Requirement 2.6) and normalise crop names
    yp_df["season"] = yp_df["season"].str.strip()
    yp_df["crop"] = yp_df["crop"].str.strip().str.lower()
    yp_df["note"] = PLACEHOLDER_TAG
    yp_df.to_csv(YIELD_PRICE_OUT, index=False)
    print(f"  ✓ Written {YIELD_PRICE_OUT}  ({len(yp_df)} placeholder rows)")

    # ------------------------------------------------------------------ #
    # msp.csv — 8 rows                                                   #
    # paddy 2018–2022 (5 rows), maize 2020–2022 (3 rows),               #
    # groundnut 2020–2022 (2 rows — included but limited)                #
    # Source: CACP MSP tables; PLACEHOLDER – verify exact figures        #
    # ------------------------------------------------------------------ #
    msp_rows = [
        # crop,        year,   msp_q
        # paddy MSP — approximate CACP announced figures
        ("paddy",      2018,   1750.0),
        ("paddy",      2019,   1815.0),
        ("paddy",      2020,   1868.0),
        ("paddy",      2021,   1940.0),
        ("paddy",      2022,   2015.0),
        # maize MSP
        ("maize",      2020,   1700.0),
        ("maize",      2021,   1870.0),
        ("maize",      2022,   1962.0),
        # groundnut MSP
        ("groundnut",  2021,   5275.0),
        ("groundnut",  2022,   5550.0),
    ]
    msp_df = pd.DataFrame(msp_rows, columns=["crop", "year", "msp_per_quintal"])
    # Normalise crop names
    msp_df["crop"] = msp_df["crop"].str.strip().str.lower()
    msp_df["note"] = PLACEHOLDER_TAG
    msp_df.to_csv(MSP_OUT, index=False)
    print(f"  ✓ Written {MSP_OUT}  ({len(msp_df)} placeholder rows)")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _ensure_raw_dir() -> None:
    """Create data/raw/ if it does not exist."""
    os.makedirs(RAW_DIR, exist_ok=True)


def _check_columns(df: pd.DataFrame, required: list, source: str) -> None:
    """Raise ValueError if any required column is missing after renaming."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"File '{source}' is missing required columns after mapping: "
            f"{missing}.  Edit the rename block in the relevant clean_* "
            f"function in data/clean_data.py to fix the mapping."
        )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    If all three raw files are present, clean them and write output CSVs.
    Otherwise, write placeholder CSVs and print download instructions.
    """
    raw_files = {
        "cost":        COST_RAW,
        "yield_price": YIELD_PRICE_RAW,
        "msp":         MSP_RAW,
    }

    missing = [name for name, path in raw_files.items() if not os.path.exists(path)]

    if missing:
        print(
            "\n⚠️  Raw data files not found:"
        )
        for name in missing:
            print(f"    • data/raw/{name}_raw.csv")
        print(
            "\n  Generating PLACEHOLDER CSVs instead.\n"
            "  See the module docstring in data/clean_data.py for download\n"
            "  instructions, then re-run this script with the real files.\n"
        )
        generate_placeholders()
    else:
        print("\n  Real raw files found — cleaning data …\n")
        clean_cost(COST_RAW).to_csv(COST_OUT, index=False)
        print(f"  ✓ Written {COST_OUT}")

        clean_yield_price(YIELD_PRICE_RAW).to_csv(YIELD_PRICE_OUT, index=False)
        print(f"  ✓ Written {YIELD_PRICE_OUT}")

        clean_msp(MSP_RAW).to_csv(MSP_OUT, index=False)
        print(f"  ✓ Written {MSP_OUT}")

    print("\n  Done.  Remember to review note columns for PLACEHOLDER rows.\n")


if __name__ == "__main__":
    main()
