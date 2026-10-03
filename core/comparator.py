"""
core/comparator.py — AgriSecure AI
=====================================

MoneylenderComparator: pure functions that compare the interest cost of
borrowing the same principal from three lender types for a given duration.

Design rules
------------
- No Streamlit imports.
- All rates come from config.py via get_config(); never hard-coded.
- Rate validation uses MONEYLENDER_RATE_MIN and MONEYLENDER_RATE_MAX from
  config.py (Requirement 6.1).
- Every function returns a plain Python value.

Public API
----------
interest_costs(principal, months, moneylender_rate=None) -> dict
    Returns the simple interest cost for each of the three lender types:
    - "moneylender": uses moneylender_rate if provided, else
                     MONEYLENDER_RATE_DEFAULT from config.py
    - "bank":        uses BANK_CROP_LOAN_RATE from config.py
    - "kcc":         uses KCC_RATE from config.py

    Interest formula (same for all three):
        interest = principal × (annual_rate / 100) / 12 × months

Requirements: 6.1 (moneylender rate input + validation),
              6.2 (interest cost comparison chart)
"""

from config import get_config


# ---------------------------------------------------------------------------
# Interest cost comparison
# ---------------------------------------------------------------------------

def interest_costs(
    principal: float,
    months: int,
    moneylender_rate: float | None = None,
) -> dict:
    """Return the simple interest cost for moneylender, bank, and KCC loans.

    Uses the formula:
        interest = principal × (annual_rate_pct / 100) / 12 × months

    Parameters
    ----------
    principal : float
        Loan amount in ₹.  Must be >= 0.
    months : int | float
        Loan duration in months.  Must be >= 0.
    moneylender_rate : float | None, optional
        Annual interest rate (%) entered by the farmer for their moneylender.
        Must be in the range [MONEYLENDER_RATE_MIN, MONEYLENDER_RATE_MAX]
        from config.py.  When ``None``, falls back to
        ``MONEYLENDER_RATE_DEFAULT``.

    Returns
    -------
    dict
        ``{"moneylender": float, "bank": float, "kcc": float}``
        — simple interest cost (₹) for each lender type.

    Raises
    ------
    ValueError
        If ``moneylender_rate`` is outside
        [MONEYLENDER_RATE_MIN, MONEYLENDER_RATE_MAX].

    Notes
    -----
    All rate constants are sourced from config.py with inline attribution.
    MONEYLENDER_RATE_DEFAULT = 36 % pa (RBI Financial Inclusion Survey 2021).
    BANK_CROP_LOAN_RATE     = 9  % pa (RBI base rate for agricultural loans).
    KCC_RATE                = 4  % pa (GoI KCC scheme, after 3 % subvention).

    Satisfies Requirements 6.1 and 6.2.
    """
    # ------------------------------------------------------------------
    # Validate moneylender_rate if provided
    # ------------------------------------------------------------------
    if moneylender_rate is not None:
        rate_min: float = get_config("MONEYLENDER_RATE_MIN")
        rate_max: float = get_config("MONEYLENDER_RATE_MAX")
        if moneylender_rate < rate_min or moneylender_rate > rate_max:
            raise ValueError(
                f"moneylender_rate {moneylender_rate!r} is outside the valid "
                f"range [{rate_min}, {rate_max}] % per year. "
                "Please enter a realistic annual interest rate."
            )
        ml_rate = moneylender_rate
    else:
        ml_rate = get_config("MONEYLENDER_RATE_DEFAULT")

    bank_rate: float = get_config("BANK_CROP_LOAN_RATE")
    kcc_rate: float = get_config("KCC_RATE")

    def _simple_interest(rate_pct: float) -> float:
        """principal × (rate/100) / 12 × months"""
        return principal * (rate_pct / 100.0) / 12.0 * months

    return {
        "moneylender": _simple_interest(ml_rate),
        "bank":        _simple_interest(bank_rate),
        "kcc":         _simple_interest(kcc_rate),
    }
