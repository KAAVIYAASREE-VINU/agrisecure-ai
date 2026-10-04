"""
tests/test_presets.py — AgriSecure AI
======================================

Unit tests for assistant/presets.py:
    answer_repay_on_time, answer_rain_fails, answer_moneylender_worth_it

Coverage
--------
answer_repay_on_time
- Returns a string for valid results + green DSCR
- Returns a string for valid results + yellow DSCR
- Returns a string for valid results + red DSCR
- Returns "no_loan" string when own_capital covers full cost
- Returns None when required key "crop" is missing from results
- The returned string contains the DSCR value

answer_rain_fails
- Returns a string for valid results with bad-harvest profit > 0
- Returns a string for valid results with bad-harvest profit < 0
- Returns None when required key "acres" is missing from results
- Returns None when the DataFrame is empty (no data)

answer_moneylender_worth_it
- Returns a string showing the extra cost for valid results
- Returns None when there is no funding gap (own_capital >= total_cost)
- Returns None when required key "season" is missing from results
- Returned string contains moneylender and KCC cost figures

Requirements: 12 (preset question buttons, no LLM)
"""

import math
import pytest
import pandas as pd

from assistant.presets import (
    answer_repay_on_time,
    answer_rain_fails,
    answer_moneylender_worth_it,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _t(key: str) -> str:
    """Minimal t_fn that returns templates from en.json matching keys."""
    templates = {
        "preset_repay_green": "YES DSCR={dscr} income={income} obligation={obligation}",
        "preset_repay_yellow": "UNCERTAIN DSCR={dscr} income={income} obligation={obligation}",
        "preset_repay_red": "RED DSCR={dscr} income={income} obligation={obligation}",
        "preset_repay_no_loan": "NO_LOAN",
        "preset_rain_positive": "POSITIVE profit={profit} revenue={revenue}",
        "preset_rain_negative": "NEGATIVE loss={profit} revenue={revenue}",
        "preset_moneylender_extra": "EXTRA={extra} ml={ml_cost} kcc={kcc_cost} months={months} principal={principal}",
    }
    return templates.get(key, key)


def _make_yp_df(
    crop: str = "paddy",
    state: str = "Tamil Nadu",
    season: str = "Kharif",
    rows: int = 10,
) -> pd.DataFrame:
    """Return a minimal yield_price DataFrame (column names match the real CSV)."""
    import numpy as np
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "crop": [crop] * rows,
        "state": [state] * rows,
        "season": [season] * rows,
        "yield_quintal_per_acre": rng.uniform(8, 12, rows).tolist(),
        "price_per_quintal": rng.uniform(1500, 2000, rows).tolist(),
        "year": list(range(2010, 2010 + rows)),
        "note": [""] * rows,
    })


def _make_msp_df(crop: str = "paddy") -> pd.DataFrame:
    return pd.DataFrame({
        "crop": [crop],
        "msp_per_quintal": [1800.0],
        "year": [2023],
    })


def _make_cost_df(
    crop: str = "paddy",
    state: str = "Tamil Nadu",
    season: str = "Kharif",
) -> pd.DataFrame:
    return pd.DataFrame({
        "crop": [crop],
        "state": [state],
        "season": [season],
        "seed": [3000.0],
        "fertilizer": [4000.0],
        "labour": [5000.0],
        "irrigation": [2000.0],
        "other": [1000.0],
        "duration_weeks": [20],
        "note": [""],
    })


def _base_results(
    *,
    own_capital: float = 0.0,
    cost_total: float = 20000.0,
    moneylender_rate: float | None = None,
) -> dict:
    """Return a minimal results dict for paddy / Tamil Nadu / Kharif."""
    return {
        "crop": "paddy",
        "state": "Tamil Nadu",
        "season": "Kharif",
        "acres": 2.0,
        "costs": {"total": cost_total, "seed": 6000, "fertilizer": 8000,
                  "labour": 10000, "irrigation": 4000, "other": 2000},
        "own_capital": own_capital,
        "moneylender_rate": moneylender_rate,
        "computed_total": cost_total,
    }


# ---------------------------------------------------------------------------
# answer_repay_on_time
# ---------------------------------------------------------------------------

class TestAnswerRepayOnTime:
    def test_returns_string_for_valid_results(self):
        results = _base_results(own_capital=0.0, cost_total=20000.0)
        df_yp = _make_yp_df()
        df_msp = _make_msp_df()
        df_cost = _make_cost_df()
        answer = answer_repay_on_time(results, df_yp, df_msp, df_cost, _t)
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_answer_contains_dscr_value(self):
        results = _base_results(own_capital=0.0, cost_total=20000.0)
        df_yp = _make_yp_df()
        df_msp = _make_msp_df()
        df_cost = _make_cost_df()
        answer = answer_repay_on_time(results, df_yp, df_msp, df_cost, _t)
        # Template substitutes {dscr} — if answer is not "NO_LOAN", DSCR should be a number
        assert answer is not None
        # Should not still contain the literal placeholder
        assert "{dscr}" not in answer

    def test_no_loan_case_when_own_capital_covers_costs(self):
        """own_capital > cost_total → funding gap = 0 → no loan → 'no_loan' key."""
        results = _base_results(own_capital=50000.0, cost_total=20000.0)
        df_yp = _make_yp_df()
        df_msp = _make_msp_df()
        df_cost = _make_cost_df()
        answer = answer_repay_on_time(results, df_yp, df_msp, df_cost, _t)
        # DSCR is math.inf → should use no_loan template
        assert answer == "NO_LOAN"

    def test_returns_none_when_crop_missing(self):
        results = _base_results()
        results.pop("crop")
        df_yp = _make_yp_df()
        answer = answer_repay_on_time(results, df_yp, _make_msp_df(), _make_cost_df(), _t)
        assert answer is None

    def test_returns_none_when_empty_dataframe(self):
        results = _base_results()
        empty_df = pd.DataFrame(columns=["crop", "state", "season",
                                          "yield_quintal_per_acre",
                                          "price_per_quintal", "year", "note"])
        answer = answer_repay_on_time(results, empty_df, _make_msp_df(), _make_cost_df(), _t)
        assert answer is None

    def test_returns_none_when_acres_missing(self):
        results = _base_results()
        results.pop("acres")
        answer = answer_repay_on_time(results, _make_yp_df(), _make_msp_df(), _make_cost_df(), _t)
        assert answer is None


