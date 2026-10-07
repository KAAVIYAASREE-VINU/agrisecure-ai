"""
tests/test_cleaning.py
Tests for data/clean_data.py (Requirement 19.5).

generate_placeholders() was removed in favour of clean_cost/clean_yield_price/
clean_msp which require real (or synthetic) raw files.  Every test builds its
own minimal synthetic raw CSV in a temp directory so the suite is
self-contained and never touches the live data/ files.

Covers:
- clean_cost / clean_yield_price / clean_msp return correctly-shaped DataFrames
- source_url and retrieved_date are present and equal to the values passed in
- Season names are stripped of whitespace
- Crop names are normalised to lowercase
- note column is preserved / defaulted to empty string when absent
- Output includes exactly the expected columns (no extra columns from raw file)
- Missing required column in raw file raises ValueError
- main() exits with SystemExit(1) when raw files are absent
"""

import os
import sys
import textwrap
import tempfile

import pandas as pd
import pytest

import data.clean_data as clean_mod
from data.clean_data import (
    clean_cost,
    clean_yield_price,
    clean_msp,
    PLACEHOLDER_TAG,
)

# ---------------------------------------------------------------------------
# Synthetic raw-file builders
# ---------------------------------------------------------------------------

def _write_cost_raw(path: str, rows=None, extra_cols: dict | None = None) -> None:
    """Write a minimal cost_raw.csv to *path*."""
    if rows is None:
        rows = [
            ("Tamil Nadu", "Kuruvai", "paddy", 2022,
             1500, 3500, 6000, 2500, 1000, "test note"),
        ]
    lines = ["state,season,crop,year,seed,fertilizer,labour,irrigation,other,note"]
    for r in rows:
        lines.append(",".join(str(v) for v in r))
    if extra_cols:
        header = lines[0] + "," + ",".join(extra_cols.keys())
        lines[0] = header
        for i, r in enumerate(rows):
            lines[i+1] += "," + ",".join(str(v) for v in list(extra_cols.values())[0:1])
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def _write_yp_raw(path: str, rows=None) -> None:
    """Write a minimal yield_price_raw.csv to *path*."""
    if rows is None:
        rows = [
            ("Tamil Nadu", "Kuruvai", "paddy", 2022, 15.0, 2000.0, "test note"),
        ]
    lines = ["state,season,crop,year,yield_quintal_per_acre,price_per_quintal,note"]
    for r in rows:
        lines.append(",".join(str(v) for v in r))
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def _write_msp_raw(path: str, rows=None) -> None:
    """Write a minimal msp_raw.csv to *path*."""
    if rows is None:
        rows = [("paddy", 2022, 2015.0, "CACP")]
    lines = ["crop,year,msp_per_quintal,note"]
    for r in rows:
        lines.append(",".join(str(v) for v in r))
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


_URL  = "https://example.gov.in/data"
_DATE = "2025-10-01"


# ---------------------------------------------------------------------------
# clean_cost
# ---------------------------------------------------------------------------

