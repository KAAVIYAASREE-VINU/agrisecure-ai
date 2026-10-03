"""
tests/test_comparator.py — AgriSecure AI
==========================================

Unit tests for core/comparator.py :: interest_costs.

Coverage
--------
- Normal case: all three lender costs returned for given principal/months
- Moneylender uses provided rate; bank and KCC use config rates
- Fallback to MONEYLENDER_RATE_DEFAULT when rate not provided
- Rate validation: below MONEYLENDER_RATE_MIN raises ValueError
- Rate validation: above MONEYLENDER_RATE_MAX raises ValueError
- Rate at boundary values (MONEYLENDER_RATE_MIN, MONEYLENDER_RATE_MAX) is valid
- KCC is always cheaper than bank; bank cheaper than default moneylender rate
- Edge cases: zero months, zero principal
"""

import pytest

from config import get_config
from core.comparator import interest_costs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _expected_interest(principal: float, rate_pct: float, months: float) -> float:
    """Replicate the formula: principal × (rate/100) / 12 × months."""
    return principal * (rate_pct / 100.0) / 12.0 * months


# ---------------------------------------------------------------------------
# Normal cases
# ---------------------------------------------------------------------------

class TestNormalCase:
    def test_returns_all_three_keys(self):
        """Result dict must contain moneylender, bank, and kcc keys."""
        result = interest_costs(100_000, 6)
        assert set(result.keys()) == {"moneylender", "bank", "kcc"}

    def test_all_values_are_floats(self):
        """All returned values must be numeric (float)."""
        result = interest_costs(50_000, 4)
        for key, val in result.items():
            assert isinstance(val, float), f"{key} is not float"

    def test_explicit_moneylender_rate_used(self):
        """When moneylender_rate is supplied, it is used for the moneylender cost."""
        principal, months, rate = 100_000, 6, 48.0
        result = interest_costs(principal, months, moneylender_rate=rate)
        expected = _expected_interest(principal, rate, months)
        assert result["moneylender"] == pytest.approx(expected)

    def test_bank_uses_config_rate(self):
        """bank cost uses BANK_CROP_LOAN_RATE from config regardless of input."""
        principal, months = 100_000, 12
        bank_rate = get_config("BANK_CROP_LOAN_RATE")
        result = interest_costs(principal, months, moneylender_rate=30.0)
        assert result["bank"] == pytest.approx(
            _expected_interest(principal, bank_rate, months)
        )

    def test_kcc_uses_config_rate(self):
        """kcc cost uses KCC_RATE from config regardless of input."""
        principal, months = 100_000, 12
        kcc_rate = get_config("KCC_RATE")
        result = interest_costs(principal, months, moneylender_rate=30.0)
        assert result["kcc"] == pytest.approx(
            _expected_interest(principal, kcc_rate, months)
        )

    def test_interest_formula_correctness(self):
        """Verify formula: principal × rate/100 / 12 × months for all lenders."""
        principal, months = 75_000, 9
        ml_rate = 36.0
        bank_rate = get_config("BANK_CROP_LOAN_RATE")
        kcc_rate = get_config("KCC_RATE")

        result = interest_costs(principal, months, moneylender_rate=ml_rate)

        assert result["moneylender"] == pytest.approx(
            _expected_interest(principal, ml_rate, months)
        )
        assert result["bank"] == pytest.approx(
            _expected_interest(principal, bank_rate, months)
        )
        assert result["kcc"] == pytest.approx(
            _expected_interest(principal, kcc_rate, months)
        )


# ---------------------------------------------------------------------------
# Fallback to default moneylender rate
# ---------------------------------------------------------------------------

class TestDefaultMoneylenderRate:
    def test_no_rate_falls_back_to_default(self):
        """When moneylender_rate is None, MONEYLENDER_RATE_DEFAULT is used."""
        principal, months = 100_000, 6
        default_rate = get_config("MONEYLENDER_RATE_DEFAULT")

        result_no_rate = interest_costs(principal, months)
        expected = _expected_interest(principal, default_rate, months)
        assert result_no_rate["moneylender"] == pytest.approx(expected)

    def test_explicit_default_equals_no_rate(self):
        """Passing MONEYLENDER_RATE_DEFAULT explicitly equals omitting the arg."""
        principal, months = 80_000, 5
        default_rate = get_config("MONEYLENDER_RATE_DEFAULT")

        result_omitted = interest_costs(principal, months)
        result_explicit = interest_costs(principal, months,
                                         moneylender_rate=default_rate)
        assert result_omitted["moneylender"] == pytest.approx(
            result_explicit["moneylender"]
        )