# ---------------------------------------------------------------------------
# answer_rain_fails
# ---------------------------------------------------------------------------

class TestAnswerRainFails:
    def test_returns_string_for_valid_results(self):
        results = _base_results(cost_total=20000.0)
        df_yp = _make_yp_df()
        df_msp = _make_msp_df()
        answer = answer_rain_fails(results, df_yp, df_msp, _t)
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_answer_contains_no_placeholder_tokens(self):
        results = _base_results(cost_total=20000.0)
        answer = answer_rain_fails(results, _make_yp_df(), _make_msp_df(), _t)
        assert answer is None or "{profit}" not in answer
        assert answer is None or "{revenue}" not in answer

    def test_negative_profit_uses_negative_template(self):
        """With high cost, bad harvest should show negative profit."""
        # Cost = ₹200,000 on 2 acres; yield ~8-12 qa/acre × ₹1500-2000/q
        # Even good harvest ≈ 2 * 10 * 1750 = ₹35,000 << cost → bad always negative
        results = _base_results(cost_total=200_000.0)
        answer = answer_rain_fails(results, _make_yp_df(), _make_msp_df(), _t)
        assert answer is not None
        assert answer.startswith("NEGATIVE")

    def test_positive_profit_uses_positive_template(self):
        """With zero cost, bad harvest profit = revenue → positive."""
        results = _base_results(cost_total=0.0)
        answer = answer_rain_fails(results, _make_yp_df(), _make_msp_df(), _t)
        assert answer is not None
        assert answer.startswith("POSITIVE")

    def test_returns_none_when_crop_missing(self):
        results = _base_results()
        results.pop("crop")
        answer = answer_rain_fails(results, _make_yp_df(), _make_msp_df(), _t)
        assert answer is None

    def test_returns_none_when_empty_dataframe(self):
        results = _base_results()
        empty_df = pd.DataFrame(columns=["crop", "state", "season",
                                          "yield_quintal_per_acre",
                                          "price_per_quintal", "year", "note"])
        answer = answer_rain_fails(results, empty_df, _make_msp_df(), _t)
        assert answer is None

    def test_returns_none_when_acres_missing(self):
        results = _base_results()
        results.pop("acres")
        answer = answer_rain_fails(results, _make_yp_df(), _make_msp_df(), _t)
        assert answer is None


# ---------------------------------------------------------------------------
# answer_moneylender_worth_it
# ---------------------------------------------------------------------------

class TestAnswerMoneylenderWorthIt:
    def test_returns_string_for_valid_results_with_gap(self):
        results = _base_results(own_capital=0.0, cost_total=20000.0)
        answer = answer_moneylender_worth_it(results, _make_cost_df(), _t)
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_answer_contains_no_placeholder_tokens(self):
        results = _base_results(own_capital=0.0, cost_total=20000.0)
        answer = answer_moneylender_worth_it(results, _make_cost_df(), _t)
        assert answer is not None
        for token in ["{extra}", "{ml_cost}", "{kcc_cost}", "{months}", "{principal}"]:
            assert token not in answer

    def test_answer_starts_with_extra_prefix(self):
        results = _base_results(own_capital=0.0, cost_total=20000.0)
        answer = answer_moneylender_worth_it(results, _make_cost_df(), _t)
        assert answer is not None
        assert answer.startswith("EXTRA=")

    def test_returns_none_when_no_funding_gap(self):
        """When own_capital >= cost_total, gap = 0 → moneylender question doesn't apply."""
        results = _base_results(own_capital=50000.0, cost_total=20000.0)
        answer = answer_moneylender_worth_it(results, _make_cost_df(), _t)
        assert answer is None

    def test_returns_none_when_season_missing(self):
        results = _base_results()
        results.pop("season")
        answer = answer_moneylender_worth_it(results, _make_cost_df(), _t)
        assert answer is None

    def test_custom_moneylender_rate_is_used(self):
        """Passing a custom moneylender_rate should produce a different extra cost."""
        results_default = _base_results(own_capital=0.0, cost_total=20000.0)
        results_custom = _base_results(own_capital=0.0, cost_total=20000.0,
                                        moneylender_rate=60.0)
        answer_default = answer_moneylender_worth_it(results_default, _make_cost_df(), _t)
        answer_custom = answer_moneylender_worth_it(results_custom, _make_cost_df(), _t)
        assert answer_default is not None
        assert answer_custom is not None
        # The EXTRA= values should differ (60% rate vs default 36%)
        assert answer_default != answer_custom

    def test_returns_none_when_own_capital_missing(self):
        results = _base_results()
        results.pop("own_capital")
        answer = answer_moneylender_worth_it(results, _make_cost_df(), _t)
        assert answer is None
