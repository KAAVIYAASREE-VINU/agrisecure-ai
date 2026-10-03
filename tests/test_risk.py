"""
tests/test_risk.py — AgriSecure AI
=====================================

Unit tests for core/risk.py :: cv_risk_colour, dscr, dscr_colour.

Coverage
--------
cv_risk_colour
  - CV below green threshold → "green"
  - CV at green threshold exactly → "yellow" (boundary)
  - CV between thresholds → "yellow"
  - CV at red threshold exactly → "yellow" (boundary)
  - CV above red threshold → "red"
  - CV = 0.0 → "green" (zero variation, perfect predictability)

dscr
  - Zero obligation → math.inf (must not raise ZeroDivisionError)
  - Normal positive income and obligation → correct ratio
  - Income = 0 → 0.0
  - Large income, small obligation → large ratio

dscr_colour
  - math.inf → None (indeterminate / no loan)
  - DSCR below yellow threshold → "red"
  - DSCR at yellow threshold exactly → "yellow" (boundary)
  - DSCR between thresholds → "yellow"
  - DSCR at green threshold exactly → "green" (boundary)
  - DSCR above green threshold → "green"
  - DSCR = 0.0 → "red"

Thresholds (from config.py, verified 2024-01-15):
  CV_GREEN_THRESHOLD = 0.20
  CV_RED_THRESHOLD   = 0.40
  DSCR_YELLOW_THRESHOLD = 1.0
  DSCR_GREEN_THRESHOLD  = 1.5
"""

import math
import pytest

from config import get_config
from core.risk import cv_risk_colour, dscr, dscr_colour


# ---------------------------------------------------------------------------
# Fixtures — read thresholds from config once for boundary tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def cv_green():
    return get_config("CV_GREEN_THRESHOLD")      # 0.20


@pytest.fixture(scope="module")
def cv_red():
    return get_config("CV_RED_THRESHOLD")        # 0.40


@pytest.fixture(scope="module")
def dscr_yellow():
    return get_config("DSCR_YELLOW_THRESHOLD")   # 1.0


@pytest.fixture(scope="module")
def dscr_green():
    return get_config("DSCR_GREEN_THRESHOLD")    # 1.5


# ===========================================================================
# cv_risk_colour
# ===========================================================================

class TestCvRiskColour:
    """Tests for cv_risk_colour(cv) -> "green" | "yellow" | "red"."""

    # --- Normal cases -------------------------------------------------------

    def test_low_cv_is_green(self, cv_green):
        """CV well below green threshold → low risk → "green"."""
        assert cv_risk_colour(cv_green / 2) == "green"

    def test_mid_cv_is_yellow(self, cv_green, cv_red):
        """CV halfway between thresholds → medium risk → "yellow"."""
        mid = (cv_green + cv_red) / 2
        assert cv_risk_colour(mid) == "yellow"

    def test_high_cv_is_red(self, cv_red):
        """CV well above red threshold → high risk → "red"."""
        assert cv_risk_colour(cv_red * 2) == "red"

    # --- Zero CV (no variation) ---------------------------------------------

    def test_zero_cv_is_green(self):
        """CV = 0.0 means perfect predictability → "green"."""
        assert cv_risk_colour(0.0) == "green"

    # --- Boundary: green threshold ------------------------------------------

    def test_cv_just_below_green_threshold_is_green(self, cv_green):
        """CV just below CV_GREEN_THRESHOLD → "green"."""
        assert cv_risk_colour(cv_green - 1e-9) == "green"

    def test_cv_at_green_threshold_is_yellow(self, cv_green):
        """CV exactly at CV_GREEN_THRESHOLD → "yellow" (threshold is exclusive for green)."""
        assert cv_risk_colour(cv_green) == "yellow"

    def test_cv_just_above_green_threshold_is_yellow(self, cv_green):
        """CV just above CV_GREEN_THRESHOLD → "yellow"."""
        assert cv_risk_colour(cv_green + 1e-9) == "yellow"

    # --- Boundary: red threshold --------------------------------------------

    def test_cv_just_below_red_threshold_is_yellow(self, cv_red):
        """CV just below CV_RED_THRESHOLD → "yellow"."""
        assert cv_risk_colour(cv_red - 1e-9) == "yellow"

    def test_cv_at_red_threshold_is_yellow(self, cv_red):
        """CV exactly at CV_RED_THRESHOLD → "yellow" (threshold is exclusive for red)."""
        assert cv_risk_colour(cv_red) == "yellow"

    def test_cv_just_above_red_threshold_is_red(self, cv_red):
        """CV just above CV_RED_THRESHOLD → "red"."""
        assert cv_risk_colour(cv_red + 1e-9) == "red"

    # --- Return type guard --------------------------------------------------

    def test_returns_string(self, cv_green, cv_red):
        """cv_risk_colour always returns a str."""
        for cv_val in [0.0, cv_green, (cv_green + cv_red) / 2, cv_red, cv_red * 2]:
            assert isinstance(cv_risk_colour(cv_val), str)


