"""
assistant/presets.py — AgriSecure AI
======================================

Preset question answer functions for the three quick-answer buttons.

Design rules
------------
- No Streamlit imports — pure functions only.
- No numbers invented — every figure comes from a /core function called
  with data already present in the session results dict.
- Each function returns a formatted string answer, or None if the required
  data is missing (the UI then shows a localized missing-step message).
- All text templates come from lang/*.json via the i18n key strings returned
  by the caller; the functions receive a pre-loaded ``t`` callable.

Public API
----------
answer_repay_on_time(results, df_yield_price, df_msp, df_cost, t_fn) -> str | None
    Checks DSCR and risk colour from computed session data.
    Returns None if required keys are missing.

answer_rain_fails(results, df_yield_price, df_msp, t_fn) -> str | None
    Looks at the "bad" scenario profit from computed session data.
    Returns None if required keys are missing.

answer_moneylender_worth_it(results, df_cost, t_fn) -> str | None
    States the extra interest cost of moneylender vs KCC in rupees.
    Returns None if required keys are missing.

Requirements: 12 (preset question buttons, no LLM, core results only)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    import pandas as pd


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_keys(d: dict, *keys: str) -> bool:
    """Return True only if every key is present in d and not None."""
    return all(d.get(k) is not None for k in keys)


# ---------------------------------------------------------------------------
# Q1: Can I repay on time?
# ---------------------------------------------------------------------------

def answer_repay_on_time(
    results: dict,
    df_yield_price: "pd.DataFrame",
    df_msp: "pd.DataFrame",
    df_cost: "pd.DataFrame",
    t_fn: Callable[[str], str],
) -> str | None:
    """Return a yes/no/uncertain repayment answer based on DSCR.

    Uses the normal-harvest revenue from profit_scenarios and the
    funding gap + KCC interest as the repayment obligation.

    Parameters
    ----------
    results : dict
        Session state results dict (must contain crop, state, season,
        acres, costs, own_capital).
    df_yield_price, df_msp, df_cost : pd.DataFrame
        Pre-loaded DataFrames from the data layer.
    t_fn : Callable[[str], str]
        Language lookup function (returns translated text for a key).

    Returns
    -------
    str | None
        Formatted answer string, or None if required data is absent.
    """
    required = ("crop", "state", "season", "acres", "costs", "own_capital")
    if not _require_keys(results, *required):
        return None

    crop = results["crop"]
    state = results["state"]
    season = results["season"]
    acres = float(results["acres"])
    own_capital = float(results["own_capital"])
    costs = results["costs"]

    # Recompute effective total (accounts for any live cost overrides stored
    # in the results — the caller should pass the live computed_total if
    # available; we fall back to the stored costs total).
    cost_total = results.get("computed_total") or float(costs.get("total", 0.0))

    try:
        import core.crops as crops_module
        import core.loans as loans_module
        import core.risk as risk_module
        import core.comparator as comparator_module
        from core.formatting import indian_format

        ps_result = crops_module.profit_scenarios(
            crop=crop,
            state=state,
            season=season,
            land_acres=acres,
            df_yield_price=df_yield_price,
            df_msp=df_msp,
            cost_override=cost_total,
        )

        if ps_result["no_data"]:
            return None

        normal_scenario = next(
            (s for s in ps_result["scenarios"] if s["label"] == "normal"), None
        )
        if normal_scenario is None:
            return None

        normal_income = float(normal_scenario["revenue_total"])

        # Funding gap and KCC interest cost
        gap = loans_module.funding_gap(cost_total, own_capital)
        df_cost_hw = df_cost  # already loaded
        months = loans_module.harvest_window(crop, season, df_cost_hw)
        months_for_calc = months if months is not None else 6

        if gap > 0:
            lender_costs = comparator_module.interest_costs(
                principal=gap,
                months=months_for_calc,
                moneylender_rate=results.get("moneylender_rate"),
            )
            kcc_interest = lender_costs["kcc"]
        else:
            kcc_interest = 0.0

        repayment_obligation = gap + kcc_interest
        dscr_value = risk_module.dscr(normal_income, repayment_obligation)
        colour = risk_module.dscr_colour(dscr_value)

    except Exception:
        return None

    # Build answer from language template keys
    dscr_str = "∞" if dscr_value == math.inf else f"{dscr_value:.2f}"

    if dscr_value == math.inf:
        # No loan needed
        answer_key = "preset_repay_no_loan"
    elif colour == "green":
        answer_key = "preset_repay_green"
    elif colour == "yellow":
        answer_key = "preset_repay_yellow"
    else:
        answer_key = "preset_repay_red"

    template = t_fn(answer_key)
    # Substitute {dscr} placeholder in the template if present
    return template.replace("{dscr}", dscr_str).replace(
        "{income}", indian_format(normal_income)
    ).replace("{obligation}", indian_format(repayment_obligation))


# ---------------------------------------------------------------------------
# Q2: What if rain fails?
# ---------------------------------------------------------------------------

def answer_rain_fails(
    results: dict,
    df_yield_price: "pd.DataFrame",
    df_msp: "pd.DataFrame",
    t_fn: Callable[[str], str],
) -> str | None:
    """Return the bad-harvest profit/loss figure with a plain statement.

    Parameters
    ----------
    results : dict
        Session state results dict (must contain crop, state, season, acres,
        costs).
    df_yield_price, df_msp : pd.DataFrame
        Pre-loaded DataFrames.
    t_fn : Callable[[str], str]
        Language lookup function.

    Returns
    -------
    str | None
        Formatted answer, or None if required data is absent.
    """
    required = ("crop", "state", "season", "acres", "costs")
    if not _require_keys(results, *required):
        return None

    crop = results["crop"]
    state = results["state"]
    season = results["season"]
    acres = float(results["acres"])
    costs = results["costs"]
    cost_total = results.get("computed_total") or float(costs.get("total", 0.0))

    try:
        import core.crops as crops_module
        from core.formatting import indian_format

        ps_result = crops_module.profit_scenarios(
            crop=crop,
            state=state,
            season=season,
            land_acres=acres,
            df_yield_price=df_yield_price,
            df_msp=df_msp,
            cost_override=cost_total,
        )

        if ps_result["no_data"]:
            return None

        bad_scenario = next(
            (s for s in ps_result["scenarios"] if s["label"] == "bad"), None
        )
        if bad_scenario is None:
            return None

        bad_profit = bad_scenario.get("profit_total")
        bad_revenue = float(bad_scenario["revenue_total"])

        if bad_profit is None:
            return None

        profit_str = indian_format(abs(bad_profit))
        revenue_str = indian_format(bad_revenue)

    except Exception:
        return None

    if bad_profit >= 0:
        template = t_fn("preset_rain_positive")
    else:
        template = t_fn("preset_rain_negative")

    return template.replace("{profit}", profit_str).replace("{revenue}", revenue_str)


# ---------------------------------------------------------------------------
# Q3: Is moneylender worth it?
# ---------------------------------------------------------------------------

def answer_moneylender_worth_it(
    results: dict,
    df_cost: "pd.DataFrame",
    t_fn: Callable[[str], str],
) -> str | None:
    """Return the extra interest cost of moneylender vs KCC. No recommendation.

    Per Requirement 12, the answer shows only the cost comparison, with no
    recommendation about whether to use a moneylender.

    Parameters
    ----------
    results : dict
        Session state results dict (must contain crop, season, acres,
        costs, own_capital).
    df_cost : pd.DataFrame
        Pre-loaded cost DataFrame (for harvest_window).
    t_fn : Callable[[str], str]
        Language lookup function.

    Returns
    -------
    str | None
        Formatted answer, or None if required data is absent.
    """
    required = ("crop", "season", "acres", "costs", "own_capital")
    if not _require_keys(results, *required):
        return None

    crop = results["crop"]
    season = results["season"]
    acres = float(results["acres"])
    own_capital = float(results["own_capital"])
    costs = results["costs"]
    cost_total = results.get("computed_total") or float(costs.get("total", 0.0))

    try:
        import core.loans as loans_module
        import core.comparator as comparator_module
        from core.formatting import indian_format

        gap = loans_module.funding_gap(cost_total, own_capital)

        if gap <= 0:
            # No loan needed — moneylender question doesn't apply
            return None

        months = loans_module.harvest_window(crop, season, df_cost)
        months_for_calc = months if months is not None else 6

        lender_costs = comparator_module.interest_costs(
            principal=gap,
            months=months_for_calc,
            moneylender_rate=results.get("moneylender_rate"),
        )

        ml_cost = lender_costs["moneylender"]
        kcc_cost = lender_costs["kcc"]
        extra = ml_cost - kcc_cost

        extra_str = indian_format(extra)
        ml_str = indian_format(ml_cost)
        kcc_str = indian_format(kcc_cost)

    except Exception:
        return None

    template = t_fn("preset_moneylender_extra")
    return (
        template
        .replace("{extra}", extra_str)
        .replace("{ml_cost}", ml_str)
        .replace("{kcc_cost}", kcc_str)
        .replace("{months}", str(months_for_calc))
        .replace("{principal}", indian_format(gap))
    )
