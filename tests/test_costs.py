"""
tests/test_costs.py — AgriSecure AI
=====================================

Unit tests for core/costs.py :: estimate_costs.

Coverage
--------
- Normal case: matching rows found, returns correctly scaled costs
- No matching rows: returns all zeros and placeholder=True
- Overrides applied correctly (one component overridden)
- Override above COST_COMPONENT_MAX raises ValueError
- Override below COST_COMPONENT_MIN (negative) raises ValueError
- Invalid override key raises ValueError
- placeholder flag correctly set when note column contains PLACEHOLDER_TAG
- placeholder flag False when note column is absent
- Zero acres: multiplies all components by 0
- Multiple matching years: mean is taken, then scaled
"""

import pytest
import pandas as pd

from config import get_config
from data.clean_data import PLACEHOLDER_TAG
from core.costs import estimate_costs, COST_COMPONENTS


# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

def _make_cost_df(rows: list[dict], include_note: bool = True) -> pd.DataFrame:
    """Build a minimal cost DataFrame from a list of row dicts."""
    cols = ["state", "season", "crop", "year",
            "seed", "fertilizer", "labour", "irrigation", "other"]
    df = pd.DataFrame(rows, columns=cols)
    if include_note:
        df["note"] = ""          # default: no PLACEHOLDER tag
    return df


def _paddy_row(year=2021, seed=1000, fertilizer=2000, labour=3000,
               irrigation=1000, other=500, note="") -> dict:
    """Return a single paddy row dict for Tamil Nadu / Kuruvai."""
    return {
        "state": "Tamil Nadu",
        "season": "Kuruvai",
        "crop": "paddy",
        "year": year,
        "seed": seed,
        "fertilizer": fertilizer,
        "labour": labour,
        "irrigation": irrigation,
        "other": other,
        "note": note,
    }


# ---------------------------------------------------------------------------
# Normal case
# ---------------------------------------------------------------------------

class TestNormalCase:
    def test_single_row_1_acre(self):
        """Single matching row, 1 acre — result equals the per-acre values."""
        row = _paddy_row(seed=1000, fertilizer=2000, labour=3000,
                         irrigation=1000, other=500)
        df = pd.DataFrame([row])
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0)

        assert result["seed"] == pytest.approx(1000.0)
        assert result["fertilizer"] == pytest.approx(2000.0)
        assert result["labour"] == pytest.approx(3000.0)
        assert result["irrigation"] == pytest.approx(1000.0)
        assert result["other"] == pytest.approx(500.0)
        assert result["total"] == pytest.approx(7500.0)

    def test_single_row_scaled_by_acres(self):
        """Costs are multiplied by the acres value."""
        row = _paddy_row(seed=1000, fertilizer=2000, labour=3000,
                         irrigation=1000, other=500)
        df = pd.DataFrame([row])
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=2.5)

        assert result["seed"] == pytest.approx(2500.0)
        assert result["total"] == pytest.approx(7500.0 * 2.5)

    def test_returns_all_required_keys(self):
        """Result dict contains all expected keys."""
        df = pd.DataFrame([_paddy_row()])
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0)

        assert set(result.keys()) == {
            "seed", "fertilizer", "labour", "irrigation", "other", "total", "placeholder"
        }

    def test_crop_name_case_insensitive(self):
        """Crop match is case-insensitive (CSV stores lowercase)."""
        df = pd.DataFrame([_paddy_row()])   # CSV has "paddy" (lowercase)
        result = estimate_costs(df, "Paddy", "Tamil Nadu", "Kuruvai", acres=1.0)

        assert result["total"] > 0.0  # found the row


# ---------------------------------------------------------------------------
# No matching rows
# ---------------------------------------------------------------------------

class TestNoMatchingRows:
    def test_wrong_crop_returns_zeros(self):
        """No data for the requested crop → all zeros, placeholder=True."""
        df = pd.DataFrame([_paddy_row()])
        result = estimate_costs(df, "wheat", "Tamil Nadu", "Kuruvai", acres=1.0)

        for comp in COST_COMPONENTS:
            assert result[comp] == 0.0
        assert result["total"] == 0.0
        assert result["placeholder"] is True

    def test_wrong_season_returns_zeros(self):
        """No data for the requested season → all zeros, placeholder=True."""
        df = pd.DataFrame([_paddy_row()])   # season = Kuruvai
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Rabi", acres=1.0)

        assert result["total"] == 0.0
        assert result["placeholder"] is True

    def test_wrong_state_returns_zeros(self):
        """No data for the requested state → all zeros, placeholder=True."""
        df = pd.DataFrame([_paddy_row()])   # state = Tamil Nadu
        result = estimate_costs(df, "paddy", "Maharashtra", "Kuruvai", acres=1.0)

        assert result["total"] == 0.0
        assert result["placeholder"] is True


