"""
clean_data.py — AgriSecure AI  Data Preparation
================================================

PURPOSE
-------
This script cleans and standardises raw government datasets into the three CSV
files consumed by the AgriSecure AI app.

WARNING: No placeholder fallback
---------------------------------
This script requires all three raw files to be present in data/raw/.  If any
file is missing it exits immediately with a clear error listing the missing
files and the download instructions.  There is no placeholder fallback —
placeholder CSVs hide data quality problems and must never reach production.

OUTPUT SCHEMA
-------------
Every output CSV includes source_url and retrieved_date on every row.
A blank source_url or retrieved_date is an error in scripts/check_data.py.

  data/cost.csv
    state, season, crop, year, seed, fertilizer, labour, irrigation,
    other, note, source_url, retrieved_date

  data/yield_price.csv
    state, season, crop, year, yield_quintal_per_acre, price_per_quintal,
    note, source_url, retrieved_date

  data/msp.csv
    crop, year, msp_per_quintal, note, source_url, retrieved_date

=============================================================================
FILES YOU MUST DOWNLOAD MANUALLY
=============================================================================

1. COST OF CULTIVATION — data/raw/cost_raw.csv
   Source : https://eands.dacnet.nic.in/Cost_of_Cultivation.htm
   Org    : Directorate of Economics and Statistics (DES), MoAFW, GoI
   Note   : Costs are in ₹/hectare — divide by 2.47105 for ₹/acre.
            Use A2+FL cost basis (paid-out costs including family labour).
            Document the choice in docs/assumptions.md.

2. YIELD & PRICE — data/raw/yield_price_raw.csv
   Sources:
     (a) TN Season and Crop Report — yield in kg/ha; convert to q/acre.
         https://www.tn.gov.in/tnportal/dept/agri/crop_report
     (b) Agmarknet wholesale prices (modal, Sep–Oct arrival month).
         https://agmarknet.gov.in
   Note   : yield_quintal_per_acre = (kg_ha / 100) / 2.47105

3. MSP — data/raw/msp_raw.csv
   Source : https://cacp.dacnet.nic.in
   Org    : Commission for Agricultural Costs and Prices (CACP), GoI

=============================================================================
HOW TO USE
=============================================================================

Step 1 — Place the three raw files in data/raw/:
           cost_raw.csv, yield_price_raw.csv, msp_raw.csv

Step 2 — Edit the COLUMN MAPPING sections in clean_cost(), clean_yield_price()
         and clean_msp() to match the actual column names in each file.

Step 3 — Run:  python3 data/clean_data.py

Step 4 — Run:  python3 scripts/check_data.py
         Fix every ERROR before committing the CSVs.

Step 5 — Run:  pytest
=============================================================================
"""

import os
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(_HERE, "raw")

COST_RAW        = os.path.join(RAW_DIR, "cost_raw.csv")
YIELD_PRICE_RAW = os.path.join(RAW_DIR, "yield_price_raw.csv")
MSP_RAW         = os.path.join(RAW_DIR, "msp_raw.csv")

COST_OUT        = os.path.join(_HERE, "cost.csv")
YIELD_PRICE_OUT = os.path.join(_HERE, "yield_price.csv")
MSP_OUT         = os.path.join(_HERE, "msp.csv")

# Tag for any row whose value is estimated or unverified.
# Must match config.py and scripts/check_data.py exactly.
PLACEHOLDER_TAG = "PLACEHOLDER – verify"

# ---------------------------------------------------------------------------
# Provenance helpers
# ---------------------------------------------------------------------------

def _add_provenance(df: pd.DataFrame, source_url: str, retrieved_date: str) -> pd.DataFrame:
    """Attach source_url and retrieved_date to every row.

    Both are required columns in the output schema.  scripts/check_data.py
    will error on any row where either column is blank.
    """
    df = df.copy()
    df["source_url"]     = source_url
    df["retrieved_date"] = retrieved_date
    return df


# ---------------------------------------------------------------------------
# Cleaning functions
# ---------------------------------------------------------------------------

