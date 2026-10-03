"""
tests/test_loans.py — AgriSecure AI
=====================================

Unit tests for core/loans.py:
  - funding_gap
  - institutional_loan_limit
  - residual_gap
  - harvest_window

Coverage
--------
- Normal cases for all four functions
- Loan larger than funding need → residual_gap returns 0, not negative
- Missing / unknown crop duration in harvest_window → returns None, no crash
- Edge case: zero own_funds (full cost is the gap)
- Edge case: zero land_acres (loan limit is 0)
- own_funds greater than total_cost (funding_gap clamped to 0)
- harvest_window: known crops return a positive integer
- harvest_window: crop lookup is case-insensitive
- harvest_window: season parameter accepted without error
- institutional_loan_limit: capped at KCC_MAX_LOAN for large land areas
"""

import pytest
import pandas as pd

from config import get_config
from core.loans import (
    funding_gap,
    institutional_loan_limit,
    residual_gap,
    harvest_window,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_cost_df(crop: str = "paddy", season: str = "Kuruvai") -> pd.DataFrame:
    """Return a one-row cost DataFrame sufficient for harvest_window tests."""
    return pd.DataFrame([{
        "state": "Tamil Nadu",
        "season": season,
        "crop": crop,
        "year": 2022,
        "seed": 1000,
        "fertilizer": 2000,
        "labour": 3000,
        "irrigation": 1000,
        "other": 500,
        "note": "",
    }])


# ---------------------------------------------------------------------------
# funding_gap
# ---------------------------------------------------------------------------

class TestFundingGap:
    def test_normal_case(self):
        """Farmer needs 20000 - 5000 = 15000."""
        assert funding_gap(20_000.0, 5_000.0) == pytest.approx(15_000.0)

    def test_zero_own_funds(self):
        """Zero own funds → full cost is the gap."""
        assert funding_gap(30_000.0, 0.0) == pytest.approx(30_000.0)

    def test_exact_coverage(self):
        """Own funds exactly equal total cost → gap is 0."""
        assert funding_gap(15_000.0, 15_000.0) == pytest.approx(0.0)

    def test_surplus_own_funds_clamped_to_zero(self):
        """Own funds exceed total cost → gap clamped to 0, never negative."""
        result = funding_gap(10_000.0, 20_000.0)
        assert result == pytest.approx(0.0)
        assert result >= 0.0

    def test_zero_cost_zero_gap(self):
        """Zero cost → zero gap regardless of own funds."""
        assert funding_gap(0.0, 0.0) == pytest.approx(0.0)
        assert funding_gap(0.0, 5_000.0) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# institutional_loan_limit
# ---------------------------------------------------------------------------

class TestInstitutionalLoanLimit:
    def test_normal_case(self):
        """1 acre → per_acre_rate × 1.0, assuming result < KCC_MAX_LOAN."""
        per_acre = get_config("KCC_SCALE_OF_FINANCE_PER_ACRE")
        result = institutional_loan_limit(1.0)
        # 1 acre × per_acre is 15000 which is well below 300000 cap
        assert result == pytest.approx(per_acre * 1.0)

    def test_zero_acres_returns_zero(self):
        """Zero acres → zero loan limit."""
        assert institutional_loan_limit(0.0) == pytest.approx(0.0)

    def test_scales_with_acres(self):
        """5 acres → 5× the per-acre rate (if under cap)."""
        per_acre = get_config("KCC_SCALE_OF_FINANCE_PER_ACRE")
        result = institutional_loan_limit(5.0)
        assert result == pytest.approx(per_acre * 5.0)

    def test_capped_at_kcc_max_loan(self):
        """Very large land area → result capped at KCC_MAX_LOAN."""
        kcc_max = get_config("KCC_MAX_LOAN")
        result = institutional_loan_limit(1_000.0)
        assert result == pytest.approx(kcc_max)

    def test_result_never_exceeds_kcc_max(self):
        """For any acreage, result must not exceed KCC_MAX_LOAN."""
        kcc_max = get_config("KCC_MAX_LOAN")
        for acres in [0.1, 1.0, 10.0, 100.0, 999.9]:
            assert institutional_loan_limit(acres) <= kcc_max + 1e-9


# ---------------------------------------------------------------------------
# residual_gap
# ---------------------------------------------------------------------------

class TestResidualGap:
    def test_normal_case(self):
        """Need 15000, loan 10000 → residual 5000."""
        assert residual_gap(15_000.0, 10_000.0) == pytest.approx(5_000.0)

    def test_loan_exactly_covers_need(self):
        """Loan equals need → residual is 0."""
        assert residual_gap(12_000.0, 12_000.0) == pytest.approx(0.0)

    def test_loan_larger_than_need_clamped_to_zero(self):
        """Loan exceeds need → residual clamped to 0, never negative."""
        result = residual_gap(10_000.0, 20_000.0)
        assert result == pytest.approx(0.0)
        assert result >= 0.0

    def test_loan_larger_than_need_large_surplus(self):
        """Large institutional loan well above the gap → still returns 0."""
        result = residual_gap(5_000.0, 300_000.0)
        assert result == pytest.approx(0.0)

    def test_zero_loan_residual_equals_gap(self):
        """Zero loan → residual gap equals the full funding gap."""
        assert residual_gap(25_000.0, 0.0) == pytest.approx(25_000.0)

    def test_zero_gap_zero_residual(self):
        """If funding gap is already 0, residual is also 0."""
        assert residual_gap(0.0, 10_000.0) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# harvest_window
# ---------------------------------------------------------------------------

class TestHarvestWindow:
    def test_known_crop_returns_positive_int(self):
        """Paddy is in CROP_DURATION_WEEKS → returns a positive integer."""
        df = _minimal_cost_df(crop="paddy")
        result = harvest_window("paddy", "Kuruvai", df)
        assert isinstance(result, int)
        assert result >= 1

    def test_known_crop_maize(self):
        """Maize is a known crop and should return a positive integer."""
        df = _minimal_cost_df(crop="maize")
        result = harvest_window("maize", "Kuruvai", df)
        assert isinstance(result, int)
        assert result >= 1

    def test_known_crop_groundnut(self):
        """Groundnut is a known crop → positive integer."""
        df = _minimal_cost_df(crop="groundnut")
        result = harvest_window("groundnut", "Rabi", df)
        assert isinstance(result, int)
        assert result >= 1

    def test_unknown_crop_returns_none(self):
        """Crop not in CROP_DURATION_WEEKS → returns None, does not crash."""
        df = _minimal_cost_df(crop="unknown_crop_xyz")
        result = harvest_window("unknown_crop_xyz", "Kharif", df)
        assert result is None

    def test_missing_crop_does_not_raise(self):
        """Calling harvest_window with an unknown crop must not raise."""
        df = pd.DataFrame()   # empty DataFrame
        try:
            result = harvest_window("nonexistent", "Rabi", df)
            assert result is None
        except Exception as exc:
            pytest.fail(f"harvest_window raised unexpectedly: {exc}")

    def test_case_insensitive_crop_name(self):
        """Crop name matching is case-insensitive ('PADDY' == 'paddy')."""
        df = _minimal_cost_df(crop="paddy")
        result_lower = harvest_window("paddy", "Kuruvai", df)
        result_upper = harvest_window("PADDY", "Kuruvai", df)
        result_mixed = harvest_window("Paddy", "Kuruvai", df)
        assert result_lower == result_upper == result_mixed

    def test_season_parameter_accepted(self):
        """season parameter is accepted; function does not crash on any season."""
        df = _minimal_cost_df(crop="paddy")
        for season in ["Kuruvai", "Rabi", "Kharif", "Samba", "Thaladi"]:
            result = harvest_window("paddy", season, df)
            assert result is not None

    def test_paddy_approx_4_months(self):
        """Paddy is ~17 weeks → ~4 months (17 / 4.333 ≈ 3.92 → rounds to 4)."""
        df = _minimal_cost_df(crop="paddy")
        result = harvest_window("paddy", "Kuruvai", df)
        assert result == 4

    def test_sugarcane_approx_12_months(self):
        """Sugarcane is ~52 weeks → ~12 months (52 / 4.333 ≈ 12.0)."""
        df = _minimal_cost_df(crop="sugarcane")
        result = harvest_window("sugarcane", "Kharif", df)
        assert result == 12

    def test_empty_df_unknown_crop_returns_none(self):
        """Empty DataFrame with unknown crop → None without crash."""
        result = harvest_window("millet", "Kharif", pd.DataFrame())
        assert result is None


# ---------------------------------------------------------------------------
# Integration: funding_gap → institutional_loan_limit → residual_gap
# ---------------------------------------------------------------------------

class TestLoanWorkflow:
    def test_full_workflow_no_moneylender_needed(self):
        """If the institutional loan covers the full need, residual is 0."""
        total_cost = 50_000.0
        own_capital = 20_000.0
        acres = 5.0

        gap = funding_gap(total_cost, own_capital)           # 30000
        limit = institutional_loan_limit(acres)               # 15000*5 = 75000
        remaining = residual_gap(gap, limit)                  # max(0, 30000-75000) = 0

        assert gap == pytest.approx(30_000.0)
        assert limit == pytest.approx(75_000.0)
        assert remaining == pytest.approx(0.0)

    def test_full_workflow_moneylender_needed(self):
        """Small holding: institutional loan doesn't cover full need."""
        total_cost = 80_000.0
        own_capital = 5_000.0
        acres = 1.0

        per_acre = get_config("KCC_SCALE_OF_FINANCE_PER_ACRE")   # 15000
        gap = funding_gap(total_cost, own_capital)                # 75000
        limit = institutional_loan_limit(acres)                    # 15000
        remaining = residual_gap(gap, limit)                       # 75000-15000=60000

        assert gap == pytest.approx(75_000.0)
        assert limit == pytest.approx(per_acre * 1.0)
        assert remaining == pytest.approx(75_000.0 - per_acre * 1.0)
