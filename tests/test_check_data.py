"""
tests/test_check_data.py — AgriSecure AI
==========================================

Tests for scripts/check_data.py (validator) and the PLACEHOLDER_TAG
propagation through core/crops._is_placeholder().

Coverage
--------
Validator (check_data.main):
  - passes on the live CSVs
  - returns non-zero when a required column is missing
  - returns non-zero when source_url column is absent
  - returns non-zero when source_url is blank
  - returns non-zero when source_url contains "placeholder" (case-insensitive)
  - returns non-zero when retrieved_date is blank
  - returns non-zero when a negative yield is present
  - returns non-zero when a crop in yield_price has no MSP row

Placeholder tag (_is_placeholder):
  - True when note == PLACEHOLDER_TAG
  - True when source_url is blank
  - True when source_url is whitespace-only
  - True when source_url is null
  - False when note is clean AND source_url is a real URL
  - False for empty DataFrame
  - False when neither column exists
"""

import os
import sys
import tempfile

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Import the validator module from scripts/
# ---------------------------------------------------------------------------

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_ROOT, "scripts")

if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_data as _cd

# ---------------------------------------------------------------------------
# Helpers — synthetic DataFrames with real provenance fields
# ---------------------------------------------------------------------------

_REAL_URL  = "https://example.gov.in/data"
_REAL_DATE = "2025-10-01"


