"""
core/risk.py — AgriSecure AI
==============================

RiskEngine: colour-coding functions for crop revenue risk and loan repayment risk.

Design rules
------------
- No Streamlit imports.
- All thresholds come from config.py via get_config(); never hard-coded here.
- cv_risk_colour uses CV (coefficient of variation = std/mean) thresholds.
- dscr computes the Debt Service Coverage Ratio (income / debt obligation).
- dscr_colour maps a DSCR value to a traffic-light colour using config thresholds.
- Zero debt obligation is handled gracefully (returns math.inf, not a crash).

Public API
----------
cv_risk_colour(cv: float) -> str
    Returns "green", "yellow", or "red" based on CV thresholds in config.py.

dscr(annual_income: float, total_annual_debt_obligation: float) -> float
    Returns income / obligation, or math.inf when obligation is zero.

dscr_colour(dscr_value: float) -> str | None
    Returns "green", "yellow", "red", or None (indeterminate) based on thresholds.

Requirements: 3.2 (CV colour), 8.1 (DSCR thresholds), 8.3 (zero obligation → indeterminate)
"""

import math

from config import get_config


# ---------------------------------------------------------------------------
# CV (Coefficient of Variation) colour
# ---------------------------------------------------------------------------

def cv_risk_colour(cv: float) -> str:
    """
    Map a coefficient of variation to a risk colour.

    Parameters
    ----------
    cv : float
        Coefficient of variation (std / mean) for the crop's revenue or yield.
        Must be >= 0.

    Returns
    -------
    str
        "green"  — CV < CV_GREEN_THRESHOLD  (low risk)
        "yellow" — CV_GREEN_THRESHOLD <= CV <= CV_RED_THRESHOLD  (medium risk)
        "red"    — CV > CV_RED_THRESHOLD    (high risk)

    Notes
    -----
    Thresholds are read from config.py (Requirement G2):
      CV_GREEN_THRESHOLD = 0.20
      CV_RED_THRESHOLD   = 0.40
    A crop with fewer than MIN_RECORDS_FOR_COLOUR historical rows should be
    passed to this function as a sentinel — callers in crops.py default to red
    before calling here (Requirement 3.2).
    """
    green_thresh: float = get_config("CV_GREEN_THRESHOLD")
    red_thresh: float = get_config("CV_RED_THRESHOLD")

    if cv < green_thresh:
        return "green"
    if cv > red_thresh:
        return "red"
    return "yellow"


# ---------------------------------------------------------------------------
# DSCR — Debt Service Coverage Ratio
# ---------------------------------------------------------------------------

def dscr(annual_income: float, total_annual_debt_obligation: float) -> float:
    """
    Compute the Debt Service Coverage Ratio.

    DSCR = annual_income / total_annual_debt_obligation

    Parameters
    ----------
    annual_income : float
        Expected normal-harvest income for the season (₹).
    total_annual_debt_obligation : float
        Principal + interest that must be repaid this season (₹).

    Returns
    -------
    float
        Ratio of income to obligation.  Returns ``math.inf`` when
        *total_annual_debt_obligation* is zero (farmer has no debt —
        safe by definition).  Never raises ZeroDivisionError.

    Notes
    -----
    Per Requirement 8.3, a zero obligation is the "indeterminate / no loan"
    case; callers should check for math.inf before calling dscr_colour and
    show an "indeterminate" message instead.
    """
    if total_annual_debt_obligation == 0:
        return math.inf
    return annual_income / total_annual_debt_obligation


# ---------------------------------------------------------------------------
# DSCR colour
# ---------------------------------------------------------------------------

def dscr_colour(dscr_value: float) -> str | None:
    """
    Map a DSCR value to a repayment-risk colour.

    Parameters
    ----------
    dscr_value : float
        Value returned by :func:`dscr`.  Pass ``math.inf`` to get ``None``
        (indeterminate — farmer has no debt obligation).

    Returns
    -------
    str | None
        "green"  — dscr_value >= DSCR_GREEN_THRESHOLD  (comfortable buffer)
        "yellow" — DSCR_YELLOW_THRESHOLD <= dscr_value < DSCR_GREEN_THRESHOLD
        "red"    — dscr_value < DSCR_YELLOW_THRESHOLD  (cannot repay alone)
        None     — dscr_value is math.inf (no obligation / indeterminate)

    Notes
    -----
    Thresholds from config.py (Requirement G2, 8.1):
      DSCR_YELLOW_THRESHOLD = 1.0  (below this → red)
      DSCR_GREEN_THRESHOLD  = 1.5  (at or above this → green)

    The design doc states: "Below dscr_yellow_threshold is red, below
    dscr_green_threshold is yellow, otherwise green."
    """
    if dscr_value == math.inf:
        return None

    yellow_thresh: float = get_config("DSCR_YELLOW_THRESHOLD")
    green_thresh: float = get_config("DSCR_GREEN_THRESHOLD")

    if dscr_value >= green_thresh:
        return "green"
    if dscr_value < yellow_thresh:
        return "red"
    return "yellow"
