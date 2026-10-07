"""
config.py — AgriSecure AI
All assumptions, rates, thresholds, and limits in one place.
Every constant carries an inline source note and a last_verified date.
Edit THIS file when a rate or rule changes; never hard-code values in core/ or ui/.

Usage
-----
from config import get_config, ConfigurationError

val = get_config("KCC_RATE")            # returns 4.0
get_config("TYPO_KEY")                  # raises ConfigurationError
"""

# ---------------------------------------------------------------------------
# Custom exception (Requirement 19.6)
# ---------------------------------------------------------------------------

class ConfigurationError(Exception):
    """Raised when a /core function requests a config key that is not defined."""


# ---------------------------------------------------------------------------
# Interest Rates
# ---------------------------------------------------------------------------

MONEYLENDER_RATE_DEFAULT = 36.0
# % per year; source: RBI Financial Inclusion Survey 2021 — informal lender
# rates in rural Tamil Nadu typically 24–48 % pa; 36 % used as midpoint.
# last_verified: 2024-01-15

MONEYLENDER_RATE_MIN = 1.0
# Validation floor for UI input; below 1 % is not meaningful.
# last_verified: 2024-01-15

MONEYLENDER_RATE_MAX = 200.0
# Validation ceiling for UI input (Requirement 6.1).
# last_verified: 2024-01-15

BANK_CROP_LOAN_RATE = 9.0
# % per year; source: RBI base lending rate for agricultural crop loans,
# effective 2024 — most commercial banks charge 8.5–10 %; 9 % used.
# last_verified: 2024-01-15

KCC_RATE = 7.0  # % per year, base rate (conservative, used in calculations)
KCC_RATE_PROMPT_REPAYMENT = 4.0
# Effective rate after 3% prompt repayment incentive (interest subvention).
# Applies to short-term crop loans up to ₹3 lakh (₹2 lakh for animal
# husbandry/fisheries). Late repayment forfeits the incentive; full 7% applies.
# source: PIB Cabinet decision 28 May 2025; RBI circular 13 Jan 2026.
# last_verified: 2026-10-07

# ---------------------------------------------------------------------------
# KCC / Loan Limits
# ---------------------------------------------------------------------------

KCC_SCALE_OF_FINANCE_PER_ACRE = 15000.0
# ₹ per acre; PLACEHOLDER – verify.
# source: district-level Scale of Finance is set annually by the District
# Level Technical Committee (DLTC); varies by crop and district.
# Typical range ₹10,000–₹25,000/acre for paddy in Tamil Nadu.
# Verify with local DCCB / Lead Bank before use.
# last_verified: 2024-01-15

KCC_MAX_LOAN = 300000.0
# ₹ — interest subvention threshold for short-term crop loans.
# The 4% effective rate applies only to loans up to this amount.
# There is no formal upper cap on the loan itself; actual sanction
# depends on land holding, crop value, and bank assessment.
# source: PIB Cabinet decision 28 May 2025; RBI circular 13 Jan 2026.
# last_verified: 2026-10-07

# ---------------------------------------------------------------------------
# Risk Thresholds — Coefficient of Variation (CV)
# ---------------------------------------------------------------------------

CV_GREEN_THRESHOLD = 0.20
# CV below this → green (low risk).
# source: AgriSecure design doc — calibrated assumption; no published standard.
# last_verified: 2024-01-15

CV_RED_THRESHOLD = 0.40
# CV above this → red (high risk).
# source: AgriSecure design doc — calibrated assumption.
# last_verified: 2024-01-15

MIN_RECORDS_FOR_COLOUR = 3
# Fewer than this many historical rows → risk defaults to red (Requirement 3.2).
# source: AgriSecure design doc.
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# DSCR Thresholds
# ---------------------------------------------------------------------------

DSCR_YELLOW_THRESHOLD = 1.0
# DSCR below this → red (cannot repay from harvest income alone).
# source: AgriSecure design doc — calibrated assumption.
# last_verified: 2024-01-15

DSCR_GREEN_THRESHOLD = 1.5
# DSCR at or above this → green (comfortable repayment buffer).
# source: AgriSecure design doc — calibrated assumption;
# broadly in line with agricultural lending prudential norms.
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# Crop Durations (weeks) — PLACEHOLDER values, verify before use
# ---------------------------------------------------------------------------

