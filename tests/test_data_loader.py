"""
tests/test_data_loader.py
Unit tests for core/data_loader.py (Task 2.4, Requirement 19.5).

Covers:
- validate_row: valid, null, negative, zero, multiple nulls, row-index in message,
  missing field (KeyError)
- strip_season: leading/trailing whitespace, no season column, pure-function
  (no mutation), already-clean values
- load_cost: correct columns and row count, season stripped, null/negative raises
- load_yield_price: correct columns, null/negative raises
- load_msp: correct columns, null/msp raises
- Integration: generate_placeholders() → load_cost / load_yield_price / load_msp
  all succeed with 10 rows and no errors
"""

import math
import os

import pandas as pd
import pytest

from core.data_loader import validate_row, strip_season, load_cost, load_yield_price, load_msp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cost_row(**overrides):
    """Return a minimal valid cost row Series, with optional field overrides."""
    base = {
        "seed": 1000.0,
        "fertilizer": 2000.0,
        "labour": 3000.0,
        "irrigation": 1500.0,
        "other": 500.0,
    }
    base.update(overrides)
    return pd.Series(base)


COST_FIELDS = ["seed", "fertilizer", "labour", "irrigation", "other"]


# ---------------------------------------------------------------------------
# validate_row
# ---------------------------------------------------------------------------

class TestValidateRow:
    def test_valid_row_does_not_raise(self):
        """All fields non-null and non-negative → no exception."""
        validate_row(_cost_row(), COST_FIELDS, row_index=0)  # must not raise

    def test_null_field_raises_value_error(self):
        """A NaN value raises ValueError naming the field, row index, and 'null'."""
        row = _cost_row(seed=float("nan"))
        with pytest.raises(ValueError) as exc_info:
            validate_row(row, COST_FIELDS, row_index=3)
        msg = str(exc_info.value)
        assert "seed" in msg
        assert "3" in msg
        assert "null" in msg

    def test_negative_field_raises_value_error(self):
        """A negative value raises ValueError naming the field, row index, and 'negative'."""
        row = _cost_row(fertilizer=-1.0)
        with pytest.raises(ValueError) as exc_info:
            validate_row(row, COST_FIELDS, row_index=7)
        msg = str(exc_info.value)
        assert "fertilizer" in msg
        assert "7" in msg
        assert "negative" in msg

    def test_zero_value_is_valid(self):
        """Zero is a valid cost component and must NOT raise."""
        row = _cost_row(irrigation=0.0)
        validate_row(row, COST_FIELDS, row_index=0)  # must not raise

    def test_multiple_nulls_raises_on_first(self):
        """When several fields are null, ValueError is raised on the first one."""
        row = _cost_row(seed=float("nan"), fertilizer=float("nan"))
        with pytest.raises(ValueError) as exc_info:
            validate_row(row, COST_FIELDS, row_index=0)
        # "seed" appears first in COST_FIELDS, so it should be named
        assert "seed" in str(exc_info.value)

    def test_row_index_appears_in_error_message(self):
        """The exact row_index integer must appear in the error message."""
        row = _cost_row(other=-5.0)
        with pytest.raises(ValueError) as exc_info:
            validate_row(row, COST_FIELDS, row_index=42)
        assert "42" in str(exc_info.value)

    def test_missing_field_raises_key_error(self):
        """Requesting a field that is absent from the Series raises KeyError."""
        row = pd.Series({"seed": 100.0, "fertilizer": 200.0})
        with pytest.raises(KeyError):
            validate_row(row, ["seed", "fertilizer", "labour"], row_index=0)

    def test_single_field_list(self):
        """Works correctly with only one field in the list."""
        row = pd.Series({"msp_per_quintal": 1750.0})
        validate_row(row, ["msp_per_quintal"], row_index=0)  # must not raise

    def test_negative_message_contains_value(self):
        """The error message for a negative field includes the bad value."""
        row = _cost_row(labour=-999.0)
        with pytest.raises(ValueError) as exc_info:
            validate_row(row, COST_FIELDS, row_index=1)
        assert "-999" in str(exc_info.value) or "999" in str(exc_info.value)


# ---------------------------------------------------------------------------
# strip_season
# ---------------------------------------------------------------------------

