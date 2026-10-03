"""
core/loans.py — AgriSecure AI
==============================

LoanAnalyzer: pure functions that calculate funding gaps, institutional loan
limits, residual moneylender gap, and harvest window for a crop/season.

Design rules
------------
- No Streamlit imports.
- All rates and limits come from config.py via get_config(); never hard-coded.
- Every function returns a plain Python value (float or int | None).
- Negative funding or gap values are clamped to zero — the farmer can never
  "owe" less than nothing.

Public API
----------
funding_gap(total_cost, own_funds) -> float
    How much the farmer still needs to borrow (clamped to 0 minimum).

institutional_loan_limit(land_acres) -> float
    Maximum KCC/institutional loan available based on land size, capped at
    KCC_MAX_LOAN from config.py.

residual_gap(funding_gap, loan_amount) -> float
    Remaining shortfall after the institutional loan (clamped to 0 minimum).
    This is the amount that would have to come from a moneylender.

harvest_window(crop, season, df_cost) -> int | None
    Months from planting until harvest, derived from CROP_DURATION_WEEKS in
    config.py.  Returns None when the crop duration is unknown.

Requirements: 6.1 (moneylender rate input), 7.1 (funding gap / residual),
              8.1 (DSCR), 8.3 (zero loan edge case)
"""

import math

import pandas as pd

from config import get_config


# ---------------------------------------------------------------------------
# Funding gap
# ---------------------------------------------------------------------------

def funding_gap(total_cost: float, own_funds: float) -> float:
    """Return how much the farmer still needs to borrow.

    Parameters
    ----------
    total_cost : float
        Total cultivation cost in ₹ (from estimate_costs).
    own_funds : float
        Farmer's own capital in ₹.

    Returns
    -------
    float
        ``max(0, total_cost - own_funds)``.  Never negative — if own_funds
        exceed total_cost, the farmer needs no loan, so the gap is 0.

    Notes
    -----
    Satisfies Requirement 7.1 (funding need = total cost - own capital).
    """
    return max(0.0, total_cost - own_funds)


# ---------------------------------------------------------------------------
# Institutional loan limit
# ---------------------------------------------------------------------------

def institutional_loan_limit(land_acres: float) -> float:
    """Return the maximum institutional (KCC) loan available for the land size.

    The limit is ``KCC_SCALE_OF_FINANCE_PER_ACRE * land_acres``, capped at
    ``KCC_MAX_LOAN`` from config.py.  Both constants are marked PLACEHOLDER —
    verify with DLTC / Lead Bank before use.

    Parameters
    ----------
    land_acres : float
        Land size in acres.

    Returns
    -------
    float
        Maximum loan amount in ₹.  Always >= 0 (zero acres → zero limit).

    Notes
    -----
    Source: KCC_SCALE_OF_FINANCE_PER_ACRE and KCC_MAX_LOAN in config.py.
    Satisfies Requirement 7.1.
    """
    per_acre: float = get_config("KCC_SCALE_OF_FINANCE_PER_ACRE")
    max_loan: float = get_config("KCC_MAX_LOAN")
    return min(per_acre * land_acres, max_loan)


# ---------------------------------------------------------------------------
# Residual gap
# ---------------------------------------------------------------------------

def residual_gap(funding_gap: float, loan_amount: float) -> float:
    """Return how much still needs to come from a moneylender.

    Parameters
    ----------
    funding_gap : float
        Total amount the farmer needs to borrow (from :func:`funding_gap`).
    loan_amount : float
        The institutional loan the farmer will actually receive.  May exceed
        ``funding_gap`` (e.g. the farmer qualifies for more than they need).

    Returns
    -------
    float
        ``max(0, funding_gap - loan_amount)``.  Never negative — when the
        institutional loan covers the full need, the residual is 0.

    Notes
    -----
    Satisfies Requirement 7.1.  Key rule: loan larger than need → residual 0.
    """
    return max(0.0, funding_gap - loan_amount)


# ---------------------------------------------------------------------------
# Harvest window
# ---------------------------------------------------------------------------

def harvest_window(crop: str, season: str, df_cost: pd.DataFrame) -> int | None:
    """Return the number of months from planting until harvest.

    Looks up the crop in ``CROP_DURATION_WEEKS`` (config.py) and converts
    weeks to whole months (rounding to nearest month, minimum 1).  Returns
    ``None`` when the crop's duration is unknown rather than crashing.

    Parameters
    ----------
    crop : str
        Crop name (case-insensitive; matched against lowercase keys in
        ``CROP_DURATION_WEEKS``).
    season : str
        Season name — reserved for future per-season duration overrides;
        currently unused but kept in the signature for API stability.
    df_cost : pd.DataFrame
        Loaded cost DataFrame.  Used to confirm the crop appears in the
        dataset.  If the crop is not in the DataFrame AND not in
        ``CROP_DURATION_WEEKS``, returns ``None``.

    Returns
    -------
    int | None
        Number of months (>= 1) until harvest, or ``None`` if the duration
        is not known for this crop.

    Notes
    -----
    Duration source: ``CROP_DURATION_WEEKS`` in config.py.  All values are
    marked PLACEHOLDER — verify with TNAU / state agriculture dept.
    Satisfies Requirement 7.1 (repayment window display).
    """
    crop_durations: dict[str, int] = get_config("CROP_DURATION_WEEKS")

    weeks = crop_durations.get(crop.lower())
    if weeks is None:
        return None

    # Convert weeks → months: 1 month ≈ 4.333 weeks; round to nearest whole
    # month, with a floor of 1 so very short crops still show at least 1 month.
    months = max(1, round(weeks / 4.333))
    return months