CROP_DURATION_WEEKS: dict[str, int] = {
    "paddy":     17,   # ~120 days; source: TNAU crop calendar, PLACEHOLDER – verify
    "maize":     13,   # ~90 days;  PLACEHOLDER – verify
    "groundnut": 15,   # ~105 days; PLACEHOLDER – verify
    "sugarcane": 52,   # ~365 days; PLACEHOLDER – verify
    "cotton":    26,   # ~180 days; PLACEHOLDER – verify
    "wheat":     17,   # ~120 days; PLACEHOLDER – verify
    "soybean":   14,   # ~100 days; PLACEHOLDER – verify
    "onion":     13,   # ~90 days;  PLACEHOLDER – verify
}
# All durations are PLACEHOLDER – verify with TNAU / state agriculture dept.
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# Sowing Months (1 = January) — PLACEHOLDER, verify with state agriculture dept
# ---------------------------------------------------------------------------

SEASON_SOWING_MONTH: dict[str, int] = {
    "Kharif":  6,    # June;     PLACEHOLDER – verify with state agriculture dept
    "Rabi":    10,   # October;  PLACEHOLDER – verify
    "Kuruvai": 6,    # June;     TNAU paddy calendar, PLACEHOLDER – verify
    "Samba":   8,    # August;   PLACEHOLDER – verify
    "Thaladi": 11,   # November; PLACEHOLDER – verify
    "Navarai": 1,    # January;  PLACEHOLDER – verify
}
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# Government Scheme Config
# ---------------------------------------------------------------------------

SCHEME_KCC_URL = "https://www.nabard.org/content1.aspx?id=572"
# NABARD KCC information page.
# For scheme details and current circulars see also:
#   PIB Cabinet decision 28 May 2025
#   RBI circular 13 Jan 2026
# last_verified: 2026-10-07

SCHEME_PMKISAN_URL = "https://pmkisan.gov.in/"
# Official PM-KISAN portal.
# last_verified: 2024-01-01

SCHEME_PMFBY_URL = "https://pmfby.gov.in/"
# Official PMFBY portal.
# last_verified: 2024-01-01

SCHEME_PMKISAN_AMOUNT = 6000.0
# ₹ per year (₹2,000 in three instalments);
# source: PM-KISAN scheme notification, GoI, 2019.
# last_verified: 2024-01-01

SCHEME_PMFBY_PREMIUM_RATE_KHARIF = 0.02
# Up to 2% of sum insured for Kharif food/oilseed crops (farmer share).
# Centre and State pay the balance of the actuarial premium.
# source: PIB PMFBY FAQ; pmfby.gov.in.
# last_verified: 2026-10-07

SCHEME_PMFBY_PREMIUM_RATE_RABI = 0.015
# Up to 1.5% of sum insured for Rabi food/oilseed crops (farmer share).
# source: PIB PMFBY FAQ; pmfby.gov.in.
# last_verified: 2026-10-07

# ---------------------------------------------------------------------------
# Scheme Eligibility Rules
# VERIFY ON OFFICIAL SITE before use — rules may change.
# ---------------------------------------------------------------------------

# KCC Eligibility
KCC_MAX_ELIGIBLE_ACRES = 999.9
# KCC has no national upper land-area ceiling; any farmer with land ownership
# or tenancy documents qualifies.  This sentinel value means "no land cap".
# source: NABARD KCC Master Circular 2019 — verify on official site.
# last_verified: 2024-01-15

KCC_ELIGIBLE_LAST_VERIFIED = "2024-01-15"
# Date on which KCC eligibility rules were last checked against official sources.
# VERIFY ON OFFICIAL SITE: https://www.nabard.org/content1.aspx?id=572

# PM-KISAN Eligibility
PMKISAN_MAX_ELIGIBLE_ACRES = 999.9
# PM-KISAN has no land-size limit — all landholding farmer families with
# cultivable land in their name are eligible (no upper acreage cap).
# Sentinel value 999.9 means 'no cap' (matches KCC_MAX_ELIGIBLE_ACRES pattern).
# Exclusions are status-based, not land-based: income-tax payers,
# serving/retired government employees (Group A/B), institutional holders.
# source: pmkisan.gov.in; last_verified: 2026-10-07

