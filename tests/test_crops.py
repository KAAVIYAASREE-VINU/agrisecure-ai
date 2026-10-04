"""
tests/test_crops.py — AgriSecure AI
=====================================

Unit tests for core/crops.py:
    available_crops, profit_scenarios, revenue_range_per_acre, profit_range_per_acre, break_even_price

Coverage
--------
Normal cases
- available_crops returns sorted crop names for a state/season
- available_crops returns empty list for unknown state/season
- profit_scenarios (>= 4 rows) returns 3 scenarios with correct structure
- profit_scenarios applies MSP floor when market price < MSP
- profit_scenarios includes gross revenue when no cost_override supplied
- profit_scenarios includes net profit when cost_override supplied
- revenue_range_per_acre returns (min, max) tuple for normal data (GROSS, no cost subtracted)
- profit_range_per_acre returns (min, max) net profit tuple when cost_per_acre given
- profit_range_per_acre returns None when cost_per_acre is None
- break_even_price returns correct price for exact inputs

Edge cases — fewer than 4 rows (MIN_RECORDS_FOR_COLOUR = 3)
- profit_scenarios with 2 rows sets low_data=True and does not crash
- profit_scenarios with 2 rows uses min/mean/max instead of quantiles
- revenue_range_per_acre with 2 rows still returns a tuple (not None)

Edge cases — missing MSP
- profit_scenarios with no MSP data sets msp_available=False
- profit_scenarios with no MSP does not apply MSP floor
- revenue_range_per_acre with no MSP uses market price directly
- available_crops with no matching data returns empty list

Other edge cases
- profit_scenarios with empty yield DataFrame sets no_data=True
- revenue_range_per_acre with empty yield DataFrame returns None
- break_even_price raises ValueError for zero yield
- break_even_price raises ValueError for negative yield
- crop matching is case-insensitive
"""

import pytest
import pandas as pd

from core.crops import (
    available_crops,
    profit_scenarios,
    revenue_range_per_acre,
    profit_range_per_acre,
    break_even_price,
)
from data.clean_data import PLACEHOLDER_TAG


# ---------------------------------------------------------------------------
# DataFrame builders
# ---------------------------------------------------------------------------

def _make_yp(rows: list[tuple]) -> pd.DataFrame:
    """Build a yield-price DataFrame from (state, season, crop, year, yield_q, price_q) tuples."""
    return pd.DataFrame(
        rows,
        columns=["state", "season", "crop", "year",
                 "yield_quintal_per_acre", "price_per_quintal"],
    )


def _make_msp(rows: list[tuple]) -> pd.DataFrame:
    """Build an MSP DataFrame from (crop, year, msp_per_quintal) tuples."""
    return pd.DataFrame(rows, columns=["crop", "year", "msp_per_quintal"])


def _empty_msp() -> pd.DataFrame:
    return pd.DataFrame(columns=["crop", "year", "msp_per_quintal"])


# Reusable data: 5 rows of paddy/Kuruvai/Tamil Nadu (enough for percentile path)
_PADDY_5 = [
    ("Tamil Nadu", "Kuruvai", "paddy", 2018, 14.0, 1720.0),
    ("Tamil Nadu", "Kuruvai", "paddy", 2019, 15.5, 1780.0),
    ("Tamil Nadu", "Kuruvai", "paddy", 2020, 16.0, 1840.0),
    ("Tamil Nadu", "Kuruvai", "paddy", 2021, 15.0, 1950.0),
    ("Tamil Nadu", "Kuruvai", "paddy", 2022, 17.5, 2050.0),
]

# 2 rows of paddy — triggers the low-data path (< MIN_RECORDS_FOR_COLOUR = 3)
_PADDY_2 = [
    ("Tamil Nadu", "Kuruvai", "paddy", 2021, 14.0, 1800.0),
    ("Tamil Nadu", "Kuruvai", "paddy", 2022, 18.0, 2200.0),
]

_MSP_PADDY = [("paddy", 2022, 2015.0)]


# ---------------------------------------------------------------------------
# available_crops
# ---------------------------------------------------------------------------

