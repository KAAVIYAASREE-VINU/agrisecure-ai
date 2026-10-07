#!/usr/bin/env python3
"""
scripts/check_data.py — AgriSecure AI data validator

Checks (all are hard errors unless noted):
  - Required columns present in all three CSVs
    (includes source_url and retrieved_date)
  - No negative yields or cost components
  - No nulls in numeric columns
  - Every crop in yield_price and cost has at least one MSP row
  - source_url is present, non-blank, and does not contain "placeholder"
  - retrieved_date is present and non-blank

Prints: file, row (1-based), column name for every problem.
Exits non-zero on any ERROR.

Usage (from project root):
    python3 scripts/check_data.py
"""

import os, sys
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COST_CSV        = os.path.join(_ROOT, "data", "cost.csv")
YIELD_PRICE_CSV = os.path.join(_ROOT, "data", "yield_price.csv")
MSP_CSV         = os.path.join(_ROOT, "data", "msp.csv")

# Required columns now include provenance columns.
COST_REQUIRED  = ["state", "season", "crop", "year",
                  "seed", "fertilizer", "labour", "irrigation", "other",
                  "note", "source_url", "retrieved_date"]
YP_REQUIRED    = ["state", "season", "crop", "year",
                  "yield_quintal_per_acre", "price_per_quintal",
                  "note", "source_url", "retrieved_date"]
MSP_REQUIRED   = ["crop", "year", "msp_per_quintal",
                  "note", "source_url", "retrieved_date"]

COST_NUMERIC   = ["seed", "fertilizer", "labour", "irrigation", "other"]
YP_NUMERIC     = ["yield_quintal_per_acre", "price_per_quintal"]
MSP_NUMERIC    = ["msp_per_quintal"]

errors   = []
warnings = []


def _check_required(df, required, path):
    for col in required:
        if col not in df.columns:
            errors.append(f"{path}: missing required column '{col}'")


def _check_non_negative(df, cols, path):
    for col in cols:
        if col not in df.columns:
            continue
        for idx in df.index[df[col] < 0]:
            errors.append(
                f"{path}: row {idx+2}, column '{col}' = {df.at[idx,col]} (negative)"
            )


def _check_no_nulls(df, cols, path):
    for col in cols:
        if col not in df.columns:
            continue
        for idx in df.index[df[col].isna()]:
            errors.append(f"{path}: row {idx+2}, column '{col}' is null")


def _check_provenance(df, path):
    """Every row must have a non-blank source_url that is not a placeholder,
    and a non-blank retrieved_date.  Both are hard errors.
    """
    for col in ("source_url", "retrieved_date"):
        if col not in df.columns:
            errors.append(f"{path}: missing required column '{col}'")
            continue
        blank_mask = df[col].fillna("").str.strip() == ""
        for idx in df.index[blank_mask]:
            errors.append(
                f"{path}: row {idx+2}, column '{col}' is blank "
                f"(every row must have a real source)"
            )

    if "source_url" not in df.columns:
        return

    # Any source_url that contains the word "placeholder" (case-insensitive)
    # means the data has not been verified — that is an error, not a warning.
    placeholder_mask = (
        df["source_url"]
        .fillna("")
        .str.lower()
        .str.contains("placeholder", na=False)
    )
    for idx in df.index[placeholder_mask]:
        val = df.at[idx, "source_url"]
        errors.append(
            f"{path}: row {idx+2}, source_url contains 'placeholder': '{val}' "
            f"— replace with the real URL before committing"
        )


def main():
    print("AgriSecure AI — data validator\n")
    for p in [COST_CSV, YIELD_PRICE_CSV, MSP_CSV]:
        if not os.path.exists(p):
            errors.append(f"File not found: {p}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    cost_df = pd.read_csv(COST_CSV)
    yp_df   = pd.read_csv(YIELD_PRICE_CSV)
    msp_df  = pd.read_csv(MSP_CSV)

    _check_required(cost_df, COST_REQUIRED, COST_CSV)
    _check_required(yp_df,   YP_REQUIRED,   YIELD_PRICE_CSV)
    _check_required(msp_df,  MSP_REQUIRED,  MSP_CSV)

    _check_non_negative(cost_df, COST_NUMERIC, COST_CSV)
    _check_non_negative(yp_df,   YP_NUMERIC,   YIELD_PRICE_CSV)
    _check_non_negative(msp_df,  MSP_NUMERIC,  MSP_CSV)

    _check_no_nulls(cost_df, COST_NUMERIC, COST_CSV)
    _check_no_nulls(yp_df,   YP_NUMERIC,   YIELD_PRICE_CSV)
    _check_no_nulls(msp_df,  MSP_NUMERIC,  MSP_CSV)

    _check_provenance(cost_df, COST_CSV)
    _check_provenance(yp_df,   YIELD_PRICE_CSV)
    _check_provenance(msp_df,  MSP_CSV)

    yp_crops   = set(yp_df["crop"].str.lower().unique())   if "crop" in yp_df.columns   else set()
    cost_crops = set(cost_df["crop"].str.lower().unique()) if "crop" in cost_df.columns else set()
    msp_crops  = set(msp_df["crop"].str.lower().unique())  if "crop" in msp_df.columns  else set()

    for crop in sorted((yp_crops | cost_crops) - msp_crops):
        errors.append(
            f"{MSP_CSV}: crop '{crop}' in yield_price/cost but no MSP row"
        )

    if warnings:
        print("INFO (not failures):")
        for w in warnings:
            print(f"  {w}")
        print()

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  {e}")
        print(f"\n{len(errors)} error(s). Fix before use.")
        return 1

    print(f"All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