PMKISAN_ELIGIBILITY_LAST_VERIFIED = "2024-01-15"
# VERIFY ON OFFICIAL SITE: https://pmkisan.gov.in/

# PMFBY Eligibility — Covered Crops
PMFBY_COVERED_CROPS: list[str] = [
    "paddy",
    "wheat",
    "maize",
    "groundnut",
    "cotton",
    "sugarcane",
    "soybean",
    "jowar",
    "bajra",
    "sunflower",
    "turmeric",
]
# PLACEHOLDER – verify.
# List of crops notified under PMFBY at national level.  Actual coverage varies
# by state and season; the state/district notifies specific crops each year.
# Crops like onion and tomato are typically not covered under PMFBY.
# source: PMFBY operational guidelines (GoI) — verify on official site.
# last_verified: 2024-01-15

PMFBY_COVERED_SEASONS: list[str] = [
    "Kharif",
    "Rabi",
    "Kuruvai",
    "Samba",
    "Thaladi",
]
# PLACEHOLDER – verify.
# Seasons for which PMFBY coverage is available.  Summer crops are not
# typically covered under the main PMFBY scheme.
# source: PMFBY operational guidelines (GoI) — verify on official site.
# last_verified: 2024-01-15

PMFBY_ELIGIBILITY_LAST_VERIFIED = "2024-01-15"
# VERIFY ON OFFICIAL SITE: https://pmfby.gov.in/

# ---------------------------------------------------------------------------
# Land Input Limits (Requirement 2.4)
# ---------------------------------------------------------------------------

LAND_MIN_ACRES = 0.10
# Minimum plot size accepted in the UI; source: Requirement 2.4.
# last_verified: 2024-01-15

LAND_MAX_ACRES = 999.90
# Maximum plot size accepted in the UI; source: Requirement 2.4.
# last_verified: 2024-01-15

LAND_STEP_ACRES = 0.10
# Stepper increment (10 cents); source: Requirement 2.4.
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# Cost Component Limits (Requirement 4.2)
# ---------------------------------------------------------------------------

COST_COMPONENT_MAX = 9999999.0
# ₹99,99,999 — maximum editable cost value; source: Requirement 4.2.
# last_verified: 2024-01-15

COST_COMPONENT_MIN = 0.0
# ₹0 — minimum editable cost value; source: Requirement 4.2.
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# Export Format (Requirement 16.2)
# ---------------------------------------------------------------------------

EXPORT_FORMAT = "whatsapp_text"
# "whatsapp_text" or "pdf"; source: Requirement 16.2.
# Change to "pdf" only if fpdf2 / reportlab is added to requirements.txt.
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# Text-to-Speech (TTS) Configuration  (Requirement 14)
# ---------------------------------------------------------------------------

TTS_CACHE_MAX_SIZE = 50
# Maximum number of audio clips to keep in the LRU cache.
# Least-recently-used entry is evicted when the limit is reached.
# source: AgriSecure design doc — Requirement 14.
# last_verified: 2024-01-15

TTS_TIMEOUT_SECONDS = 10
# Maximum wall-clock seconds to wait for the gTTS API to respond.
# If the request exceeds this limit the function returns None and the UI
# falls back to showing the text result with a localised notice.
# source: AgriSecure design doc — Requirement 14.
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# Data Quality Tag
# ---------------------------------------------------------------------------

PLACEHOLDER_TAG = "PLACEHOLDER – verify"
# String written to the 'note' column of every estimated/unverified CSV row.
# Must match the value in data/clean_data.py exactly.
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# Supported Crops — single source of truth
# To add a 4th crop: append it here, then add rows to data/cost.csv,
# data/yield_price.csv, and data/msp.csv.
# ---------------------------------------------------------------------------

SUPPORTED_CROPS: list[str] = [
    "paddy",
    "maize",
    "groundnut",
    # Add new crops here — one line each, lowercase, matching CSV crop column
]
# source: matches data/yield_price.csv, data/cost.csv crop values.
# last_verified: 2024-01-15

# ---------------------------------------------------------------------------
# Internal lookup dict — maps every public name above to its value.
# get_config() uses this to satisfy Requirement 19.6.
# ---------------------------------------------------------------------------