class TestStripSeason:
    def test_leading_whitespace_stripped(self):
        df = pd.DataFrame({"season": ["  Kuruvai", "  Samba"]})
        result = strip_season(df)
        assert list(result["season"]) == ["Kuruvai", "Samba"]

    def test_trailing_whitespace_stripped(self):
        df = pd.DataFrame({"season": ["Kuruvai  ", "Samba  "]})
        result = strip_season(df)
        assert list(result["season"]) == ["Kuruvai", "Samba"]

    def test_leading_and_trailing_whitespace_stripped(self):
        df = pd.DataFrame({"season": ["  Thaladi  ", " Navarai "]})
        result = strip_season(df)
        assert list(result["season"]) == ["Thaladi", "Navarai"]

    def test_no_season_column_returns_unchanged(self):
        """DataFrame without 'season' column must be returned without error."""
        df = pd.DataFrame({"crop": ["paddy", "maize"], "yield": [14.0, 12.0]})
        result = strip_season(df)
        assert list(result.columns) == ["crop", "yield"]
        assert list(result["crop"]) == ["paddy", "maize"]

    def test_pure_function_does_not_mutate_input(self):
        """Original DataFrame must not be modified after calling strip_season."""
        original_seasons = ["  Kuruvai", "Samba  "]
        df = pd.DataFrame({"season": original_seasons.copy()})
        _ = strip_season(df)
        assert list(df["season"]) == original_seasons

    def test_already_clean_values_unchanged(self):
        """Season values with no whitespace should come back exactly as-is."""
        seasons = ["Kuruvai", "Samba", "Thaladi", "Navarai", "Rabi"]
        df = pd.DataFrame({"season": seasons})
        result = strip_season(df)
        assert list(result["season"]) == seasons

    def test_returns_new_dataframe(self):
        """strip_season must return a different object, not the same reference."""
        df = pd.DataFrame({"season": ["Kuruvai"]})
        result = strip_season(df)
        assert result is not df


# ---------------------------------------------------------------------------
# load_cost (uses tmp_path pytest fixture)
# ---------------------------------------------------------------------------

