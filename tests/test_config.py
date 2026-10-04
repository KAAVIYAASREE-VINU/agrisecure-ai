"""
tests/test_config.py
Unit tests for config.py (Task 1.2, Requirements G2 and 19.6).

Checks:
- Every expected constant is present and has the correct type.
- get_config() returns known values.
- get_config() raises ConfigurationError (naming the key) for unknown keys.
- ConfigurationError inherits from Exception.
- Numeric thresholds are internally consistent.
"""

import pytest
import config
from config import get_config, ConfigurationError


# ---------------------------------------------------------------------------
# ConfigurationError contract
# ---------------------------------------------------------------------------

class TestConfigurationError:
    def test_inherits_from_exception(self):
        assert issubclass(ConfigurationError, Exception)

    def test_missing_key_raises_and_names_key(self):
        bad_key = "TOTALLY_UNKNOWN_KEY_XYZ"
        with pytest.raises(ConfigurationError) as exc_info:
            get_config(bad_key)
        assert bad_key in str(exc_info.value)

    def test_empty_string_key_raises(self):
        with pytest.raises(ConfigurationError):
            get_config("")

    def test_close_but_wrong_key_raises(self):
        """Typo in a key name must not silently return None."""
        with pytest.raises(ConfigurationError):
            get_config("KCC_RAET")   # transposed letters


# ---------------------------------------------------------------------------
# get_config() happy-path spot-checks
# ---------------------------------------------------------------------------

class TestGetConfigHappyPath:
    @pytest.mark.parametrize("key,expected", [
        ("MONEYLENDER_RATE_DEFAULT",         36.0),
        ("MONEYLENDER_RATE_MIN",              1.0),
        ("MONEYLENDER_RATE_MAX",            200.0),
        ("BANK_CROP_LOAN_RATE",               9.0),
        ("KCC_RATE",                          7.0),
        ("KCC_SCALE_OF_FINANCE_PER_ACRE", 15000.0),
        ("KCC_MAX_LOAN",                 300000.0),
        ("CV_GREEN_THRESHOLD",               0.20),
        ("CV_RED_THRESHOLD",                 0.40),
        ("MIN_RECORDS_FOR_COLOUR",              3),
        ("DSCR_YELLOW_THRESHOLD",             1.0),
        ("DSCR_GREEN_THRESHOLD",              1.5),
        ("LAND_MIN_ACRES",                   0.10),
        ("LAND_MAX_ACRES",                 999.90),
        ("LAND_STEP_ACRES",                  0.10),
        ("COST_COMPONENT_MIN",               0.0),
        ("COST_COMPONENT_MAX",         9999999.0),
        ("EXPORT_FORMAT",         "whatsapp_text"),
        ("SCHEME_PMKISAN_AMOUNT",          6000.0),
        ("SCHEME_PMFBY_PREMIUM_RATE_KHARIF", 0.02),
        ("SCHEME_PMFBY_PREMIUM_RATE_RABI",  0.015),
    ])
    def test_known_scalar_values(self, key, expected):
        assert get_config(key) == expected

    def test_crop_duration_weeks_returns_dict(self):
        durations = get_config("CROP_DURATION_WEEKS")
        assert isinstance(durations, dict)

    def test_crop_duration_weeks_paddy(self):
        assert get_config("CROP_DURATION_WEEKS")["paddy"] == 17

    def test_season_sowing_month_returns_dict(self):
        months = get_config("SEASON_SOWING_MONTH")
        assert isinstance(months, dict)

    def test_season_sowing_month_kuruvai(self):
        assert get_config("SEASON_SOWING_MONTH")["Kuruvai"] == 6

    def test_scheme_urls_are_strings(self):
        for key in ("SCHEME_KCC_URL", "SCHEME_PMKISAN_URL", "SCHEME_PMFBY_URL"):
            val = get_config(key)
            assert isinstance(val, str) and val.startswith("http")


# ---------------------------------------------------------------------------
# Type checks on module-level constants
# ---------------------------------------------------------------------------

class TestConstantTypes:
    def test_interest_rates_are_floats(self):
        for name in ("MONEYLENDER_RATE_DEFAULT", "BANK_CROP_LOAN_RATE", "KCC_RATE"):
            assert isinstance(getattr(config, name), float), name

    def test_land_limits_are_floats(self):
        for name in ("LAND_MIN_ACRES", "LAND_MAX_ACRES", "LAND_STEP_ACRES"):
            assert isinstance(getattr(config, name), float), name

    def test_min_records_is_int(self):
        assert isinstance(config.MIN_RECORDS_FOR_COLOUR, int)

    def test_crop_duration_dict_values_are_ints(self):
        for crop, weeks in config.CROP_DURATION_WEEKS.items():
            assert isinstance(weeks, int), f"{crop} duration should be int"

    def test_sowing_month_dict_values_are_ints(self):
        for season, month in config.SEASON_SOWING_MONTH.items():
            assert isinstance(month, int), f"{season} month should be int"
            assert 1 <= month <= 12, f"{season} month {month} out of range"


# ---------------------------------------------------------------------------
# Internal-consistency checks
# ---------------------------------------------------------------------------

class TestConsistency:
    def test_cv_green_below_red(self):
        assert config.CV_GREEN_THRESHOLD < config.CV_RED_THRESHOLD

    def test_dscr_yellow_below_green(self):
        assert config.DSCR_YELLOW_THRESHOLD < config.DSCR_GREEN_THRESHOLD

    def test_moneylender_rate_range_valid(self):
        assert config.MONEYLENDER_RATE_MIN < config.MONEYLENDER_RATE_MAX

    def test_moneylender_default_within_range(self):
        assert (config.MONEYLENDER_RATE_MIN
                <= config.MONEYLENDER_RATE_DEFAULT
                <= config.MONEYLENDER_RATE_MAX)

    def test_land_min_less_than_max(self):
        assert config.LAND_MIN_ACRES < config.LAND_MAX_ACRES

    def test_land_step_within_range(self):
        assert config.LAND_MIN_ACRES >= config.LAND_STEP_ACRES

    def test_cost_min_less_than_max(self):
        assert config.COST_COMPONENT_MIN < config.COST_COMPONENT_MAX

    def test_kcc_rate_lower_than_bank_rate(self):
        """KCC subvention makes it cheaper than a plain bank loan."""
        assert config.KCC_RATE < config.BANK_CROP_LOAN_RATE

    def test_crop_durations_positive(self):
        for crop, weeks in config.CROP_DURATION_WEEKS.items():
            assert weeks > 0, f"{crop} duration must be positive"