_CONFIG: dict = {
    # Interest Rates
    "MONEYLENDER_RATE_DEFAULT":         MONEYLENDER_RATE_DEFAULT,
    "MONEYLENDER_RATE_MIN":             MONEYLENDER_RATE_MIN,
    "MONEYLENDER_RATE_MAX":             MONEYLENDER_RATE_MAX,
    "BANK_CROP_LOAN_RATE":              BANK_CROP_LOAN_RATE,
    "KCC_RATE":                         KCC_RATE,
    # KCC / Loan Limits
    "KCC_SCALE_OF_FINANCE_PER_ACRE":    KCC_SCALE_OF_FINANCE_PER_ACRE,
    "KCC_MAX_LOAN":                     KCC_MAX_LOAN,
    # Risk Thresholds (CV)
    "CV_GREEN_THRESHOLD":               CV_GREEN_THRESHOLD,
    "CV_RED_THRESHOLD":                 CV_RED_THRESHOLD,
    "MIN_RECORDS_FOR_COLOUR":           MIN_RECORDS_FOR_COLOUR,
    # DSCR Thresholds
    "DSCR_YELLOW_THRESHOLD":            DSCR_YELLOW_THRESHOLD,
    "DSCR_GREEN_THRESHOLD":             DSCR_GREEN_THRESHOLD,
    # Crop Durations
    "CROP_DURATION_WEEKS":              CROP_DURATION_WEEKS,
    # Sowing Months
    "SEASON_SOWING_MONTH":              SEASON_SOWING_MONTH,
    # Government Scheme Config
    "SCHEME_KCC_URL":                       SCHEME_KCC_URL,
    "SCHEME_PMKISAN_URL":                   SCHEME_PMKISAN_URL,
    "SCHEME_PMFBY_URL":                     SCHEME_PMFBY_URL,
    "SCHEME_PMKISAN_AMOUNT":                SCHEME_PMKISAN_AMOUNT,
    "SCHEME_PMFBY_PREMIUM_RATE_KHARIF":     SCHEME_PMFBY_PREMIUM_RATE_KHARIF,
    "SCHEME_PMFBY_PREMIUM_RATE_RABI":       SCHEME_PMFBY_PREMIUM_RATE_RABI,
    # Scheme Eligibility Rules
    "KCC_MAX_ELIGIBLE_ACRES":               KCC_MAX_ELIGIBLE_ACRES,
    "KCC_ELIGIBILITY_LAST_VERIFIED":        KCC_ELIGIBLE_LAST_VERIFIED,
    "PMKISAN_MAX_ELIGIBLE_ACRES":           PMKISAN_MAX_ELIGIBLE_ACRES,
    "PMKISAN_ELIGIBILITY_LAST_VERIFIED":    PMKISAN_ELIGIBILITY_LAST_VERIFIED,
    "PMFBY_COVERED_CROPS":                  PMFBY_COVERED_CROPS,
    "PMFBY_COVERED_SEASONS":                PMFBY_COVERED_SEASONS,
    "PMFBY_ELIGIBILITY_LAST_VERIFIED":      PMFBY_ELIGIBILITY_LAST_VERIFIED,
    # Land Input Limits
    "LAND_MIN_ACRES":                   LAND_MIN_ACRES,
    "LAND_MAX_ACRES":                   LAND_MAX_ACRES,
    "LAND_STEP_ACRES":                  LAND_STEP_ACRES,
    # Cost Component Limits
    "COST_COMPONENT_MAX":               COST_COMPONENT_MAX,
    "COST_COMPONENT_MIN":               COST_COMPONENT_MIN,
    # Export
    "EXPORT_FORMAT":                    EXPORT_FORMAT,
    # Data Quality
    "PLACEHOLDER_TAG":                  PLACEHOLDER_TAG,
    "SUPPORTED_CROPS":                  SUPPORTED_CROPS,
    # TTS
    "TTS_CACHE_MAX_SIZE":               TTS_CACHE_MAX_SIZE,
    "TTS_TIMEOUT_SECONDS":              TTS_TIMEOUT_SECONDS,
}


def get_config(key: str):
    """
    Return the config value for *key*.

    Raises
    ------
    ConfigurationError
        If *key* is not present in _CONFIG, naming the missing key so that
        the error is easy to trace (Requirement 19.6).
    """
    if key not in _CONFIG:
        raise ConfigurationError(
            f"Configuration key '{key}' is not defined in config.py"
        )
    return _CONFIG[key]