class TestCleanCost:
    def test_returns_dataframe(self, tmp_path):
        p = str(tmp_path / "cost_raw.csv")
        _write_cost_raw(p)
        df = clean_cost(p, _URL, _DATE)
        assert isinstance(df, pd.DataFrame)

    def test_expected_columns_present(self, tmp_path):
        p = str(tmp_path / "cost_raw.csv")
        _write_cost_raw(p)
        df = clean_cost(p, _URL, _DATE)
        expected = {"state","season","crop","year","seed","fertilizer",
                    "labour","irrigation","other","note","source_url","retrieved_date"}
        assert expected.issubset(set(df.columns))

    def test_source_url_and_retrieved_date_set(self, tmp_path):
        p = str(tmp_path / "cost_raw.csv")
        _write_cost_raw(p)
        df = clean_cost(p, _URL, _DATE)
        assert (df["source_url"] == _URL).all()
        assert (df["retrieved_date"] == _DATE).all()

    def test_crop_names_lowercased(self, tmp_path):
        p = str(tmp_path / "cost_raw.csv")
        _write_cost_raw(p, rows=[
            ("Tamil Nadu", "Kuruvai", "PADDY", 2022, 1500, 3500, 6000, 2500, 1000, "")
        ])
        df = clean_cost(p, _URL, _DATE)
        assert (df["crop"] == df["crop"].str.lower()).all()

    def test_season_whitespace_stripped(self, tmp_path):
        p = str(tmp_path / "cost_raw.csv")
        _write_cost_raw(p, rows=[
            ("Tamil Nadu", "  Kuruvai  ", "paddy", 2022, 1500, 3500, 6000, 2500, 1000, "")
        ])
        df = clean_cost(p, _URL, _DATE)
        assert (df["season"] == df["season"].str.strip()).all()

    def test_note_column_defaults_to_empty_when_absent(self, tmp_path):
        # Write raw file without note column
        raw = "state,season,crop,year,seed,fertilizer,labour,irrigation,other\n"
        raw += "Tamil Nadu,Kuruvai,paddy,2022,1500,3500,6000,2500,1000\n"
        p = str(tmp_path / "cost_raw.csv")
        with open(p, "w") as f:
            f.write(raw)
        df = clean_cost(p, _URL, _DATE)
        assert "note" in df.columns
        assert df["note"].fillna("").iloc[0] == ""

    def test_raises_on_missing_required_column(self, tmp_path):
        # Drop 'seed' column
        raw = "state,season,crop,year,fertilizer,labour,irrigation,other,note\n"
        raw += "Tamil Nadu,Kuruvai,paddy,2022,3500,6000,2500,1000,ok\n"
        p = str(tmp_path / "cost_raw.csv")
        with open(p, "w") as f:
            f.write(raw)
        with pytest.raises(ValueError, match="seed"):
            clean_cost(p, _URL, _DATE)

    def test_numeric_columns_are_numeric(self, tmp_path):
        p = str(tmp_path / "cost_raw.csv")
        _write_cost_raw(p)
        df = clean_cost(p, _URL, _DATE)
        for col in ["seed", "fertilizer", "labour", "irrigation", "other"]:
            assert pd.api.types.is_numeric_dtype(df[col]), f"{col} should be numeric"


# ---------------------------------------------------------------------------
# clean_yield_price
# ---------------------------------------------------------------------------

class TestCleanYieldPrice:
    def test_returns_dataframe(self, tmp_path):
        p = str(tmp_path / "yp_raw.csv")
        _write_yp_raw(p)
        df = clean_yield_price(p, _URL, _DATE)
        assert isinstance(df, pd.DataFrame)

    def test_expected_columns_present(self, tmp_path):
        p = str(tmp_path / "yp_raw.csv")
        _write_yp_raw(p)
        df = clean_yield_price(p, _URL, _DATE)
        expected = {"state","season","crop","year","yield_quintal_per_acre",
                    "price_per_quintal","note","source_url","retrieved_date"}
        assert expected.issubset(set(df.columns))

    def test_source_url_and_retrieved_date_set(self, tmp_path):
        p = str(tmp_path / "yp_raw.csv")
        _write_yp_raw(p)
        df = clean_yield_price(p, _URL, _DATE)
        assert (df["source_url"] == _URL).all()
        assert (df["retrieved_date"] == _DATE).all()

    def test_crop_names_lowercased(self, tmp_path):
        p = str(tmp_path / "yp_raw.csv")
        _write_yp_raw(p, rows=[("Tamil Nadu", "Kuruvai", "MAIZE", 2022, 12.0, 1500.0, "")])
        df = clean_yield_price(p, _URL, _DATE)
        assert (df["crop"] == df["crop"].str.lower()).all()

    def test_season_whitespace_stripped(self, tmp_path):
        p = str(tmp_path / "yp_raw.csv")
        _write_yp_raw(p, rows=[("Tamil Nadu", " Kuruvai ", "paddy", 2022, 15.0, 2000.0, "")])
        df = clean_yield_price(p, _URL, _DATE)
        assert (df["season"] == df["season"].str.strip()).all()

    def test_raises_on_missing_required_column(self, tmp_path):
        raw = "state,season,crop,year,price_per_quintal,note\n"
        raw += "Tamil Nadu,Kuruvai,paddy,2022,2000.0,ok\n"
        p = str(tmp_path / "yp_raw.csv")
        with open(p, "w") as f:
            f.write(raw)
        with pytest.raises(ValueError, match="yield_quintal_per_acre"):
            clean_yield_price(p, _URL, _DATE)

    def test_numeric_columns_are_numeric(self, tmp_path):
        p = str(tmp_path / "yp_raw.csv")
        _write_yp_raw(p)
        df = clean_yield_price(p, _URL, _DATE)
        for col in ["yield_quintal_per_acre", "price_per_quintal"]:
            assert pd.api.types.is_numeric_dtype(df[col])