def clean_cost(raw_path: str, source_url: str, retrieved_date: str) -> pd.DataFrame:
    """Clean cost_raw.csv → cost.csv schema.

    Returns a DataFrame with columns:
        state, season, crop, year, seed, fertilizer, labour,
        irrigation, other, note, source_url, retrieved_date

    Parameters
    ----------
    raw_path : str
        Path to the raw cost CSV.
    source_url : str
        The authoritative URL this file was downloaded from.
    retrieved_date : str
        ISO-8601 date the file was downloaded, e.g. "2025-10-01".
    """
    df = pd.read_csv(raw_path)

    # ------------------------------------------------------------------
    # EDIT THIS SECTION to match actual column names in cost_raw.csv
    # ------------------------------------------------------------------
    # df = df.rename(columns={
    #     "State_Name":   "state",
    #     "Season":       "season",
    #     "Crop_Name":    "crop",
    #     "Year":         "year",
    #     "Seed_Cost":    "seed",        # ₹/acre (divide ₹/ha by 2.47105)
    #     "Fert_Cost":    "fertilizer",
    #     "Labour_Cost":  "labour",
    #     "Irrigation":   "irrigation",
    #     "Other_Cost":   "other",
    # })
    # ------------------------------------------------------------------

    if "season" in df.columns:
        df["season"] = df["season"].str.strip()
    if "crop" in df.columns:
        df["crop"] = df["crop"].str.strip().str.lower()
    if "note" not in df.columns:
        df["note"] = ""

    required = ["state", "season", "crop", "year",
                "seed", "fertilizer", "labour", "irrigation", "other"]
    _check_columns(df, required, raw_path)

    for col in ["seed", "fertilizer", "labour", "irrigation", "other"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[required + ["note"]]
    return _add_provenance(df, source_url, retrieved_date)


def clean_yield_price(raw_path: str, source_url: str, retrieved_date: str) -> pd.DataFrame:
    """Clean yield_price_raw.csv → yield_price.csv schema.

    Returns a DataFrame with columns:
        state, season, crop, year, yield_quintal_per_acre,
        price_per_quintal, note, source_url, retrieved_date
    """
    df = pd.read_csv(raw_path)

    # ------------------------------------------------------------------
    # EDIT THIS SECTION to match actual column names in yield_price_raw.csv
    # ------------------------------------------------------------------
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

    df = df[required + ["note"]]
    return _add_provenance(df, source_url, retrieved_date)


def clean_msp(raw_path: str, source_url: str, retrieved_date: str) -> pd.DataFrame:
    """Clean msp_raw.csv → msp.csv schema.

    Returns a DataFrame with columns:
        crop, year, msp_per_quintal, note, source_url, retrieved_date

    If the raw file already carries ``source_url`` and ``retrieved_date``
    columns (per-row provenance), those values are used directly and the
    *source_url* / *retrieved_date* parameters are ignored.  This allows
    different MSP years to cite different official sources.

    If the columns are absent, *source_url* and *retrieved_date* are applied
    uniformly to every row via ``_add_provenance``.
    """
    df = pd.read_csv(raw_path)

    # ------------------------------------------------------------------
    # EDIT THIS SECTION to match actual column names in msp_raw.csv
    # ------------------------------------------------------------------
    # df = df.rename(columns={
    #     "Crop":        "crop",
    #     "Year":        "year",
    #     "MSP_Quintal": "msp_per_quintal",
    # })
    # ------------------------------------------------------------------

    if "crop" in df.columns:
        df["crop"] = df["crop"].str.strip().str.lower()
    if "note" not in df.columns:
        df["note"] = ""

    required = ["crop", "year", "msp_per_quintal"]
    _check_columns(df, required, raw_path)

    df["msp_per_quintal"] = pd.to_numeric(df["msp_per_quintal"], errors="coerce")

    # Preserve per-row provenance when present; fall back to uniform values.
    has_per_row_provenance = (
        "source_url" in df.columns and "retrieved_date" in df.columns
    )
    base_cols = required + ["note"]
    if has_per_row_provenance:
        df = df[base_cols + ["source_url", "retrieved_date"]].copy()
    else:
        df = df[base_cols]
        df = _add_provenance(df, source_url, retrieved_date)

    return df


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _check_columns(df: pd.DataFrame, required: list, source: str) -> None:
    """Raise ValueError if any required column is missing."""
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

# Default provenance values — edit these to match your actual download sources
# before running this script.
_COST_SOURCE_URL        = "https://eands.dacnet.nic.in/Cost_of_Cultivation.htm"
_YIELD_PRICE_SOURCE_URL = "https://www.tn.gov.in/tnportal/dept/agri/crop_report"
_MSP_SOURCE_URL         = "https://cacp.dacnet.nic.in"
_RETRIEVED_DATE         = "2025-10-01"   # update to today's date when you re-download


def main() -> None:
    """Clean raw files and write output CSVs.

    Exits with a non-zero code and a clear message if any raw file is missing.
    There is no placeholder fallback.
    """
    raw_files = {
        "cost":        COST_RAW,
        "yield_price": YIELD_PRICE_RAW,
        "msp":         MSP_RAW,
    }

    missing = [name for name, path in raw_files.items() if not os.path.exists(path)]

    if missing:
        print("\n❌  Raw data files not found — cannot proceed:\n")
        for name in missing:
            print(f"    • data/raw/{name}_raw.csv")
        print(
            "\nDownload the files from the sources listed in the module docstring,\n"
            "place them in data/raw/ with the exact names above, then re-run:\n"
            "    python3 data/clean_data.py\n"
        )
        sys.exit(1)

    print("\n  Cleaning data …\n")

    df_cost = clean_cost(COST_RAW, _COST_SOURCE_URL, _RETRIEVED_DATE)
    df_cost.to_csv(COST_OUT, index=False)
    print(f"  ✓ Written {COST_OUT}  ({len(df_cost)} rows)")

    df_yp = clean_yield_price(YIELD_PRICE_RAW, _YIELD_PRICE_SOURCE_URL, _RETRIEVED_DATE)
    df_yp.to_csv(YIELD_PRICE_OUT, index=False)
    print(f"  ✓ Written {YIELD_PRICE_OUT}  ({len(df_yp)} rows)")

    df_msp = clean_msp(MSP_RAW, _MSP_SOURCE_URL, _RETRIEVED_DATE)
    df_msp.to_csv(MSP_OUT, index=False)
    print(f"  ✓ Written {MSP_OUT}  ({len(df_msp)} rows)")

    print(
        "\n  Done.  Run scripts/check_data.py to validate before committing.\n"
    )


if __name__ == "__main__":
    main()