def _make_cost_df(**overrides):
    data = {
        "state":          ["Tamil Nadu"],
        "season":         ["Kuruvai"],
        "crop":           ["paddy"],
        "year":           [2022],
        "seed":           [1500.0],
        "fertilizer":     [3500.0],
        "labour":         [6000.0],
        "irrigation":     [2500.0],
        "other":          [1000.0],
        "note":           ["DES 2022"],
        "source_url":     [_REAL_URL],
        "retrieved_date": [_REAL_DATE],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def _make_yp_df(**overrides):
    data = {
        "state":                  ["Tamil Nadu"],
        "season":                 ["Kuruvai"],
        "crop":                   ["paddy"],
        "year":                   [2022],
        "yield_quintal_per_acre": [15.0],
        "price_per_quintal":      [2000.0],
        "note":                   ["TN Crop Report 2022"],
        "source_url":             [_REAL_URL],
        "retrieved_date":         [_REAL_DATE],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def _make_msp_df(**overrides):
    data = {
        "crop":            ["paddy"],
        "year":            [2022],
        "msp_per_quintal": [2015.0],
        "note":            ["CACP 2022"],
        "source_url":      [_REAL_URL],
        "retrieved_date":  [_REAL_DATE],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def _run_validator(cost_df, yp_df, msp_df):
    """Write three temp CSVs, monkey-patch check_data paths, call main()."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cost_path = os.path.join(tmpdir, "cost.csv")
        yp_path   = os.path.join(tmpdir, "yield_price.csv")
        msp_path  = os.path.join(tmpdir, "msp.csv")
        cost_df.to_csv(cost_path, index=False)
        yp_df.to_csv(yp_path,    index=False)
        msp_df.to_csv(msp_path,  index=False)

        # Save and replace module-level state
        saved = {
            "COST_CSV":        _cd.COST_CSV,
            "YIELD_PRICE_CSV": _cd.YIELD_PRICE_CSV,
            "MSP_CSV":         _cd.MSP_CSV,
            "errors":          _cd.errors[:],
            "warnings":        _cd.warnings[:],
        }
        _cd.COST_CSV        = cost_path
        _cd.YIELD_PRICE_CSV = yp_path
        _cd.MSP_CSV         = msp_path
        _cd.errors.clear()
        _cd.warnings.clear()
        try:
            rc = _cd.main()
        finally:
            _cd.COST_CSV        = saved["COST_CSV"]
            _cd.YIELD_PRICE_CSV = saved["YIELD_PRICE_CSV"]
            _cd.MSP_CSV         = saved["MSP_CSV"]
            _cd.errors.clear();  _cd.errors.extend(saved["errors"])
            _cd.warnings.clear(); _cd.warnings.extend(saved["warnings"])
        return rc


# ---------------------------------------------------------------------------
# Validator — live CSVs
# ---------------------------------------------------------------------------

class TestValidatorOnLiveCSVs:
    def test_live_csvs_pass(self):
        """The live CSVs must pass all validator checks with no errors."""
        _cd.errors.clear()
        _cd.warnings.clear()
        rc = _cd.main()
        assert rc == 0, (
            f"Validator failed on live CSVs ({len(_cd.errors)} error(s)):\n"
            + "\n".join(_cd.errors)
        )


# ---------------------------------------------------------------------------
# Validator — synthetic cases (all data quality)
# ---------------------------------------------------------------------------

class TestValidatorSyntheticCases:
    def test_passes_on_valid_data(self):
        rc = _run_validator(_make_cost_df(), _make_yp_df(), _make_msp_df())
        assert rc == 0

    def test_fails_missing_required_column(self):
        bad_yp = _make_yp_df().drop(columns=["yield_quintal_per_acre"])
        rc = _run_validator(_make_cost_df(), bad_yp, _make_msp_df())
        assert rc != 0

    def test_fails_negative_yield(self):
        bad_yp = _make_yp_df(yield_quintal_per_acre=[-5.0])
        rc = _run_validator(_make_cost_df(), bad_yp, _make_msp_df())
        assert rc != 0

    def test_fails_negative_cost_component(self):
        bad_cost = _make_cost_df(seed=[-100.0])
        rc = _run_validator(bad_cost, _make_yp_df(), _make_msp_df())
        assert rc != 0

    def test_fails_crop_missing_msp(self):
        yp_wheat = _make_yp_df(crop=["wheat"])
        rc = _run_validator(_make_cost_df(), yp_wheat, _make_msp_df())
        assert rc != 0


# ---------------------------------------------------------------------------
# Provenance checks — all hard errors now
# ---------------------------------------------------------------------------

class TestProvenanceChecks:
    def test_fails_when_source_url_column_absent(self):
        """Missing source_url column is an error."""
        bad_yp = _make_yp_df().drop(columns=["source_url"])
        rc = _run_validator(_make_cost_df(), bad_yp, _make_msp_df())
        assert rc != 0

    def test_fails_when_source_url_is_blank(self):
        """Blank source_url must now fail (previously was a warning only)."""
        bad_yp = _make_yp_df(source_url=[""])
        rc = _run_validator(_make_cost_df(), bad_yp, _make_msp_df())
        assert rc != 0

    def test_fails_when_source_url_is_whitespace(self):
        bad_yp = _make_yp_df(source_url=["   "])
        rc = _run_validator(_make_cost_df(), bad_yp, _make_msp_df())
        assert rc != 0

    def test_fails_when_source_url_contains_placeholder_lowercase(self):
        """source_url containing 'placeholder' is an error."""
        bad_yp = _make_yp_df(source_url=["placeholder – verify"])
        rc = _run_validator(_make_cost_df(), bad_yp, _make_msp_df())
        assert rc != 0

    def test_fails_when_source_url_contains_placeholder_uppercase(self):
        """Case-insensitive: 'PLACEHOLDER' in source_url is an error."""
        bad_yp = _make_yp_df(source_url=["PLACEHOLDER – verify"])
        rc = _run_validator(_make_cost_df(), bad_yp, _make_msp_df())
        assert rc != 0

    def test_fails_when_source_url_contains_placeholder_mixed_case(self):
        bad_cost = _make_cost_df(source_url=["Placeholder URL"])
        rc = _run_validator(bad_cost, _make_yp_df(), _make_msp_df())
        assert rc != 0

    def test_fails_when_retrieved_date_column_absent(self):
        bad_msp = _make_msp_df().drop(columns=["retrieved_date"])
        rc = _run_validator(_make_cost_df(), _make_yp_df(), bad_msp)
        assert rc != 0

    def test_fails_when_retrieved_date_is_blank(self):
        bad_msp = _make_msp_df(retrieved_date=[""])
        rc = _run_validator(_make_cost_df(), _make_yp_df(), bad_msp)
        assert rc != 0

    def test_passes_with_real_url_and_date(self):
        """A real, non-placeholder URL and a retrieved_date should pass."""
        rc = _run_validator(_make_cost_df(), _make_yp_df(), _make_msp_df())
        assert rc == 0


# ---------------------------------------------------------------------------
# Placeholder tag propagation via _is_placeholder
# ---------------------------------------------------------------------------

from data.clean_data import PLACEHOLDER_TAG
from core.crops import _is_placeholder  # type: ignore[attr-defined]


class TestIsPlaceholder:
    def test_true_when_note_equals_placeholder_tag(self):
        df = pd.DataFrame({"note": [PLACEHOLDER_TAG], "source_url": [_REAL_URL]})
        assert _is_placeholder(df) is True

    def test_true_when_source_url_is_blank(self):
        df = pd.DataFrame({"note": ["ok"], "source_url": [""]})
        assert _is_placeholder(df) is True

    def test_true_when_source_url_is_whitespace(self):
        df = pd.DataFrame({"note": ["ok"], "source_url": ["   "]})
        assert _is_placeholder(df) is True

    def test_true_when_source_url_is_null(self):
        df = pd.DataFrame({"note": ["ok"], "source_url": [None]})
        assert _is_placeholder(df) is True

    def test_false_when_note_clean_and_source_url_set(self):
        df = pd.DataFrame({"note": [""], "source_url": [_REAL_URL]})
        assert _is_placeholder(df) is False

    def test_false_for_empty_dataframe(self):
        df = pd.DataFrame({"note": [], "source_url": []})
        assert _is_placeholder(df) is False

    def test_false_when_no_columns(self):
        df = pd.DataFrame({"value": [1, 2, 3]})
        assert _is_placeholder(df) is False
