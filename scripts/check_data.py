#!/usr/bin/env python3
"""
scripts/check_data.py — AgriSecure AI data validator

Checks:
  - Required columns present in all three CSVs
  - No negative yields or cost components
  - No nulls in numeric columns
  - Every crop in yield_price and cost has at least one MSP row
  - source_url blank rows printed as INFO (not failure)

Prints: file, row (1-based header offset), column name for each problem.
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

COST_REQUIRED  = ["state","season","crop","year","seed","fertilizer","labour","irrigation","other","note"]
YP_REQUIRED    = ["state","season","crop","year","yield_quintal_per_acre","price_per_quintal","note"]
MSP_REQUIRED   = ["crop","year","msp_per_quintal","note"]
COST_NUMERIC   = ["seed","fertilizer","labour","irrigation","other"]
YP_NUMERIC     = ["yield_quintal_per_acre","price_per_quintal"]
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
            errors.append(f"{path}: row {idx+2}, column '{col}' = {df.at[idx,col]} (negative)")


def _check_no_nulls(df, cols, path):
    for col in cols:
        if col not in df.columns:
            continue
        for idx in df.index[df[col].isna()]:
            errors.append(f"{path}: row {idx+2}, column '{col}' is null")


def _check_source_url(df, path):
    if "source_url" not in df.columns:
        warnings.append(f"{path}: column 'source_url' missing")
        return
    n = (df["source_url"].fillna("").str.strip() == "").sum()
    if n:
        warnings.append(f"{path}: {n} row(s) have blank source_url (PLACEHOLDER – verify)")


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

    yp_crops   = set(yp_df["crop"].str.lower().unique())   if "crop" in yp_df.columns   else set()
    cost_crops = set(cost_df["crop"].str.lower().unique()) if "crop" in cost_df.columns else set()
    msp_crops  = set(msp_df["crop"].str.lower().unique())  if "crop" in msp_df.columns  else set()

    for crop in sorted((yp_crops | cost_crops) - msp_crops):
        errors.append(f"{MSP_CSV}: crop '{crop}' in yield_price/cost but no MSP row")

    _check_source_url(cost_df, COST_CSV)
    _check_source_url(yp_df,   YIELD_PRICE_CSV)
    _check_source_url(msp_df,  MSP_CSV)

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

    print(f"All checks passed. ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
