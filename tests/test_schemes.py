"""
tests/test_schemes.py — AgriSecure AI
=======================================

Unit tests for core/schemes.py:
  - check_kcc_eligibility(acres, crop)
  - check_pmkisan_eligibility(acres)
  - check_pmfby_eligibility(crop, season)

Coverage
--------
- Eligible cases for all three schemes
- Ineligible cases: zero land, too much land, wrong crop, wrong season
- Edge cases: boundary land sizes, case-insensitive crop/season matching
- Return value structure: always {"eligible": bool, "reason": str}
- Reason keys must be resolvable strings (non-empty)
- Config-driven: thresholds come from config.py
"""

import pytest

from config import get_config
from core.schemes import (
    check_kcc_eligibility,
    check_pmkisan_eligibility,
    check_pmfby_eligibility,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_result_shape(result: dict) -> None:
    """All three functions must return {"eligible": bool, "reason": str}."""
    assert isinstance(result, dict), "result must be a dict"
    assert "eligible" in result, "result must have 'eligible' key"
    assert "reason" in result, "result must have 'reason' key"
    assert isinstance(result["eligible"], bool), "'eligible' must be bool"
    assert isinstance(result["reason"], str), "'reason' must be str"
    assert result["reason"], "'reason' must be a non-empty string"


# ---------------------------------------------------------------------------
# KCC Eligibility
# ---------------------------------------------------------------------------

class TestCheckKccEligibility:
    def test_typical_smallholder_eligible(self):
        """2-acre farmer growing paddy should be eligible for KCC."""
        result = check_kcc_eligibility(2.0, "paddy")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_any_crop_eligible(self):
        """KCC has no crop restriction at national level; cotton is eligible."""
        result = check_kcc_eligibility(1.5, "cotton")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_large_land_holding_eligible(self):
        """Large farm (50 acres) should still be KCC-eligible (no land cap)."""
        result = check_kcc_eligibility(50.0, "wheat")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_minimum_land_eligible(self):
        """Minimum viable land (0.1 acre) should be eligible."""
        result = check_kcc_eligibility(0.1, "paddy")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_zero_land_ineligible(self):
        """Zero land → ineligible; KCC requires land ownership/lease."""
        result = check_kcc_eligibility(0.0, "paddy")
        _assert_result_shape(result)
        assert result["eligible"] is False
        assert "no_land" in result["reason"]

    def test_negative_land_ineligible(self):
        """Negative land value → treated as ineligible (defensive check)."""
        result = check_kcc_eligibility(-1.0, "paddy")
        _assert_result_shape(result)
        assert result["eligible"] is False

    def test_unknown_crop_still_eligible(self):
        """Unknown/exotic crop: KCC has no national crop exclusion."""
        result = check_kcc_eligibility(1.0, "dragon_fruit")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_eligible_reason_key_is_correct(self):
        """Eligible result must use 'scheme_kcc_eligible' reason key."""
        result = check_kcc_eligibility(3.0, "maize")
        assert result["reason"] == "scheme_kcc_eligible"


# ---------------------------------------------------------------------------
# PM-KISAN Eligibility
# ---------------------------------------------------------------------------

class TestCheckPmkisanEligibility:
    def test_small_farmer_eligible(self):
        """Farmer with 2 acres is well within PM-KISAN limit."""
        result = check_pmkisan_eligibility(2.0)
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_boundary_land_eligible(self):
        """Exactly at the PMKISAN_MAX_ELIGIBLE_ACRES limit → eligible."""
        max_acres = get_config("PMKISAN_MAX_ELIGIBLE_ACRES")
        result = check_pmkisan_eligibility(max_acres)
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_above_limit_ineligible(self):
        """Land above the PM-KISAN limit → ineligible."""
        max_acres = get_config("PMKISAN_MAX_ELIGIBLE_ACRES")
        result = check_pmkisan_eligibility(max_acres + 0.1)
        _assert_result_shape(result)
        assert result["eligible"] is False
        assert "land_too_large" in result["reason"]

    def test_large_farm_ineligible(self):
        """Large farm (20 acres) exceeds PM-KISAN limit."""
        result = check_pmkisan_eligibility(20.0)
        _assert_result_shape(result)
        assert result["eligible"] is False

    def test_zero_land_ineligible(self):
        """Zero land → ineligible for PM-KISAN."""
        result = check_pmkisan_eligibility(0.0)
        _assert_result_shape(result)
        assert result["eligible"] is False
        assert "no_land" in result["reason"]

    def test_negative_land_ineligible(self):
        """Negative land → ineligible (defensive)."""
        result = check_pmkisan_eligibility(-0.5)
        _assert_result_shape(result)
        assert result["eligible"] is False

    def test_minimum_land_eligible(self):
        """Very small plot (0.1 acre) should be eligible."""
        result = check_pmkisan_eligibility(0.1)
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_eligible_reason_key_is_correct(self):
        """Eligible result must use 'scheme_pmkisan_eligible' reason key."""
        result = check_pmkisan_eligibility(1.0)
        assert result["reason"] == "scheme_pmkisan_eligible"

    def test_ineligible_reason_key_contains_scheme_name(self):
        """Ineligible reason key must contain 'pmkisan' for easy identification."""
        result = check_pmkisan_eligibility(100.0)
        assert "pmkisan" in result["reason"]

    def test_threshold_from_config(self):
        """Eligibility boundary exactly matches PMKISAN_MAX_ELIGIBLE_ACRES."""
        max_acres = get_config("PMKISAN_MAX_ELIGIBLE_ACRES")
        below = check_pmkisan_eligibility(max_acres - 0.01)
        at = check_pmkisan_eligibility(max_acres)
        above = check_pmkisan_eligibility(max_acres + 0.01)
        assert below["eligible"] is True
        assert at["eligible"] is True
        assert above["eligible"] is False


# ---------------------------------------------------------------------------
# PMFBY Eligibility
# ---------------------------------------------------------------------------

class TestCheckPmfbyEligibility:
    def test_paddy_kharif_eligible(self):
        """Paddy in Kharif is a standard PMFBY-covered combination."""
        result = check_pmfby_eligibility("paddy", "Kharif")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_wheat_rabi_eligible(self):
        """Wheat in Rabi is a standard PMFBY-covered combination."""
        result = check_pmfby_eligibility("wheat", "Rabi")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_groundnut_kharif_eligible(self):
        """Groundnut in Kharif is covered under PMFBY."""
        result = check_pmfby_eligibility("groundnut", "Kharif")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_cotton_kharif_eligible(self):
        """Cotton in Kharif is covered under PMFBY."""
        result = check_pmfby_eligibility("cotton", "Kharif")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_paddy_kuruvai_eligible(self):
        """Paddy in Tamil Nadu's Kuruvai season should be eligible."""
        result = check_pmfby_eligibility("paddy", "Kuruvai")
        _assert_result_shape(result)
        assert result["eligible"] is True

    def test_uncovered_crop_ineligible(self):
        """Tomato is not in PMFBY_COVERED_CROPS → ineligible."""
        result = check_pmfby_eligibility("tomato", "Kharif")
        _assert_result_shape(result)
        assert result["eligible"] is False
        assert "crop_not_covered" in result["reason"]

    def test_onion_not_covered(self):
        """Onion is typically not a PMFBY-notified crop → ineligible."""
        result = check_pmfby_eligibility("onion", "Rabi")
        _assert_result_shape(result)
        assert result["eligible"] is False
        assert "crop_not_covered" in result["reason"]

    def test_summer_season_ineligible(self):
        """Summer season is not in PMFBY_COVERED_SEASONS → ineligible."""
        result = check_pmfby_eligibility("paddy", "Summer")
        _assert_result_shape(result)
        assert result["eligible"] is False
        assert "season_not_covered" in result["reason"]

    def test_unknown_season_ineligible(self):
        """Unknown season → ineligible (not in covered seasons list)."""
        result = check_pmfby_eligibility("paddy", "Spring")
        _assert_result_shape(result)
        assert result["eligible"] is False

    def test_unknown_crop_ineligible(self):
        """Completely unknown crop → ineligible."""
        result = check_pmfby_eligibility("dragon_fruit", "Kharif")
        _assert_result_shape(result)
        assert result["eligible"] is False

    def test_crop_case_insensitive(self):
        """Crop name matching is case-insensitive: 'PADDY' == 'paddy'."""
        result_lower = check_pmfby_eligibility("paddy", "Kharif")
        result_upper = check_pmfby_eligibility("PADDY", "Kharif")
        result_mixed = check_pmfby_eligibility("Paddy", "Kharif")
        assert result_lower["eligible"] == result_upper["eligible"] == result_mixed["eligible"] is True

    def test_season_case_insensitive(self):
        """Season name matching is case-insensitive: 'kharif' == 'Kharif'."""
        result_lower = check_pmfby_eligibility("paddy", "kharif")
        result_title = check_pmfby_eligibility("paddy", "Kharif")
        result_upper = check_pmfby_eligibility("paddy", "KHARIF")
        assert result_lower["eligible"] == result_title["eligible"] == result_upper["eligible"] is True

    def test_eligible_reason_key_is_correct(self):
        """Eligible result must use 'scheme_pmfby_eligible' reason key."""
        result = check_pmfby_eligibility("maize", "Kharif")
        assert result["reason"] == "scheme_pmfby_eligible"

    def test_covered_crops_from_config(self):
        """Every crop in PMFBY_COVERED_CROPS with a valid season is eligible."""
        covered = get_config("PMFBY_COVERED_CROPS")
        for crop in covered:
            result = check_pmfby_eligibility(crop, "Kharif")
            _assert_result_shape(result)
            assert result["eligible"] is True, (
                f"Expected {crop} to be eligible but got: {result}"
            )

    def test_covered_seasons_from_config(self):
        """Paddy in every PMFBY_COVERED_SEASONS is eligible."""
        seasons = get_config("PMFBY_COVERED_SEASONS")
        for season in seasons:
            result = check_pmfby_eligibility("paddy", season)
            _assert_result_shape(result)
            assert result["eligible"] is True, (
                f"Expected paddy in {season} to be eligible but got: {result}"
            )


# ---------------------------------------------------------------------------
# Return-value contract: all functions must return consistent dict shape
# ---------------------------------------------------------------------------

class TestReturnValueContract:
    """The result dict shape must be consistent across all states."""

    def test_kcc_eligible_has_correct_keys(self):
        result = check_kcc_eligibility(1.0, "paddy")
        assert set(result.keys()) == {"eligible", "reason"}

    def test_kcc_ineligible_has_correct_keys(self):
        result = check_kcc_eligibility(0.0, "paddy")
        assert set(result.keys()) == {"eligible", "reason"}

    def test_pmkisan_eligible_has_correct_keys(self):
        result = check_pmkisan_eligibility(1.0)
        assert set(result.keys()) == {"eligible", "reason"}

    def test_pmkisan_ineligible_has_correct_keys(self):
        result = check_pmkisan_eligibility(0.0)
        assert set(result.keys()) == {"eligible", "reason"}

    def test_pmfby_eligible_has_correct_keys(self):
        result = check_pmfby_eligibility("paddy", "Kharif")
        assert set(result.keys()) == {"eligible", "reason"}

    def test_pmfby_ineligible_has_correct_keys(self):
        result = check_pmfby_eligibility("tomato", "Kharif")
        assert set(result.keys()) == {"eligible", "reason"}


# ---------------------------------------------------------------------------
# Lang-key existence: reason keys must exist in en.json
# ---------------------------------------------------------------------------

class TestReasonKeysExistInLangFile:
    """All reason keys returned must be present in the English lang file."""

    @pytest.fixture
    def en_keys(self):
        import json, os
        lang_path = os.path.join(
            os.path.dirname(__file__), "..", "lang", "en.json"
        )
        with open(lang_path, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.keys())

    def test_kcc_eligible_key_in_lang(self, en_keys):
        result = check_kcc_eligibility(2.0, "paddy")
        assert result["reason"] in en_keys, (
            f"Reason key '{result['reason']}' not found in lang/en.json"
        )

    def test_kcc_ineligible_no_land_key_in_lang(self, en_keys):
        result = check_kcc_eligibility(0.0, "paddy")
        assert result["reason"] in en_keys

    def test_pmkisan_eligible_key_in_lang(self, en_keys):
        result = check_pmkisan_eligibility(1.0)
        assert result["reason"] in en_keys

    def test_pmkisan_ineligible_no_land_key_in_lang(self, en_keys):
        result = check_pmkisan_eligibility(0.0)
        assert result["reason"] in en_keys

    def test_pmkisan_ineligible_large_land_key_in_lang(self, en_keys):
        result = check_pmkisan_eligibility(100.0)
        assert result["reason"] in en_keys

    def test_pmfby_eligible_key_in_lang(self, en_keys):
        result = check_pmfby_eligibility("paddy", "Kharif")
        assert result["reason"] in en_keys

    def test_pmfby_ineligible_crop_key_in_lang(self, en_keys):
        result = check_pmfby_eligibility("tomato", "Kharif")
        assert result["reason"] in en_keys

    def test_pmfby_ineligible_season_key_in_lang(self, en_keys):
        result = check_pmfby_eligibility("paddy", "Summer")
        assert result["reason"] in en_keys