class TestAvailableCrops:
    def test_returns_crops_for_valid_state_season(self):
        """Returns sorted unique crop names matching state and season."""
        df = _make_yp(
            _PADDY_5
            + [("Tamil Nadu", "Kuruvai", "maize", 2020, 12.0, 1360.0)]
        )
        result = available_crops("Tamil Nadu", "Kuruvai", df)
        assert result == ["maize", "paddy"]

    def test_single_crop_returned_as_list(self):
        """Single matching crop is returned as a one-element list."""
        df = _make_yp(_PADDY_5)
        result = available_crops("Tamil Nadu", "Kuruvai", df)
        assert result == ["paddy"]

    def test_unknown_state_returns_empty_list(self):
        """No matching state → empty list."""
        df = _make_yp(_PADDY_5)
        result = available_crops("Maharashtra", "Kuruvai", df)
        assert result == []

    def test_unknown_season_returns_empty_list(self):
        """No matching season → empty list."""
        df = _make_yp(_PADDY_5)
        result = available_crops("Tamil Nadu", "Rabi", df)
        assert result == []

    def test_empty_dataframe_returns_empty_list(self):
        """Empty DataFrame → empty list."""
        df = _make_yp([])
        result = available_crops("Tamil Nadu", "Kuruvai", df)
        assert result == []

    def test_crop_names_returned_lowercase(self):
        """Crop names are lowercased in the result."""
        rows = [("Tamil Nadu", "Kuruvai", "Paddy", 2021, 15.0, 1900.0)]
        df = _make_yp(rows)
        result = available_crops("Tamil Nadu", "Kuruvai", df)
        assert "paddy" in result

    def test_duplicates_deduplicated(self):
        """Multiple rows for the same crop are deduplicated."""
        df = _make_yp(_PADDY_5)  # 5 rows all for paddy
        result = available_crops("Tamil Nadu", "Kuruvai", df)
        assert result.count("paddy") == 1


# ---------------------------------------------------------------------------
# profit_scenarios — normal cases (5 rows, >= MIN_RECORDS_FOR_COLOUR)
# ---------------------------------------------------------------------------

class TestProfitScenariosNormal:
    def test_returns_three_scenarios(self):
        """Three scenarios (bad, normal, good) are returned."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert len(result["scenarios"]) == 3

    def test_scenario_labels(self):
        """Scenarios are labelled bad, normal, good in order."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        labels = [s["label"] for s in result["scenarios"]]
        assert labels == ["bad", "normal", "good"]

    def test_scenario_keys_present(self):
        """Each scenario dict has the expected keys."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        expected_keys = {
            "label", "yield_per_acre", "price_per_quintal",
            "effective_price", "revenue_per_acre", "revenue_total",
            "profit_per_acre", "profit_total",
        }
        for scenario in result["scenarios"]:
            assert set(scenario.keys()) == expected_keys

    def test_revenue_per_acre_equals_yield_times_price(self):
        """revenue_per_acre = yield_per_acre × effective_price."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        for s in result["scenarios"]:
            assert s["revenue_per_acre"] == pytest.approx(
                s["yield_per_acre"] * s["effective_price"]
            )

    def test_revenue_total_scaled_by_acres(self):
        """revenue_total = revenue_per_acre × land_acres."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 2.0, df, _empty_msp())
        for s in result["scenarios"]:
            assert s["revenue_total"] == pytest.approx(s["revenue_per_acre"] * 2.0)

    def test_low_data_flag_false_for_5_rows(self):
        """low_data=False when >= MIN_RECORDS_FOR_COLOUR rows are available."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert result["low_data"] is False

    def test_no_data_flag_false_for_5_rows(self):
        """no_data=False when matching rows exist."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert result["no_data"] is False

    def test_profit_none_when_no_cost_override(self):
        """profit_per_acre and profit_total are None when cost_override is not given."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        for s in result["scenarios"]:
            assert s["profit_per_acre"] is None
            assert s["profit_total"] is None

    def test_profit_calculated_when_cost_override_given(self):
        """profit_total = revenue_total - cost_override when cost_override is provided."""
        df = _make_yp(_PADDY_5)
        cost = 10000.0  # ₹ total for 1 acre
        result = profit_scenarios(
            "paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp(),
            cost_override=cost,
        )
        for s in result["scenarios"]:
            assert s["profit_total"] == pytest.approx(s["revenue_total"] - cost)
            assert s["profit_per_acre"] == pytest.approx(s["revenue_per_acre"] - cost)

    def test_good_scenario_higher_than_bad(self):
        """Good scenario revenue is >= bad scenario revenue."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        bad  = result["scenarios"][0]["revenue_per_acre"]
        good = result["scenarios"][2]["revenue_per_acre"]
        assert good >= bad

    def test_case_insensitive_crop_match(self):
        """Crop name matching is case-insensitive."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("Paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert result["no_data"] is False
        assert len(result["scenarios"]) == 3