class TestLoadCost:
    def _write_valid_cost_csv(self, path):
        """Write a minimal valid cost CSV to *path*."""
        content = (
            "state,season,crop,year,seed,fertilizer,labour,irrigation,other\n"
            "Tamil Nadu,Kuruvai,paddy,2021,1460,3450,5950,2450,980\n"
            "Tamil Nadu,Kuruvai,paddy,2022,1500,3500,6000,2500,1000\n"
        )
        path.write_text(content)
        return str(path)

    def test_valid_csv_returns_correct_columns(self, tmp_path):
        csv_path = self._write_valid_cost_csv(tmp_path / "cost.csv")
        df = load_cost(csv_path)
        for col in ["state", "season", "crop", "year", "seed",
                    "fertilizer", "labour", "irrigation", "other"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_valid_csv_returns_correct_row_count(self, tmp_path):
        csv_path = self._write_valid_cost_csv(tmp_path / "cost.csv")
        df = load_cost(csv_path)
        assert len(df) == 2

    def test_season_whitespace_stripped_on_load(self, tmp_path):
        """Seasons with surrounding whitespace should be stripped by load_cost."""
        content = (
            "state,season,crop,year,seed,fertilizer,labour,irrigation,other\n"
            "Tamil Nadu,  Kuruvai  ,paddy,2021,1460,3450,5950,2450,980\n"
        )
        csv_path = tmp_path / "cost.csv"
        csv_path.write_text(content)
        df = load_cost(str(csv_path))
        assert df["season"].iloc[0] == "Kuruvai"

    def test_null_seed_raises_value_error(self, tmp_path):
        content = (
            "state,season,crop,year,seed,fertilizer,labour,irrigation,other\n"
            "Tamil Nadu,Kuruvai,paddy,2021,,3450,5950,2450,980\n"
        )
        csv_path = tmp_path / "cost.csv"
        csv_path.write_text(content)
        with pytest.raises(ValueError) as exc_info:
            load_cost(str(csv_path))
        assert "seed" in str(exc_info.value)
        assert "null" in str(exc_info.value)

    def test_negative_fertilizer_raises_value_error(self, tmp_path):
        content = (
            "state,season,crop,year,seed,fertilizer,labour,irrigation,other\n"
            "Tamil Nadu,Kuruvai,paddy,2021,1460,-1,5950,2450,980\n"
        )
        csv_path = tmp_path / "cost.csv"
        csv_path.write_text(content)
        with pytest.raises(ValueError) as exc_info:
            load_cost(str(csv_path))
        assert "fertilizer" in str(exc_info.value)
        assert "negative" in str(exc_info.value)

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_cost(str(tmp_path / "nonexistent.csv"))


# ---------------------------------------------------------------------------
# load_yield_price
# ---------------------------------------------------------------------------

class TestLoadYieldPrice:
    def _write_valid_yp_csv(self, path):
        content = (
            "state,season,crop,year,yield_quintal_per_acre,price_per_quintal\n"
            "Tamil Nadu,Kuruvai,paddy,2021,15.0,1950.0\n"
            "Tamil Nadu,Kuruvai,paddy,2022,17.5,2050.0\n"
        )
        path.write_text(content)
        return str(path)

    def test_valid_csv_returns_correct_columns(self, tmp_path):
        csv_path = self._write_valid_yp_csv(tmp_path / "yp.csv")
        df = load_yield_price(csv_path)
        for col in ["state", "season", "crop", "year",
                    "yield_quintal_per_acre", "price_per_quintal"]:
            assert col in df.columns, f"Missing column: {col}"

    def test_valid_csv_returns_correct_row_count(self, tmp_path):
        csv_path = self._write_valid_yp_csv(tmp_path / "yp.csv")
        df = load_yield_price(csv_path)
        assert len(df) == 2

    def test_null_yield_raises_value_error(self, tmp_path):
        content = (
            "state,season,crop,year,yield_quintal_per_acre,price_per_quintal\n"
            "Tamil Nadu,Kuruvai,paddy,2021,,1950.0\n"
        )
        csv_path = tmp_path / "yp.csv"
        csv_path.write_text(content)
        with pytest.raises(ValueError) as exc_info:
            load_yield_price(str(csv_path))
        assert "yield_quintal_per_acre" in str(exc_info.value)
        assert "null" in str(exc_info.value)

    def test_negative_price_raises_value_error(self, tmp_path):
        content = (
            "state,season,crop,year,yield_quintal_per_acre,price_per_quintal\n"
            "Tamil Nadu,Kuruvai,paddy,2021,15.0,-100.0\n"
        )
        csv_path = tmp_path / "yp.csv"
        csv_path.write_text(content)
        with pytest.raises(ValueError) as exc_info:
            load_yield_price(str(csv_path))
        assert "price_per_quintal" in str(exc_info.value)
        assert "negative" in str(exc_info.value)

    def test_season_stripped_on_load(self, tmp_path):
        content = (
            "state,season,crop,year,yield_quintal_per_acre,price_per_quintal\n"
            "Tamil Nadu, Samba ,paddy,2021,15.0,1950.0\n"
        )
        csv_path = tmp_path / "yp.csv"
        csv_path.write_text(content)
        df = load_yield_price(str(csv_path))
        assert df["season"].iloc[0] == "Samba"


# ---------------------------------------------------------------------------
# load_msp
# ---------------------------------------------------------------------------

class TestLoadMsp:
    def _write_valid_msp_csv(self, path):
        content = (
            "crop,year,msp_per_quintal\n"
            "paddy,2021,1940.0\n"
            "paddy,2022,2015.0\n"
        )
        path.write_text(content)
        return str(path)

    def test_valid_csv_returns_msp_column(self, tmp_path):
        csv_path = self._write_valid_msp_csv(tmp_path / "msp.csv")
        df = load_msp(csv_path)
        assert "msp_per_quintal" in df.columns

    def test_valid_csv_returns_correct_row_count(self, tmp_path):
        csv_path = self._write_valid_msp_csv(tmp_path / "msp.csv")
        df = load_msp(csv_path)
        assert len(df) == 2

    def test_null_msp_raises_value_error(self, tmp_path):
        content = (
            "crop,year,msp_per_quintal\n"
            "paddy,2021,\n"
        )
        csv_path = tmp_path / "msp.csv"
        csv_path.write_text(content)
        with pytest.raises(ValueError) as exc_info:
            load_msp(str(csv_path))
        assert "msp_per_quintal" in str(exc_info.value)
        assert "null" in str(exc_info.value)

    def test_negative_msp_raises_value_error(self, tmp_path):
        content = (
            "crop,year,msp_per_quintal\n"
            "paddy,2021,-50.0\n"
        )
        csv_path = tmp_path / "msp.csv"
        csv_path.write_text(content)
        with pytest.raises(ValueError) as exc_info:
            load_msp(str(csv_path))
        assert "msp_per_quintal" in str(exc_info.value)
        assert "negative" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Integration test: generate_placeholders → loaders
# ---------------------------------------------------------------------------

class TestIntegrationPlaceholdersAndLoaders:
    """
    Run generate_placeholders() into a temp directory and confirm that all
    three loaders can read the output without errors, and that each file
    contains exactly 10 rows.
    """

    def test_placeholder_csvs_load_cleanly(self, tmp_path, monkeypatch):
        """generate_placeholders() writes 10-row CSVs that the loaders accept."""
        import data.clean_data as clean_mod

        # Redirect output paths to tmp_path so we don't overwrite real data
        monkeypatch.setattr(clean_mod, "COST_OUT", str(tmp_path / "cost.csv"))
        monkeypatch.setattr(clean_mod, "YIELD_PRICE_OUT", str(tmp_path / "yield_price.csv"))
        monkeypatch.setattr(clean_mod, "MSP_OUT", str(tmp_path / "msp.csv"))

        clean_mod.generate_placeholders()

        cost_df = load_cost(str(tmp_path / "cost.csv"))
        yp_df = load_yield_price(str(tmp_path / "yield_price.csv"))
        msp_df = load_msp(str(tmp_path / "msp.csv"))

        assert len(cost_df) == 10, f"Expected 10 cost rows, got {len(cost_df)}"
        assert len(yp_df) == 10, f"Expected 10 yield_price rows, got {len(yp_df)}"
        assert len(msp_df) == 10, f"Expected 10 msp rows, got {len(msp_df)}"