# ---------------------------------------------------------------------------
# Multiple rows (mean)
# ---------------------------------------------------------------------------

class TestMultipleRows:
    def test_mean_taken_across_years(self):
        """When multiple years match, the mean per-acre cost is used."""
        rows = [
            _paddy_row(year=2021, seed=1000, fertilizer=2000, labour=3000,
                       irrigation=1000, other=500),
            _paddy_row(year=2022, seed=2000, fertilizer=4000, labour=6000,
                       irrigation=2000, other=1000),
        ]
        df = pd.DataFrame(rows)
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0)

        # Expected mean per acre
        assert result["seed"] == pytest.approx(1500.0)
        assert result["fertilizer"] == pytest.approx(3000.0)
        assert result["labour"] == pytest.approx(4500.0)
        assert result["irrigation"] == pytest.approx(1500.0)
        assert result["other"] == pytest.approx(750.0)
        assert result["total"] == pytest.approx(11250.0)

    def test_mean_scaled_by_acres(self):
        """Mean per-acre cost is scaled by acres (multiple rows)."""
        rows = [
            _paddy_row(year=2021, seed=1000, fertilizer=2000, labour=3000,
                       irrigation=1000, other=500),
            _paddy_row(year=2022, seed=2000, fertilizer=4000, labour=6000,
                       irrigation=2000, other=1000),
        ]
        df = pd.DataFrame(rows)
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=2.0)

        assert result["seed"] == pytest.approx(3000.0)          # 1500 * 2
        assert result["total"] == pytest.approx(11250.0 * 2.0)


# ---------------------------------------------------------------------------
# Overrides
# ---------------------------------------------------------------------------

class TestOverrides:
    def test_single_override_replaces_component(self):
        """Providing one override replaces only that component's value."""
        df = pd.DataFrame([_paddy_row(seed=1000, fertilizer=2000, labour=3000,
                                      irrigation=1000, other=500)])
        result = estimate_costs(
            df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0,
            overrides={"labour": 5000.0}
        )

        assert result["seed"] == pytest.approx(1000.0)        # unchanged
        assert result["labour"] == pytest.approx(5000.0)      # overridden
        assert result["total"] == pytest.approx(
            1000 + 2000 + 5000 + 1000 + 500
        )

    def test_multiple_overrides(self):
        """Multiple overrides all applied correctly."""
        df = pd.DataFrame([_paddy_row(seed=1000, fertilizer=2000, labour=3000,
                                      irrigation=1000, other=500)])
        result = estimate_costs(
            df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0,
            overrides={"seed": 1500.0, "other": 800.0}
        )

        assert result["seed"] == pytest.approx(1500.0)
        assert result["other"] == pytest.approx(800.0)
        assert result["total"] == pytest.approx(1500 + 2000 + 3000 + 1000 + 800)

    def test_override_zero_is_valid(self):
        """Override to exactly COST_COMPONENT_MIN (0.0) is accepted."""
        df = pd.DataFrame([_paddy_row(seed=1000)])
        result = estimate_costs(
            df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0,
            overrides={"seed": 0.0}
        )
        assert result["seed"] == pytest.approx(0.0)

    def test_override_at_max_is_valid(self):
        """Override at exactly COST_COMPONENT_MAX is accepted."""
        cost_max = get_config("COST_COMPONENT_MAX")
        df = pd.DataFrame([_paddy_row()])
        result = estimate_costs(
            df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0,
            overrides={"seed": cost_max}
        )
        assert result["seed"] == pytest.approx(cost_max)


# ---------------------------------------------------------------------------
# Override validation errors
# ---------------------------------------------------------------------------

