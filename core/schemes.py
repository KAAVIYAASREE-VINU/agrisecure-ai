"""
core/schemes.py — AgriSecure AI
=================================

Pure functions that check a farmer's eligibility for three key government
schemes: KCC, PM-KISAN, and PMFBY.

Design rules
------------
- No Streamlit imports.
- All thresholds and lists come from config.py via get_config().
- Each function returns a dict with exactly two keys:
    {"eligible": bool, "reason": str}
  where "reason" is a lang-file key (e.g. "scheme_kcc_ineligible_no_reason").
  An eligible result uses reason key "scheme_<name>_eligible".
  An ineligible result uses a specific reason key for the UI to display.

Public API
----------
check_kcc_eligibility(acres, crop) -> dict
    KCC: open to all farmers with any land size.  Currently no crop restriction.

check_pmkisan_eligibility(acres) -> dict
    PM-KISAN: no land-size cap; eligibility is status-based (source: pmkisan.gov.in).

check_pmfby_eligibility(crop, season) -> dict
    PMFBY: based on whether the crop and season are notified under the scheme.

Requirements: 11 (Government Schemes panel)
"""

from config import get_config


# ---------------------------------------------------------------------------
# KCC — Kisan Credit Card
# ---------------------------------------------------------------------------

def check_kcc_eligibility(acres: float, crop: str) -> dict:
    """Check KCC eligibility for the given land size and crop.

    KCC is available to all farmers — sharecroppers, tenant farmers, and
    owner-cultivators — who have documented land (own or leased).  There is
    no national upper land-size ceiling under KCC; the loan amount scales with
    land size up to KCC_MAX_LOAN.

    Parameters
    ----------
    acres : float
        Land size in acres (must be > 0 to qualify).
    crop : str
        Crop name (currently no crop exclusions under KCC at national level;
        parameter reserved for future state-level restrictions).

    Returns
    -------
    dict
        {"eligible": bool, "reason": str}  — reason is a lang-file key.

    Notes
    -----
    Source: NABARD KCC Master Circular 2019.
    VERIFY ON OFFICIAL SITE: https://www.nabard.org/content1.aspx?id=572
    Rules last verified: see KCC_ELIGIBILITY_LAST_VERIFIED in config.py.
    """
    if acres <= 0:
        return {
            "eligible": False,
            "reason": "scheme_kcc_ineligible_no_land",
        }

    # KCC_MAX_ELIGIBLE_ACRES is a sentinel (999.9) — no real upper cap.
    max_acres: float = get_config("KCC_MAX_ELIGIBLE_ACRES")
    if acres > max_acres:
        return {
            "eligible": False,
            "reason": "scheme_kcc_ineligible_land_too_large",
        }

    return {
        "eligible": True,
        "reason": "scheme_kcc_eligible",
    }


# ---------------------------------------------------------------------------
# PM-KISAN — Pradhan Mantri Kisan Samman Nidhi
# ---------------------------------------------------------------------------

def check_pmkisan_eligibility(acres: float) -> dict:
    """Check PM-KISAN eligibility for the given land size.

    PM-KISAN provides ₹6,000/year (3 × ₹2,000) to eligible farmer families.
    There is no land-size limit — all landholding farmer families with
    cultivable land in their name qualify.  Exclusions are status-based
    (income-tax payers, government employees Group A/B, institutional holders).
    PMKISAN_MAX_ELIGIBLE_ACRES in config.py is a sentinel (999.9) meaning no cap.

    Parameters
    ----------
    acres : float
        Land size in acres.

    Returns
    -------
    dict
        {"eligible": bool, "reason": str}  — reason is a lang-file key.

    Notes
    -----
    Source: pmkisan.gov.in; last_verified: 2026-10-07.
    """
    if acres <= 0:
        return {
            "eligible": False,
            "reason": "scheme_pmkisan_ineligible_no_land",
        }

    max_acres: float = get_config("PMKISAN_MAX_ELIGIBLE_ACRES")
    if acres > max_acres:
        return {
            "eligible": False,
            "reason": "scheme_pmkisan_ineligible_land_too_large",
        }

    return {
        "eligible": True,
        "reason": "scheme_pmkisan_eligible",
    }


# ---------------------------------------------------------------------------
# PMFBY — Pradhan Mantri Fasal Bima Yojana
# ---------------------------------------------------------------------------

def check_pmfby_eligibility(crop: str, season: str) -> dict:
    """Check PMFBY eligibility for the given crop and season.

    PMFBY covers notified crops in notified seasons.  Crops not listed in
    PMFBY_COVERED_CROPS (config.py) or seasons not in PMFBY_COVERED_SEASONS
    are ineligible at the national level.  Actual coverage is notified
    annually at state/district level — verify before use.

    Parameters
    ----------
    crop : str
        Crop name (case-insensitive match against PMFBY_COVERED_CROPS list).
    season : str
        Season name (case-insensitive match against PMFBY_COVERED_SEASONS).

    Returns
    -------
    dict
        {"eligible": bool, "reason": str}  — reason is a lang-file key.

    Notes
    -----
    Source: PMFBY operational guidelines, GoI.
    VERIFY ON OFFICIAL SITE: https://pmfby.gov.in/
    Rules last verified: see PMFBY_ELIGIBILITY_LAST_VERIFIED in config.py.
    """
    covered_crops: list[str] = get_config("PMFBY_COVERED_CROPS")
    covered_seasons: list[str] = get_config("PMFBY_COVERED_SEASONS")

    crop_lower = crop.lower().strip()
    covered_crops_lower = [c.lower() for c in covered_crops]

    season_lower = season.lower().strip()
    covered_seasons_lower = [s.lower() for s in covered_seasons]

    if crop_lower not in covered_crops_lower:
        return {
            "eligible": False,
            "reason": "scheme_pmfby_ineligible_crop_not_covered",
        }

    if season_lower not in covered_seasons_lower:
        return {
            "eligible": False,
            "reason": "scheme_pmfby_ineligible_season_not_covered",
        }

    return {
        "eligible": True,
        "reason": "scheme_pmfby_eligible",
    }
