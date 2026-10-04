"""
tests/test_check_data.py — AgriSecure AI
==========================================

Tests for scripts/check_data.py (validator) and the PLACEHOLDER_TAG
propagation through core/crops._is_placeholder().

Coverage
--------
Validator (check_data.main):
  - passes on the live CSVs (blank source_url is a warning, not error)
  - returns non-zero when a required column is missing
  - returns non-zero when a negative yield is present
  - returns non-zero when a crop in yield_price has no MSP row
  - blank source_url issues a warning but does not fail

Placeholder tag:
  - _is_placeholder returns True when note == PLACEHOLDER_TAG
  - _is_placeholder returns True when source_url is blank
  - _is_placeholder returns False when note is clean AND source_url is set
  - _is_placeholder returns False for empty DataFrame
"""

import importlib
import io
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
# Helpers
# ---------------------------------------------------------------------------

def _make_cost_df(**overrides):
    data = {
        "state":      ["Tamil Nadu"],
        "season":     ["Kuruvai"],
        "crop":       ["paddy"],
        "year":       [2022],
        "seed":       [1500.0],
        "fertilizer": [3500.0],
        "labour":     [6000.0],
        "irrigation": [2500.0],
        "other":      [1000.0],
        "note":       ["PLACEHOLDER – verify"],
        "source_url": [""],
        "retrieved_date": [""],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def _make_yp_df(**overrides):
    data = {
        "state":                 ["Tamil Nadu"],
        "season":                ["Kuruvai"],
        "crop":                  ["paddy"],
        "year":                  [2022],
        "yield_quintal_per_acre":[15.0],
        "price_per_quintal":     [2000.0],
        "note":                  ["PLACEHOLDER – verify"],
        "source_url":            [""],
        "retrieved_date":        [""],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def _make_msp_df(**overrides):
    data = {
        "crop":            ["paddy"],
        "year":            [2022],
        "msp_per_quintal": [2015.0],
        "note":            ["PLACEHOLDER – verify"],
        "source_url":      [""],
        "retrieved_date":  [""],
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

        # Temporarily swap path constants
        orig = (_cd.COST_CSV, _cd.YIELD_PRICE_CSV, _cd.MSP_CSV,
                _cd.errors[:], _cd.warnings[:])
        _cd.COST_CSV        = cost_path
        _cd.YIELD_PRICE_CSV = yp_path
        _cd.MSP_CSV         = msp_path
        _cd.errors.clear()
        _cd.warnings.clear()
        try:
            rc = _cd.main()
        finally:
            (_cd.COST_CSV, _cd.YIELD_PRICE_CSV, _cd.MSP_CSV,
             _cd.errors[:], _cd.warnings[:]) = orig[0], orig[1], orig[2], orig[3], orig[4]
            _cd.errors.clear()
            _cd.errors.extend(orig[3])
            _cd.warnings.clear()
            _cd.warnings.extend(orig[4])
        return rc


# ---------------------------------------------------------------------------
# Validator — live CSVs
# ---------------------------------------------------------------------------

class TestValidatorOnLiveCSVs:
    def test_live_csvs_pass(self):
        """The current data/*.csv files must pass all checks (warnings OK)."""
        _cd.errors.clear()
        _cd.warnings.clear()
        rc = _cd.main()
        assert rc == 0, f"Validator failed on live CSVs: {_cd.errors}"


# ---------------------------------------------------------------------------
# Validator — synthetic cases
# ---------------------------------------------------------------------------

class TestValidatorSyntheticCases:
    def test_passes_on_valid_data(self):
        rc = _run_validator(_make_cost_df(), _make_yp_df(), _make_msp_df())
        assert rc == 0

    def test_fails_missing_required_column(self):
        """Removing a required column must cause a non-zero exit."""
        bad_yp = _make_yp_df()
        bad_yp = bad_yp.drop(columns=["yield_quintal_per_acre"])
        rc = _run_validator(_make_cost_df(), bad_yp, _make_msp_df())
        assert rc != 0

    def test_fails_negative_yield(self):
        """A negative yield value must cause a non-zero exit."""
        bad_yp = _make_yp_df(yield_quintal_per_acre=[-5.0])
        rc = _run_validator(_make_cost_df(), bad_yp, _make_msp_df())
        assert rc != 0

    def test_fails_negative_cost_component(self):
        """A negative seed cost must cause a non-zero exit."""
        bad_cost = _make_cost_df(seed=[-100.0])
        rc = _run_validator(bad_cost, _make_yp_df(), _make_msp_df())
        assert rc != 0

    def test_fails_crop_missing_msp(self):
        """A crop in yield_price with no MSP row must cause a non-zero exit."""
        yp_with_new_crop = _make_yp_df(crop=["wheat"])
        rc = _run_validator(_make_cost_df(), yp_with_new_crop, _make_msp_df())
        assert rc != 0

    def test_blank_source_url_is_warning_not_error(self):
        """Blank source_url should issue a warning but not fail."""
        rc = _run_validator(_make_cost_df(), _make_yp_df(), _make_msp_df())
        # rc == 0 even though source_url is blank
        assert rc == 0


# ---------------------------------------------------------------------------
# Placeholder tag propagation via _is_placeholder
# ---------------------------------------------------------------------------

from data.clean_data import PLACEHOLDER_TAG
from core.crops import _is_placeholder  # type: ignore[attr-defined]


class TestIsPlaceholder:
    def test_true_when_note_equals_placeholder_tag(self):
        df = pd.DataFrame({"note": [PLACEHOLDER_TAG], "source_url": ["https://example.com"]})
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
        df = pd.DataFrame({"note": [""], "source_url": ["https://example.com"]})
        assert _is_placeholder(df) is False

    def test_false_for_empty_dataframe(self):
        df = pd.DataFrame({"note": [], "source_url": []})
        assert _is_placeholder(df) is False

    def test_false_when_no_columns(self):
        df = pd.DataFrame({"value": [1, 2, 3]})
        assert _is_placeholder(df) is False