class TestOverrideValidationErrors:
    def test_override_above_max_raises_value_error(self):
        """Override above COST_COMPONENT_MAX raises ValueError."""
        cost_max = get_config("COST_COMPONENT_MAX")
        df = pd.DataFrame([_paddy_row()])
        with pytest.raises(ValueError, match="seed"):
            estimate_costs(
                df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0,
                overrides={"seed": cost_max + 1.0}
            )

    def test_override_negative_raises_value_error(self):
        """Negative override (below COST_COMPONENT_MIN = 0) raises ValueError."""
        df = pd.DataFrame([_paddy_row()])
        with pytest.raises(ValueError, match="fertilizer"):
            estimate_costs(
                df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0,
                overrides={"fertilizer": -100.0}
            )

    def test_invalid_override_key_raises_value_error(self):
        """An unrecognised override key raises ValueError."""
        df = pd.DataFrame([_paddy_row()])
        with pytest.raises(ValueError, match="profit"):
            estimate_costs(
                df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0,
                overrides={"profit": 500.0}
            )


# ---------------------------------------------------------------------------
# Placeholder flag
# ---------------------------------------------------------------------------

class TestPlaceholderFlag:
    def test_placeholder_true_when_note_is_tag(self):
        """placeholder=True when any matching row has note == PLACEHOLDER_TAG."""
        row = _paddy_row(note=PLACEHOLDER_TAG)
        df = pd.DataFrame([row])
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0)

        assert result["placeholder"] is True

    def test_placeholder_false_when_note_is_empty(self):
        """placeholder=False when no matching row has the PLACEHOLDER_TAG."""
        row = _paddy_row(note="")        # empty note — not a placeholder
        df = pd.DataFrame([row])
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0)

        assert result["placeholder"] is False

    def test_placeholder_true_when_any_row_tagged(self):
        """placeholder=True if at least one of several rows is tagged."""
        rows = [
            _paddy_row(year=2021, note=""),
            _paddy_row(year=2022, note=PLACEHOLDER_TAG),
        ]
        df = pd.DataFrame(rows)
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0)

        assert result["placeholder"] is True

    def test_placeholder_false_when_note_column_absent(self):
        """placeholder=False when the DataFrame has no note column."""
        row = _paddy_row()
        df = pd.DataFrame([row])
        df = df.drop(columns=["note"])   # remove note column

        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0)
        assert result["placeholder"] is False

    def test_no_rows_always_placeholder(self):
        """No matching rows always yields placeholder=True regardless of notes."""
        df = pd.DataFrame([_paddy_row()])
        result = estimate_costs(df, "wheat", "Tamil Nadu", "Kuruvai", acres=1.0)

        assert result["placeholder"] is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_acres_all_components_zero(self):
        """Multiplying by 0 acres returns all components as 0.0."""
        df = pd.DataFrame([_paddy_row(seed=1000, fertilizer=2000, labour=3000,
                                      irrigation=1000, other=500)])
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=0.0)

        for comp in COST_COMPONENTS:
            assert result[comp] == pytest.approx(0.0)
        assert result["total"] == pytest.approx(0.0)

    def test_no_overrides_argument(self):
        """Calling without overrides kwarg behaves same as overrides=None."""
        df = pd.DataFrame([_paddy_row(seed=1000)])
        result_no_kw = estimate_costs(
            df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0
        )
        result_none = estimate_costs(
            df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0, overrides=None
        )
        assert result_no_kw == result_none

    def test_total_equals_sum_of_components(self):
        """total is always the exact sum of the five components."""
        df = pd.DataFrame([_paddy_row(seed=1234, fertilizer=5678, labour=9012,
                                      irrigation=3456, other=7890)])
        result = estimate_costs(df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.5)

        expected_total = sum(result[c] for c in COST_COMPONENTS)
        assert result["total"] == pytest.approx(expected_total)

    def test_total_recalculated_after_override(self):
        """total is recalculated after overrides are applied."""
        df = pd.DataFrame([_paddy_row(seed=1000, fertilizer=2000, labour=3000,
                                      irrigation=1000, other=500)])
        result = estimate_costs(
            df, "paddy", "Tamil Nadu", "Kuruvai", acres=1.0,
            overrides={"labour": 9999.0}
        )
        expected = 1000 + 2000 + 9999 + 1000 + 500
        assert result["total"] == pytest.approx(expected)