# ---------------------------------------------------------------------------
# profit_scenarios — MSP floor
# ---------------------------------------------------------------------------

class TestProfitScenariosWithMSP:
    def test_effective_price_uses_msp_when_higher(self):
        """effective_price = MSP when market price < MSP."""
        # Use a single-row scenario where the price is deliberately below MSP.
        rows = [
            ("Tamil Nadu", "Kuruvai", "paddy", 2021, 15.0, 1500.0),
            ("Tamil Nadu", "Kuruvai", "paddy", 2022, 16.0, 1550.0),
            ("Tamil Nadu", "Kuruvai", "paddy", 2023, 14.0, 1600.0),
            ("Tamil Nadu", "Kuruvai", "paddy", 2024, 17.0, 1650.0),
        ]
        df = _make_yp(rows)
        # MSP of 2000 is above all market prices
        msp_df = _make_msp([("paddy", 2024, 2000.0)])
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, msp_df)
        for s in result["scenarios"]:
            assert s["effective_price"] == pytest.approx(2000.0)

    def test_effective_price_uses_market_when_higher_than_msp(self):
        """effective_price = market price when market price > MSP."""
        rows = [
            ("Tamil Nadu", "Kuruvai", "paddy", 2021, 15.0, 3000.0),
            ("Tamil Nadu", "Kuruvai", "paddy", 2022, 16.0, 3100.0),
            ("Tamil Nadu", "Kuruvai", "paddy", 2023, 14.0, 3200.0),
            ("Tamil Nadu", "Kuruvai", "paddy", 2024, 17.0, 3300.0),
        ]
        df = _make_yp(rows)
        msp_df = _make_msp([("paddy", 2024, 2015.0)])
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, msp_df)
        for s in result["scenarios"]:
            assert s["effective_price"] >= s["price_per_quintal"]

    def test_msp_available_true_when_msp_present(self):
        """msp_available=True and msp is set when MSP data exists."""
        df = _make_yp(_PADDY_5)
        msp_df = _make_msp(_MSP_PADDY)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, msp_df)
        assert result["msp_available"] is True
        assert result["msp"] == pytest.approx(2015.0)

    def test_msp_available_false_when_no_msp(self):
        """msp_available=False and msp is None when MSP data is absent."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert result["msp_available"] is False
        assert result["msp"] is None

    def test_msp_available_false_when_crop_not_in_msp(self):
        """msp_available=False when MSP exists but not for this crop."""
        df = _make_yp(_PADDY_5)
        msp_df = _make_msp([("wheat", 2022, 2015.0)])  # wrong crop
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, msp_df)
        assert result["msp_available"] is False


# ---------------------------------------------------------------------------
# profit_scenarios — fewer than 4 rows (low_data path)
# ---------------------------------------------------------------------------

class TestProfitScenariosLowData:
    def test_2_rows_sets_low_data_true(self):
        """2 rows (< MIN_RECORDS_FOR_COLOUR=3) → low_data=True."""
        df = _make_yp(_PADDY_2)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert result["low_data"] is True

    def test_2_rows_still_returns_3_scenarios(self):
        """Even with 2 rows, all 3 scenarios are returned without crashing."""
        df = _make_yp(_PADDY_2)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert len(result["scenarios"]) == 3
        assert result["no_data"] is False

    def test_2_rows_bad_uses_min_values(self):
        """With 2 rows, bad scenario uses min yield and min price."""
        df = _make_yp(_PADDY_2)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        bad = result["scenarios"][0]
        # _PADDY_2 min yield = 14.0, min price = 1800.0
        assert bad["yield_per_acre"] == pytest.approx(14.0)
        assert bad["price_per_quintal"] == pytest.approx(1800.0)

    def test_2_rows_good_uses_max_values(self):
        """With 2 rows, good scenario uses max yield and max price."""
        df = _make_yp(_PADDY_2)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        good = result["scenarios"][2]
        # _PADDY_2 max yield = 18.0, max price = 2200.0
        assert good["yield_per_acre"] == pytest.approx(18.0)
        assert good["price_per_quintal"] == pytest.approx(2200.0)

    def test_2_rows_normal_uses_mean_values(self):
        """With 2 rows, normal scenario uses mean yield and mean price."""
        df = _make_yp(_PADDY_2)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        normal = result["scenarios"][1]
        # _PADDY_2 mean yield = (14+18)/2 = 16.0, mean price = (1800+2200)/2 = 2000.0
        assert normal["yield_per_acre"] == pytest.approx(16.0)
        assert normal["price_per_quintal"] == pytest.approx(2000.0)

    def test_1_row_does_not_crash(self):
        """Even a single row is handled gracefully (low_data=True)."""
        rows = [("Tamil Nadu", "Kuruvai", "paddy", 2022, 16.0, 1900.0)]
        df = _make_yp(rows)
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert result["low_data"] is True
        assert len(result["scenarios"]) == 3


# ---------------------------------------------------------------------------
# profit_scenarios — empty / missing data
# ---------------------------------------------------------------------------

class TestProfitScenariosNoData:
    def test_no_matching_rows_sets_no_data_true(self):
        """no_data=True when no rows match the state/season/crop."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("wheat", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert result["no_data"] is True

    def test_no_data_returns_empty_scenarios_list(self):
        """scenarios list is empty when no data is found."""
        df = _make_yp(_PADDY_5)
        result = profit_scenarios("wheat", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert result["scenarios"] == []

    def test_empty_dataframe_no_data(self):
        """Empty DataFrame → no_data=True."""
        df = _make_yp([])
        result = profit_scenarios("paddy", "Tamil Nadu", "Kuruvai", 1.0, df, _empty_msp())
        assert result["no_data"] is True


# ---------------------------------------------------------------------------
# profit_range_per_acre
# ---------------------------------------------------------------------------

class TestRevenueRangePerAcre:
    def test_returns_tuple_for_normal_data(self):
        """Returns a (min, max) tuple when data exists."""
        df = _make_yp(_PADDY_5)
        result = revenue_range_per_acre("paddy", "Tamil Nadu", "Kuruvai", df, _empty_msp())
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_max_greater_than_or_equal_min(self):
        """Max revenue >= min revenue."""
        df = _make_yp(_PADDY_5)
        min_r, max_r = revenue_range_per_acre("paddy", "Tamil Nadu", "Kuruvai", df, _empty_msp())
        assert max_r >= min_r

    def test_returns_none_for_no_data(self):
        """Returns None when no matching rows exist."""
        df = _make_yp(_PADDY_5)
        result = revenue_range_per_acre("wheat", "Tamil Nadu", "Kuruvai", df, _empty_msp())
        assert result is None

    def test_returns_none_for_empty_dataframe(self):
        """Returns None for an empty DataFrame."""
        df = _make_yp([])
        result = revenue_range_per_acre("paddy", "Tamil Nadu", "Kuruvai", df, _empty_msp())
        assert result is None

    def test_2_rows_still_returns_tuple(self):
        """With only 2 rows (low data), a tuple is still returned."""
        df = _make_yp(_PADDY_2)
        result = revenue_range_per_acre("paddy", "Tamil Nadu", "Kuruvai", df, _empty_msp())
        assert result is not None
        assert isinstance(result, tuple)
        min_r, max_r = result
        assert max_r >= min_r

    def test_msp_floor_applied_when_price_below_msp(self):
        """Min revenue uses MSP floor when market price < MSP."""
        rows = [
            ("Tamil Nadu", "Kuruvai", "paddy", 2021, 15.0, 1500.0),
            ("Tamil Nadu", "Kuruvai", "paddy", 2022, 16.0, 1550.0),
            ("Tamil Nadu", "Kuruvai", "paddy", 2023, 14.0, 1600.0),
            ("Tamil Nadu", "Kuruvai", "paddy", 2024, 17.0, 1650.0),
        ]
        df = _make_yp(rows)
        msp_df = _make_msp([("paddy", 2024, 2000.0)])
        min_r, max_r = revenue_range_per_acre("paddy", "Tamil Nadu", "Kuruvai", df, msp_df)
        # Without MSP floor, min = 14.0 * 1500.0 = 21000
        # With MSP floor, min >= 14.0 * 2000.0 = 28000
        assert min_r >= 14.0 * 2000.0

    def test_no_msp_uses_market_price(self):
        """When MSP is unavailable, market price is used directly."""
        df = _make_yp(_PADDY_5)
        min_r, max_r = revenue_range_per_acre("paddy", "Tamil Nadu", "Kuruvai", df, _empty_msp())
        # Verify the min is computed from the P25 values (not zero or None)
        assert min_r > 0.0
        assert max_r > min_r

    def test_case_insensitive_crop_match(self):
        """Crop name is matched case-insensitively."""
        df = _make_yp(_PADDY_5)
        result = revenue_range_per_acre("PADDY", "Tamil Nadu", "Kuruvai", df, _empty_msp())
        assert result is not None


# ---------------------------------------------------------------------------
# break_even_price
# ---------------------------------------------------------------------------

class TestBreakEvenPrice:
    def test_exact_calculation(self):
        """break_even = total_cost / yield_per_acre."""
        result = break_even_price(total_cost_per_acre=15000.0, yield_per_acre=15.0)
        assert result == pytest.approx(1000.0)

    def test_fractional_yield(self):
        """Works correctly for non-integer yields."""
        result = break_even_price(total_cost_per_acre=12000.0, yield_per_acre=7.5)
        assert result == pytest.approx(1600.0)

    def test_zero_yield_raises_value_error(self):
        """Zero yield raises ValueError."""
        with pytest.raises(ValueError):
            break_even_price(total_cost_per_acre=10000.0, yield_per_acre=0.0)

    def test_negative_yield_raises_value_error(self):
        """Negative yield raises ValueError."""
        with pytest.raises(ValueError):
            break_even_price(total_cost_per_acre=10000.0, yield_per_acre=-5.0)

    def test_zero_cost_gives_zero_break_even(self):
        """Zero cost → zero break-even price."""
        result = break_even_price(total_cost_per_acre=0.0, yield_per_acre=10.0)
        assert result == pytest.approx(0.0)

    def test_high_cost_example(self):
        """High cost scenario computes correctly."""
        result = break_even_price(total_cost_per_acre=50000.0, yield_per_acre=25.0)
        assert result == pytest.approx(2000.0)


# ---------------------------------------------------------------------------
# rank_top3
# Changed in fix: dict keys now include min_profit_per_acre, max_profit_per_acre,
# cost_per_acre is now required; passing None returns [].
# ---------------------------------------------------------------------------

from core.crops import rank_top3


def _make_multi_crop_yp() -> pd.DataFrame:
    """Three crops with enough rows for percentile-based CV calculation."""
    rows = [
        # paddy — moderate yield, moderate price → medium revenue, moderate CV
        ("Tamil Nadu", "Kharif", "paddy", 2018, 14.0, 1700.0),
        ("Tamil Nadu", "Kharif", "paddy", 2019, 15.0, 1800.0),
        ("Tamil Nadu", "Kharif", "paddy", 2020, 16.0, 1850.0),
        ("Tamil Nadu", "Kharif", "paddy", 2021, 14.5, 1750.0),
        # maize — lower yield/price overall → lower revenue, low CV (consistent)
        ("Tamil Nadu", "Kharif", "maize", 2018, 10.0, 1300.0),
        ("Tamil Nadu", "Kharif", "maize", 2019, 10.1, 1310.0),
        ("Tamil Nadu", "Kharif", "maize", 2020, 10.2, 1320.0),
        ("Tamil Nadu", "Kharif", "maize", 2021, 10.0, 1305.0),
        # cotton — high yield/price → high revenue, but high CV (volatile)
        ("Tamil Nadu", "Kharif", "cotton", 2018, 5.0,  5000.0),
        ("Tamil Nadu", "Kharif", "cotton", 2019, 20.0, 1000.0),
        ("Tamil Nadu", "Kharif", "cotton", 2020, 5.0,  5000.0),
        ("Tamil Nadu", "Kharif", "cotton", 2021, 20.0, 1000.0),
    ]
    return _make_yp(rows)


class TestRankTop3:
    def test_returns_list(self):
        """rank_top3 always returns a list."""
        df = _make_multi_crop_yp()
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        assert isinstance(result, list)

    def test_normal_case_returns_up_to_3_results(self):
        """With 3+ crops, returns exactly 3 results."""
        df = _make_multi_crop_yp()
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        assert len(result) == 3

    def test_result_dict_keys(self):
        """Each result dict has the required keys."""
        df = _make_multi_crop_yp()
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        required_keys = {"crop", "min_revenue_per_acre", "max_revenue_per_acre",
                         "min_profit_per_acre", "max_profit_per_acre",
                         "cv", "risk_colour", "rank"}
        for item in result:
            assert set(item.keys()) == required_keys

    def test_ranks_are_1_2_3(self):
        """Ranks are exactly 1, 2, 3 in order."""
        df = _make_multi_crop_yp()
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        assert [r["rank"] for r in result] == [1, 2, 3]

    def test_risk_colour_is_valid(self):
        """risk_colour is one of 'green', 'yellow', 'red'."""
        df = _make_multi_crop_yp()
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        for item in result:
            assert item["risk_colour"] in ("green", "yellow", "red")

    def test_cv_is_non_negative(self):
        """CV values are >= 0."""
        df = _make_multi_crop_yp()
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        for item in result:
            assert item["cv"] >= 0.0

    def test_max_revenue_gte_min_revenue(self):
        """max_revenue_per_acre >= min_revenue_per_acre for every ranked crop (gross)."""
        df = _make_multi_crop_yp()
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        for item in result:
            assert item["max_revenue_per_acre"] >= item["min_revenue_per_acre"]

    def test_no_crops_returns_empty(self):
        """No crops for state/season → []."""
        df = _make_multi_crop_yp()
        result = rank_top3("Maharashtra", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        assert result == []

    def test_empty_dataframe_returns_empty(self):
        """Empty DataFrame → []."""
        df = _make_yp([])
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        assert result == []

    def test_fewer_than_3_crops_returns_all_with_correct_ranks(self):
        """With only 2 available crops, returns 2 results ranked 1 and 2."""
        rows = [
            ("Tamil Nadu", "Kharif", "paddy", 2018, 14.0, 1700.0),
            ("Tamil Nadu", "Kharif", "paddy", 2019, 15.0, 1800.0),
            ("Tamil Nadu", "Kharif", "paddy", 2020, 16.0, 1850.0),
            ("Tamil Nadu", "Kharif", "maize", 2018, 10.0, 1300.0),
            ("Tamil Nadu", "Kharif", "maize", 2019, 10.1, 1310.0),
            ("Tamil Nadu", "Kharif", "maize", 2020, 10.2, 1320.0),
        ]
        df = _make_yp(rows)
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        assert len(result) == 2
        assert [r["rank"] for r in result] == [1, 2]

    def test_exactly_1_crop_returns_rank_1(self):
        """Single available crop → returns one result with rank=1."""
        rows = [
            ("Tamil Nadu", "Kharif", "paddy", 2018, 14.0, 1700.0),
            ("Tamil Nadu", "Kharif", "paddy", 2019, 15.0, 1800.0),
            ("Tamil Nadu", "Kharif", "paddy", 2020, 16.0, 1850.0),
        ]
        df = _make_yp(rows)
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        assert len(result) == 1
        assert result[0]["rank"] == 1

    def test_high_revenue_low_risk_beats_low_revenue_high_risk(self):
        """A high-revenue, low-risk crop ranks above a lower-revenue, high-risk crop.

        'safe_crop' has consistently high yield/price (low CV, high mean revenue).
        'volatile_crop' has wildly variable yield/price (high CV) and a much
        lower mean revenue, so safe_crop should rank #1 under any sensible
        revenue-weighted scoring.
        """
        rows = [
            # safe_crop — very consistent, high revenue (~40 000 ₹/acre each year)
            ("Tamil Nadu", "Kharif", "safe_crop", 2018, 20.0, 2000.0),
            ("Tamil Nadu", "Kharif", "safe_crop", 2019, 20.0, 2000.0),
            ("Tamil Nadu", "Kharif", "safe_crop", 2020, 20.0, 2000.0),
            ("Tamil Nadu", "Kharif", "safe_crop", 2021, 20.0, 2000.0),
            # volatile_crop — wildly swinging, mean revenue ~6 250 ₹/acre (much lower)
            #   year A: 1 quintal × ₹500  = ₹500
            #   year B: 5 quintals × ₹2 000 = ₹10 000
            #   mean ≈ ₹5 250/acre; CV >> 1
            ("Tamil Nadu", "Kharif", "volatile_crop", 2018,  1.0,  500.0),
            ("Tamil Nadu", "Kharif", "volatile_crop", 2019,  5.0, 2000.0),
            ("Tamil Nadu", "Kharif", "volatile_crop", 2020,  1.0,  500.0),
            ("Tamil Nadu", "Kharif", "volatile_crop", 2021,  5.0, 2000.0),
        ]
        df = _make_yp(rows)
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        assert len(result) == 2
        rank1_crop = result[0]["crop"]
        assert rank1_crop == "safe_crop", (
            f"Expected 'safe_crop' at rank 1 but got '{rank1_crop}'"
        )

    def test_high_profit_high_risk_vs_lower_profit_lower_risk(self):
        """A genuinely lower-revenue crop with very low risk can still rank above
        a higher-revenue but extremely volatile crop, depending on the scoring weights.

        Here we ensure the ranking is at least deterministic and consistent.
        The exact winner depends on the 80/20 weight: the high-revenue crop is expected
        to win when its revenue advantage is large enough.
        """
        rows = [
            # high_rev_crop — high mean revenue but moderate-high CV
            ("Tamil Nadu", "Kharif", "high_rev", 2018,  5.0, 3000.0),
            ("Tamil Nadu", "Kharif", "high_rev", 2019, 30.0,  500.0),
            ("Tamil Nadu", "Kharif", "high_rev", 2020, 25.0, 4000.0),
            ("Tamil Nadu", "Kharif", "high_rev", 2021, 10.0, 1000.0),
            # low_rev_crop — lower revenue but rock-steady
            ("Tamil Nadu", "Kharif", "low_rev", 2018, 10.0, 1000.0),
            ("Tamil Nadu", "Kharif", "low_rev", 2019, 10.0, 1000.0),
            ("Tamil Nadu", "Kharif", "low_rev", 2020, 10.0, 1000.0),
            ("Tamil Nadu", "Kharif", "low_rev", 2021, 10.0, 1000.0),
        ]
        df = _make_yp(rows)
        result = rank_top3("Tamil Nadu", "Kharif", 1.0, df, _empty_msp(), cost_per_acre=1000.0)
        assert len(result) == 2
        # Scores must be calculated consistently — verify ranks are 1 and 2
        assert result[0]["rank"] == 1
        assert result[1]["rank"] == 2
        # The low_rev crop should have cv=0 (green), verifying CV is captured
        low_rev_entry = next(r for r in result if r["crop"] == "low_rev")
        assert low_rev_entry["cv"] == pytest.approx(0.0)
        assert low_rev_entry["risk_colour"] == "green"
