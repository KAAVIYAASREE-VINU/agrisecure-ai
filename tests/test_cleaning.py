"""
tests/test_cleaning.py
Tests for data/clean_data.py placeholder generation (Task 2.4, Requirement 19.5).

Covers:
- generate_placeholders() creates all three CSV files
- Every row in each placeholder CSV has note == "PLACEHOLDER – verify"
- All crop names are lowercase (no uppercase letters)
- All season names have no leading or trailing whitespace
"""

import os

import pandas as pd
import pytest

import data.clean_data as clean_mod
from data.clean_data import PLACEHOLDER_TAG


# ---------------------------------------------------------------------------
# Fixture: run generate_placeholders() into tmp_path once per test module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def placeholder_dir(tmp_path_factory):
    """
    Write placeholder CSVs into a temporary directory and return the paths
    as a dict so individual tests can load them.
    """
    tmp = tmp_path_factory.mktemp("placeholders")

    cost_path = str(tmp / "cost.csv")
    yp_path = str(tmp / "yield_price.csv")
    msp_path = str(tmp / "msp.csv")

    # Patch module-level output paths with monkeypatching at module scope
    original_cost = clean_mod.COST_OUT
    original_yp = clean_mod.YIELD_PRICE_OUT
    original_msp = clean_mod.MSP_OUT

    clean_mod.COST_OUT = cost_path
    clean_mod.YIELD_PRICE_OUT = yp_path
    clean_mod.MSP_OUT = msp_path

    clean_mod.generate_placeholders()

    # Restore originals so other tests using the real paths are unaffected
    clean_mod.COST_OUT = original_cost
    clean_mod.YIELD_PRICE_OUT = original_yp
    clean_mod.MSP_OUT = original_msp

    return {
        "cost": cost_path,
        "yield_price": yp_path,
        "msp": msp_path,
    }


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------

class TestPlaceholderFilesExist:
    def test_cost_csv_created(self, placeholder_dir):
        assert os.path.isfile(placeholder_dir["cost"]), "cost.csv was not created"

    def test_yield_price_csv_created(self, placeholder_dir):
        assert os.path.isfile(placeholder_dir["yield_price"]), "yield_price.csv was not created"

    def test_msp_csv_created(self, placeholder_dir):
        assert os.path.isfile(placeholder_dir["msp"]), "msp.csv was not created"


# ---------------------------------------------------------------------------
# PLACEHOLDER note tag on every row
# ---------------------------------------------------------------------------

class TestPlaceholderNoteTag:
    def test_cost_all_rows_tagged(self, placeholder_dir):
        df = pd.read_csv(placeholder_dir["cost"])
        assert "note" in df.columns, "cost.csv missing 'note' column"
        bad = df[df["note"] != PLACEHOLDER_TAG]
        assert len(bad) == 0, (
            f"{len(bad)} cost row(s) do not have the PLACEHOLDER tag:\n{bad}"
        )

    def test_yield_price_all_rows_tagged(self, placeholder_dir):
        df = pd.read_csv(placeholder_dir["yield_price"])
        assert "note" in df.columns, "yield_price.csv missing 'note' column"
        bad = df[df["note"] != PLACEHOLDER_TAG]
        assert len(bad) == 0, (
            f"{len(bad)} yield_price row(s) do not have the PLACEHOLDER tag:\n{bad}"
        )

    def test_msp_all_rows_tagged(self, placeholder_dir):
        df = pd.read_csv(placeholder_dir["msp"])
        assert "note" in df.columns, "msp.csv missing 'note' column"
        bad = df[df["note"] != PLACEHOLDER_TAG]
        assert len(bad) == 0, (
            f"{len(bad)} msp row(s) do not have the PLACEHOLDER tag:\n{bad}"
        )


# ---------------------------------------------------------------------------
# Crop names are all lowercase
# ---------------------------------------------------------------------------

class TestCropNamesLowercase:
    def test_cost_crop_names_lowercase(self, placeholder_dir):
        df = pd.read_csv(placeholder_dir["cost"])
        bad = df[df["crop"] != df["crop"].str.lower()]
        assert len(bad) == 0, (
            f"cost.csv has non-lowercase crop names:\n{bad['crop'].tolist()}"
        )

    def test_yield_price_crop_names_lowercase(self, placeholder_dir):
        df = pd.read_csv(placeholder_dir["yield_price"])
        bad = df[df["crop"] != df["crop"].str.lower()]
        assert len(bad) == 0, (
            f"yield_price.csv has non-lowercase crop names:\n{bad['crop'].tolist()}"
        )

    def test_msp_crop_names_lowercase(self, placeholder_dir):
        df = pd.read_csv(placeholder_dir["msp"])
        bad = df[df["crop"] != df["crop"].str.lower()]
        assert len(bad) == 0, (
            f"msp.csv has non-lowercase crop names:\n{bad['crop'].tolist()}"
        )


# ---------------------------------------------------------------------------
# Season names have no leading/trailing whitespace
# ---------------------------------------------------------------------------

class TestSeasonNamesNoWhitespace:
    def test_cost_seasons_stripped(self, placeholder_dir):
        df = pd.read_csv(placeholder_dir["cost"])
        assert "season" in df.columns, "cost.csv has no 'season' column"
        bad = df[df["season"] != df["season"].str.strip()]
        assert len(bad) == 0, (
            f"cost.csv has seasons with surrounding whitespace:\n{bad['season'].tolist()}"
        )

    def test_yield_price_seasons_stripped(self, placeholder_dir):
        df = pd.read_csv(placeholder_dir["yield_price"])
        assert "season" in df.columns, "yield_price.csv has no 'season' column"
        bad = df[df["season"] != df["season"].str.strip()]
        assert len(bad) == 0, (
            f"yield_price.csv has seasons with surrounding whitespace:\n{bad['season'].tolist()}"
        )