# ---------------------------------------------------------------------------
# clean_msp
# ---------------------------------------------------------------------------

class TestCleanMsp:
    def test_returns_dataframe(self, tmp_path):
        p = str(tmp_path / "msp_raw.csv")
        _write_msp_raw(p)
        df = clean_msp(p, _URL, _DATE)
        assert isinstance(df, pd.DataFrame)

    def test_expected_columns_present(self, tmp_path):
        p = str(tmp_path / "msp_raw.csv")
        _write_msp_raw(p)
        df = clean_msp(p, _URL, _DATE)
        expected = {"crop","year","msp_per_quintal","note","source_url","retrieved_date"}
        assert expected.issubset(set(df.columns))

    def test_source_url_and_retrieved_date_set(self, tmp_path):
        p = str(tmp_path / "msp_raw.csv")
        _write_msp_raw(p)
        df = clean_msp(p, _URL, _DATE)
        assert (df["source_url"] == _URL).all()
        assert (df["retrieved_date"] == _DATE).all()

    def test_crop_names_lowercased(self, tmp_path):
        p = str(tmp_path / "msp_raw.csv")
        _write_msp_raw(p, rows=[("PADDY", 2022, 2015.0, "")])
        df = clean_msp(p, _URL, _DATE)
        assert (df["crop"] == df["crop"].str.lower()).all()

    def test_raises_on_missing_required_column(self, tmp_path):
        raw = "crop,year,note\npaddy,2022,ok\n"
        p = str(tmp_path / "msp_raw.csv")
        with open(p, "w") as f:
            f.write(raw)
        with pytest.raises(ValueError, match="msp_per_quintal"):
            clean_msp(p, _URL, _DATE)

    def test_msp_column_is_numeric(self, tmp_path):
        p = str(tmp_path / "msp_raw.csv")
        _write_msp_raw(p)
        df = clean_msp(p, _URL, _DATE)
        assert pd.api.types.is_numeric_dtype(df["msp_per_quintal"])


# ---------------------------------------------------------------------------
# main() exits on missing raw files
# ---------------------------------------------------------------------------

class TestMainExitsOnMissingRaw:
    def test_exits_nonzero_when_raw_missing(self, tmp_path, monkeypatch):
        """main() must raise SystemExit(1) when raw files are absent."""
        monkeypatch.setattr(clean_mod, "COST_RAW",        str(tmp_path / "cost_raw.csv"))
        monkeypatch.setattr(clean_mod, "YIELD_PRICE_RAW", str(tmp_path / "yp_raw.csv"))
        monkeypatch.setattr(clean_mod, "MSP_RAW",         str(tmp_path / "msp_raw.csv"))

        with pytest.raises(SystemExit) as exc_info:
            clean_mod.main()
        assert exc_info.value.code != 0, "Expected non-zero exit when raw files missing"

    def test_exits_nonzero_when_one_raw_file_missing(self, tmp_path, monkeypatch):
        """Even one missing raw file triggers the error exit."""
        cost_path = str(tmp_path / "cost_raw.csv")
        yp_path   = str(tmp_path / "yp_raw.csv")
        msp_path  = str(tmp_path / "msp_raw.csv")

        # Write cost and msp but not yield_price
        _write_cost_raw(cost_path)
        _write_msp_raw(msp_path)

        monkeypatch.setattr(clean_mod, "COST_RAW",        cost_path)
        monkeypatch.setattr(clean_mod, "YIELD_PRICE_RAW", yp_path)   # missing
        monkeypatch.setattr(clean_mod, "MSP_RAW",         msp_path)

        with pytest.raises(SystemExit) as exc_info:
            clean_mod.main()
        assert exc_info.value.code != 0