# ---------------------------------------------------------------------------
# Rate range validation
# ---------------------------------------------------------------------------

class TestRateValidation:
    def test_rate_below_min_raises_value_error(self):
        """Rate below MONEYLENDER_RATE_MIN should raise ValueError."""
        rate_min = get_config("MONEYLENDER_RATE_MIN")
        with pytest.raises(ValueError, match="moneylender_rate"):
            interest_costs(100_000, 6, moneylender_rate=rate_min - 0.01)

    def test_negative_rate_raises_value_error(self):
        """Negative rate is always below minimum and should raise ValueError."""
        with pytest.raises(ValueError):
            interest_costs(100_000, 6, moneylender_rate=-1.0)

    def test_rate_above_max_raises_value_error(self):
        """Rate above MONEYLENDER_RATE_MAX should raise ValueError."""
        rate_max = get_config("MONEYLENDER_RATE_MAX")
        with pytest.raises(ValueError, match="moneylender_rate"):
            interest_costs(100_000, 6, moneylender_rate=rate_max + 0.01)

    def test_rate_at_min_boundary_is_valid(self):
        """Rate exactly at MONEYLENDER_RATE_MIN should not raise."""
        rate_min = get_config("MONEYLENDER_RATE_MIN")
        result = interest_costs(100_000, 6, moneylender_rate=rate_min)
        assert "moneylender" in result

    def test_rate_at_max_boundary_is_valid(self):
        """Rate exactly at MONEYLENDER_RATE_MAX should not raise."""
        rate_max = get_config("MONEYLENDER_RATE_MAX")
        result = interest_costs(100_000, 6, moneylender_rate=rate_max)
        assert "moneylender" in result

    def test_error_message_contains_range(self):
        """ValueError message mentions the valid range."""
        rate_max = get_config("MONEYLENDER_RATE_MAX")
        with pytest.raises(ValueError, match=str(int(rate_max))):
            interest_costs(100_000, 6, moneylender_rate=rate_max + 1.0)


# ---------------------------------------------------------------------------
# Relative ordering of lender costs
# ---------------------------------------------------------------------------

class TestLenderOrdering:
    def test_kcc_cheaper_than_bank(self):
        """KCC cost must always be less than bank cost (KCC_RATE < BANK_RATE)."""
        result = interest_costs(100_000, 12)
        assert result["kcc"] < result["bank"]

    def test_bank_cheaper_than_default_moneylender(self):
        """Bank cost must always be less than moneylender at default rate."""
        result = interest_costs(100_000, 12)
        assert result["bank"] < result["moneylender"]

    def test_kcc_cheapest_of_all(self):
        """KCC is cheapest, then bank, then moneylender (default rate)."""
        result = interest_costs(200_000, 6)
        assert result["kcc"] < result["bank"] < result["moneylender"]

    def test_ordering_holds_for_various_principals(self):
        """Cost ordering holds for a range of principal amounts."""
        for principal in [10_000, 50_000, 1_00_000, 3_00_000]:
            result = interest_costs(principal, 12)
            assert result["kcc"] <= result["bank"] <= result["moneylender"], (
                f"Ordering violated at principal={principal}: {result}"
            )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_months_returns_zero_interest(self):
        """Zero-month loan has zero interest cost for all lenders."""
        result = interest_costs(100_000, 0)
        assert result["moneylender"] == pytest.approx(0.0)
        assert result["bank"] == pytest.approx(0.0)
        assert result["kcc"] == pytest.approx(0.0)

    def test_zero_principal_returns_zero_interest(self):
        """Zero principal has zero interest regardless of rate or months."""
        result = interest_costs(0, 12)
        assert result["moneylender"] == pytest.approx(0.0)
        assert result["bank"] == pytest.approx(0.0)
        assert result["kcc"] == pytest.approx(0.0)

    def test_zero_principal_zero_months(self):
        """Both zero: all interest values are zero."""
        result = interest_costs(0, 0)
        for val in result.values():
            assert val == pytest.approx(0.0)

    def test_large_principal_no_error(self):
        """Large principal (above KCC limit) is accepted — comparator doesn't cap."""
        result = interest_costs(10_00_000, 12)
        assert all(v > 0 for v in result.values())

    def test_fractional_months_accepted(self):
        """Fractional months (e.g. 1.5) are accepted and produce correct results."""
        principal, months, rate = 100_000, 1.5, 24.0
        result = interest_costs(principal, months, moneylender_rate=rate)
        expected = _expected_interest(principal, rate, months)
        assert result["moneylender"] == pytest.approx(expected)