# ===========================================================================
# dscr
# ===========================================================================

class TestDscr:
    """Tests for dscr(annual_income, total_annual_debt_obligation) -> float."""

    # --- Zero obligation edge case ------------------------------------------

    def test_zero_obligation_returns_inf(self):
        """Zero debt obligation must return math.inf, never raise ZeroDivisionError."""
        result = dscr(annual_income=100_000, total_annual_debt_obligation=0)
        assert result == math.inf

    def test_zero_obligation_zero_income_returns_inf(self):
        """Even with zero income, zero obligation still returns math.inf."""
        result = dscr(annual_income=0, total_annual_debt_obligation=0)
        assert result == math.inf

    # --- Normal cases -------------------------------------------------------

    def test_equal_income_and_obligation_is_one(self):
        """Income equals obligation → DSCR = 1.0."""
        assert dscr(50_000, 50_000) == pytest.approx(1.0)

    def test_income_double_obligation(self):
        """Income is twice the obligation → DSCR = 2.0."""
        assert dscr(100_000, 50_000) == pytest.approx(2.0)

    def test_income_half_obligation(self):
        """Income is half the obligation → DSCR = 0.5."""
        assert dscr(25_000, 50_000) == pytest.approx(0.5)

    def test_zero_income_returns_zero(self):
        """Income = 0 with positive obligation → DSCR = 0.0."""
        assert dscr(0, 50_000) == pytest.approx(0.0)

    def test_large_ratio(self):
        """Very large income relative to obligation → large DSCR."""
        result = dscr(1_000_000, 100)
        assert result == pytest.approx(10_000.0)

    def test_return_type_is_float(self):
        """dscr always returns a float (not int)."""
        result = dscr(80_000, 60_000)
        assert isinstance(result, float)


# ===========================================================================
# dscr_colour
# ===========================================================================

class TestDscrColour:
    """Tests for dscr_colour(dscr_value) -> "green" | "yellow" | "red" | None."""

    # --- Indeterminate (no obligation) --------------------------------------

    def test_inf_returns_none(self):
        """math.inf → indeterminate → None (Requirement 8.3)."""
        assert dscr_colour(math.inf) is None

    # --- Normal cases -------------------------------------------------------

    def test_high_dscr_is_green(self, dscr_green):
        """DSCR well above green threshold → "green" (safe to repay)."""
        assert dscr_colour(dscr_green * 2) == "green"

    def test_mid_dscr_is_yellow(self, dscr_yellow, dscr_green):
        """DSCR between yellow and green thresholds → "yellow" (caution)."""
        mid = (dscr_yellow + dscr_green) / 2
        assert dscr_colour(mid) == "yellow"

    def test_low_dscr_is_red(self, dscr_yellow):
        """DSCR well below yellow threshold → "red" (cannot repay alone)."""
        assert dscr_colour(dscr_yellow / 2) == "red"

    def test_zero_dscr_is_red(self):
        """DSCR = 0.0 → "red"."""
        assert dscr_colour(0.0) == "red"

    # --- Boundary: yellow threshold -----------------------------------------

    def test_dscr_just_below_yellow_threshold_is_red(self, dscr_yellow):
        """DSCR just below DSCR_YELLOW_THRESHOLD → "red"."""
        assert dscr_colour(dscr_yellow - 1e-9) == "red"

    def test_dscr_at_yellow_threshold_is_yellow(self, dscr_yellow):
        """DSCR exactly at DSCR_YELLOW_THRESHOLD → "yellow" (boundary inclusive)."""
        assert dscr_colour(dscr_yellow) == "yellow"

    def test_dscr_just_above_yellow_threshold_is_yellow(self, dscr_yellow):
        """DSCR just above DSCR_YELLOW_THRESHOLD → "yellow"."""
        assert dscr_colour(dscr_yellow + 1e-9) == "yellow"

    # --- Boundary: green threshold ------------------------------------------

    def test_dscr_just_below_green_threshold_is_yellow(self, dscr_green):
        """DSCR just below DSCR_GREEN_THRESHOLD → "yellow"."""
        assert dscr_colour(dscr_green - 1e-9) == "yellow"

    def test_dscr_at_green_threshold_is_green(self, dscr_green):
        """DSCR exactly at DSCR_GREEN_THRESHOLD → "green" (at-or-above is green)."""
        assert dscr_colour(dscr_green) == "green"

    def test_dscr_just_above_green_threshold_is_green(self, dscr_green):
        """DSCR just above DSCR_GREEN_THRESHOLD → "green"."""
        assert dscr_colour(dscr_green + 1e-9) == "green"

    # --- Return type guard --------------------------------------------------

    def test_returns_string_or_none(self, dscr_yellow, dscr_green):
        """dscr_colour returns str or None for all typical inputs."""
        for val in [0.0, dscr_yellow - 0.1, dscr_yellow, (dscr_yellow + dscr_green) / 2,
                    dscr_green, dscr_green + 1.0, math.inf]:
            result = dscr_colour(val)
            assert result is None or isinstance(result, str)
