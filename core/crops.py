"""
core/crops.py — AgriSecure AI
==============================

CropAdvisor: query available crops, compute profit scenarios, profit range,
and break-even price from yield/price history and MSP data.

Design rules
------------
- No Streamlit imports.
- No numbers are invented; all thresholds come from config.py via get_config().
- Season names arrive already stripped (data_loader.strip_season).
- Crop matching is case-insensitive; CSV stores lowercase names.
- Fewer than MIN_RECORDS_FOR_COLOUR rows → fall back gracefully (Req 3.2).
- Missing MSP → return None for MSP-derived scenarios; never crash.

Public API
----------
available_crops(state, season, df_yield_price) -> list[str]
    Unique crop names for the given state/season.

profit_scenarios(crop, state, season, land_acres, df_yield_price,
                 df_msp, cost_override=None) -> dict
    Low / medium / high gross revenue and net profit per acre and total,
    plus a placeholder flag and a msp_available flag.

profit_range_per_acre(crop, state, season, df_yield_price, df_msp) -> tuple[float, float] | None
    (min_profit_per_acre, max_profit_per_acre) using bad/good scenario prices,
    or None when there is insufficient data.

break_even_price(total_cost_per_acre, yield_per_acre) -> float
    Price per quintal at which the farmer exactly breaks even.

rank_top3(state, season, land_acres, df_yield_price, df_msp, cost_per_acre=None) -> list[dict]
    Top-3 crops ranked by a combined profit-and-risk score.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5 (profit scenarios and break-even)
             3.3 (top-3 crop ranking)
"""

import pandas as pd

from config import get_config
from data.clean_data import PLACEHOLDER_TAG


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _filter_yield(df: pd.DataFrame, state: str, season: str, crop: str) -> pd.DataFrame:
    """Return rows matching state / season / crop (case-insensitive crop)."""
    return df[
        (df["state"] == state)
        & (df["season"] == season)
        & (df["crop"].str.lower() == crop.lower())
    ]


def _latest_msp(df_msp: pd.DataFrame, crop: str) -> float | None:
    """Return the most recent MSP (₹/quintal) for *crop*, or None if absent."""
    if df_msp is None or df_msp.empty:
        return None
    rows = df_msp[df_msp["crop"].str.lower() == crop.lower()]
    if rows.empty:
        return None
    # Take the row with the highest year value.
    return float(rows.loc[rows["year"].idxmax(), "msp_per_quintal"])


def _is_placeholder(df: pd.DataFrame) -> bool:
    """True if any row in *df* has the PLACEHOLDER_TAG in the note column."""
    if "note" not in df.columns:
        return False
    return bool((df["note"] == PLACEHOLDER_TAG).any())


# ---------------------------------------------------------------------------
# available_crops
# ---------------------------------------------------------------------------

def available_crops(
    state: str,
    season: str,
    df_yield_price: pd.DataFrame,
) -> list[str]:
    """Return unique crop names available for *state* and *season*.

    Parameters
    ----------
    state : str
        State name (matched exactly as stored in the CSV).
    season : str
        Season name (whitespace-stripped; matched exactly).
    df_yield_price : pd.DataFrame
        Loaded yield-price DataFrame (from ``data_loader.load_yield_price``).

    Returns
    -------
    list[str]
        Sorted list of unique crop names.  Empty list if no data matches.

    Notes
    -----
    Satisfies Requirement 3.1: show only crops with historical data.
    """
    mask = (df_yield_price["state"] == state) & (df_yield_price["season"] == season)
    matching = df_yield_price[mask]
    if matching.empty:
        return []
    return sorted(matching["crop"].str.lower().unique().tolist())


# ---------------------------------------------------------------------------
# profit_scenarios
# ---------------------------------------------------------------------------

def profit_scenarios(
    crop: str,
    state: str,
    season: str,
    land_acres: float,
    df_yield_price: pd.DataFrame,
    df_msp: pd.DataFrame,
    cost_override: float | None = None,
) -> dict:
    """Return low / medium / high profit scenarios for *crop* on *land_acres*.

    Scenarios use P25 / median / P75 quantiles for yield and price, following
    the assumption in ``docs/assumptions.md`` that extremes occur together
    (this exaggerates the spread — document this in the viva).

    When fewer than ``MIN_RECORDS_FOR_COLOUR`` rows are available the
    percentile calculation falls back to the min/mean/max of whatever data
    exists, and the ``low_data`` flag is set to True.

    The effective price used for each scenario is
    ``max(market_price_percentile, latest_msp)`` to honour the MSP floor.
    If MSP data is unavailable, only the market price is used.

    Parameters
    ----------
    crop : str
        Crop name (case-insensitive).
    state : str
        State name (exact match).
    season : str
        Season name (exact match, whitespace-stripped).
    land_acres : float
        Land size in acres; all revenue and profit figures are returned both
        per-acre and as a total (per-acre × land_acres).
    df_yield_price : pd.DataFrame
        Loaded yield-price DataFrame.
    df_msp : pd.DataFrame
        Loaded MSP DataFrame.
    cost_override : float | None
        Total cultivation cost for *land_acres* (₹).  If None, profit figures
        are None (gross revenue is still returned).

    Returns
    -------
    dict with keys:
        ``scenarios``   — list of three dicts (bad / normal / good), each with:
                          ``label``, ``yield_per_acre``, ``price_per_quintal``,
                          ``effective_price``, ``revenue_per_acre``,
                          ``revenue_total``, ``profit_per_acre`` (None if no
                          cost), ``profit_total`` (None if no cost)
        ``msp``         — latest MSP value or None
        ``msp_available`` — bool
        ``low_data``    — bool (True when fewer than MIN_RECORDS_FOR_COLOUR rows)
        ``placeholder`` — bool (True when any row is tagged PLACEHOLDER)
        ``no_data``     — bool (True when no rows at all)

    Notes
    -----
    Satisfies Requirements 5.1–5.5.
    """
    min_records = get_config("MIN_RECORDS_FOR_COLOUR")

    rows = _filter_yield(df_yield_price, state, season, crop)
    msp_value = _latest_msp(df_msp, crop)
    placeholder = _is_placeholder(rows)

    # ------------------------------------------------------------------
    # No data at all
    # ------------------------------------------------------------------
    if rows.empty:
        return {
            "scenarios": [],
            "msp": msp_value,
            "msp_available": msp_value is not None,
            "low_data": True,
            "placeholder": True,
            "no_data": True,
        }

    yields = rows["yield_quintal_per_acre"]
    prices = rows["price_per_quintal"]
    low_data = len(rows) < min_records

    # ------------------------------------------------------------------
    # Compute percentile (or min/mean/max when data is sparse)
    # ------------------------------------------------------------------
    if low_data:
        y_bad    = float(yields.min())
        y_normal = float(yields.mean())
        y_good   = float(yields.max())
        p_bad    = float(prices.min())
        p_normal = float(prices.mean())
        p_good   = float(prices.max())
    else:
        y_bad    = float(yields.quantile(0.25))
        y_normal = float(yields.quantile(0.50))
        y_good   = float(yields.quantile(0.75))
        p_bad    = float(prices.quantile(0.25))
        p_normal = float(prices.quantile(0.50))
        p_good   = float(prices.quantile(0.75))

    # ------------------------------------------------------------------
    # Build scenarios, applying MSP floor
    # ------------------------------------------------------------------
    scenario_data = [
        ("bad",    y_bad,    p_bad),
        ("normal", y_normal, p_normal),
        ("good",   y_good,   p_good),
    ]

    scenarios = []
    for label, y, p in scenario_data:
        effective_p = max(p, msp_value) if msp_value is not None else p
        rev_per_acre = y * effective_p
        rev_total    = rev_per_acre * land_acres

        if cost_override is not None:
            profit_per_acre = rev_per_acre - (cost_override / land_acres) if land_acres > 0 else None
            profit_total    = rev_total - cost_override if land_acres > 0 else None
        else:
            profit_per_acre = None
            profit_total    = None

        scenarios.append({
            "label":            label,
            "yield_per_acre":   y,
            "price_per_quintal": p,
            "effective_price":  effective_p,
            "revenue_per_acre": rev_per_acre,
            "revenue_total":    rev_total,
            "profit_per_acre":  profit_per_acre,
            "profit_total":     profit_total,
        })

    return {
        "scenarios":      scenarios,
        "msp":            msp_value,
        "msp_available":  msp_value is not None,
        "low_data":       low_data,
        "placeholder":    placeholder,
        "no_data":        False,
    }


# ---------------------------------------------------------------------------
# profit_range_per_acre
# ---------------------------------------------------------------------------

def profit_range_per_acre(
    crop: str,
    state: str,
    season: str,
    df_yield_price: pd.DataFrame,
    df_msp: pd.DataFrame,
) -> tuple[float, float] | None:
    """Return ``(min_profit_per_acre, max_profit_per_acre)`` for *crop*.

    Uses the bad-scenario revenue (P25 yield × effective P25 price) as the
    minimum and good-scenario revenue (P75 yield × effective P75 price) as the
    maximum.  Cost is not included, so these are gross-revenue extremes per
    acre.

    Returns ``None`` when there is no data for the selection.

    Parameters
    ----------
    crop : str
        Crop name (case-insensitive).
    state : str
        State name.
    season : str
        Season name.
    df_yield_price : pd.DataFrame
        Loaded yield-price DataFrame.
    df_msp : pd.DataFrame
        Loaded MSP DataFrame.

    Returns
    -------
    tuple[float, float] | None
        ``(min_revenue_per_acre, max_revenue_per_acre)`` or ``None``.

    Notes
    -----
    Satisfies Requirement 5.2: profit range for risk badge on crop cards.
    """
    rows = _filter_yield(df_yield_price, state, season, crop)
    if rows.empty:
        return None

    msp_value = _latest_msp(df_msp, crop)
    min_records = get_config("MIN_RECORDS_FOR_COLOUR")
    low_data = len(rows) < min_records

    yields = rows["yield_quintal_per_acre"]
    prices = rows["price_per_quintal"]

    if low_data:
        y_min, y_max = float(yields.min()), float(yields.max())
        p_min, p_max = float(prices.min()), float(prices.max())
    else:
        y_min, y_max = float(yields.quantile(0.25)), float(yields.quantile(0.75))
        p_min, p_max = float(prices.quantile(0.25)), float(prices.quantile(0.75))

    eff_p_min = max(p_min, msp_value) if msp_value is not None else p_min
    eff_p_max = max(p_max, msp_value) if msp_value is not None else p_max

    min_rev = y_min * eff_p_min
    max_rev = y_max * eff_p_max

    return (min_rev, max_rev)


# ---------------------------------------------------------------------------
# break_even_price
# ---------------------------------------------------------------------------

def break_even_price(total_cost_per_acre: float, yield_per_acre: float) -> float:
    """Return the price per quintal at which the farmer breaks even.

    Break-even price = total cost per acre ÷ yield per acre (quintals).

    Parameters
    ----------
    total_cost_per_acre : float
        Total cultivation cost in ₹ per acre.
    yield_per_acre : float
        Expected yield in quintals per acre (must be > 0).

    Returns
    -------
    float
        Break-even price in ₹ per quintal.

    Raises
    ------
    ValueError
        If *yield_per_acre* is zero or negative.

    Notes
    -----
    Satisfies Requirement 5.4: break-even price shown alongside profit chart.
    """
    if yield_per_acre <= 0:
        raise ValueError(
            f"yield_per_acre must be positive; got {yield_per_acre}."
        )
    return total_cost_per_acre / yield_per_acre


# ---------------------------------------------------------------------------
# rank_top3
# ---------------------------------------------------------------------------

def rank_top3(
    state: str,
    season: str,
    land_acres: float,
    df_yield_price: pd.DataFrame,
    df_msp: pd.DataFrame,
    cost_per_acre: float | None = None,
) -> list[dict]:
    """Return the top 3 crops ranked by a combined profit-and-risk score.

    Scoring methodology
    -------------------
    For each crop we compute two raw signals:

    1. **Expected revenue per acre** — the midpoint of the profit range:
       ``mean_rev = (min_revenue_per_acre + max_revenue_per_acre) / 2``
       using ``profit_range_per_acre()``, which already applies the MSP floor.

    2. **Coefficient of variation (CV)** — ``std / mean`` of all
       historical per-acre revenue values (yield × price) for that crop,
       state, and season.  Revenue is used rather than yield alone so the
       price dimension is captured.  When fewer than MIN_RECORDS_FOR_COLOUR
       rows exist, CV defaults to 1.0 (treated as maximum risk / red).

    Both signals are min-max normalised across all candidate crops so they
    are dimensionless and comparable on [0, 1]:

        norm_rev  = (rev  - rev_min)  / (rev_max  - rev_min)   [higher → better]
        norm_cv   = (cv   - cv_min)   / (cv_max   - cv_min)    [lower  → better]

    When all crops have identical revenue (range = 0) or identical CV,
    the normalised dimension is set to 0.5 for all (tie-neutral).

    The combined score is a weighted sum:

        score = 0.80 × norm_rev + 0.20 × (1 - norm_cv)

    The 80/20 split prioritises revenue while still penalising high-risk
    crops.  If all crops share the same revenue *and* the same CV, they are
    ranked alphabetically as a deterministic tie-break.

    Parameters
    ----------
    state : str
        State name (exact match as stored in the CSV).
    season : str
        Season name (whitespace-stripped; matched exactly).
    land_acres : float
        Farm size in acres (passed through to ``profit_range_per_acre``).
        ``profit_range_per_acre`` does not currently use ``land_acres`` but
        the parameter is forwarded for forward-compatibility.
    df_yield_price : pd.DataFrame
        Loaded yield-price DataFrame (from ``data_loader.load_yield_price``).
    df_msp : pd.DataFrame
        Loaded MSP DataFrame (from ``data_loader.load_msp``).
    cost_per_acre : float | None
        Optional total cultivation cost per acre (₹).  Reserved for future
        use; not used in the current scoring formula so that ranking works
        even when the user has not entered costs yet.

    Returns
    -------
    list[dict]
        Up to 3 dicts, each containing:

        ``crop``                  — crop name (str)
        ``min_revenue_per_acre``  — float, bad-scenario revenue (₹/acre)
        ``max_revenue_per_acre``  — float, good-scenario revenue (₹/acre)
        ``cv``                    — float, coefficient of variation of revenue
        ``risk_colour``           — "green" | "yellow" | "red"
        ``rank``                  — 1, 2, or 3

        Returns [] if no crops are available for the selection.

    Notes
    -----
    Requirements: 3.3 (top-3 crop ranking with risk).
    """
    from core.risk import cv_risk_colour  # local import avoids circular import

    min_records = get_config("MIN_RECORDS_FOR_COLOUR")

    # ------------------------------------------------------------------
    # Step 1: get candidate crops
    # ------------------------------------------------------------------
    crops = available_crops(state, season, df_yield_price)
    if not crops:
        return []

    # ------------------------------------------------------------------
    # Step 2: collect raw signals for each crop
    # ------------------------------------------------------------------
    candidates: list[dict] = []

    for crop in crops:
        # Revenue range (applies MSP floor internally)
        rev_range = profit_range_per_acre(crop, state, season, df_yield_price, df_msp)
        if rev_range is None:
            # Skip crops with no data (shouldn't happen given available_crops, but be safe)
            continue
        min_rev, max_rev = rev_range
        mean_rev = (min_rev + max_rev) / 2.0

        # CV of per-acre revenue from raw data
        rows = _filter_yield(df_yield_price, state, season, crop)
        msp_value = _latest_msp(df_msp, crop)

        if len(rows) < min_records:
            # Too few rows — treat as maximum risk
            cv = 1.0
        else:
            # Revenue per-acre observation = yield * effective_price
            def _eff_price(p: float) -> float:
                return max(p, msp_value) if msp_value is not None else p

            revenues = rows.apply(
                lambda r: r["yield_quintal_per_acre"] * _eff_price(r["price_per_quintal"]),
                axis=1,
            )
            mean_r = revenues.mean()
            if mean_r == 0:
                cv = 1.0
            else:
                cv = float(revenues.std(ddof=1) / mean_r)

        risk_colour = cv_risk_colour(cv)

        candidates.append(
            {
                "crop": crop,
                "min_revenue_per_acre": min_rev,
                "max_revenue_per_acre": max_rev,
                "mean_rev": mean_rev,
                "cv": cv,
                "risk_colour": risk_colour,
            }
        )

    if not candidates:
        return []

    # ------------------------------------------------------------------
    # Step 3: min-max normalise revenue and CV across candidates
    # ------------------------------------------------------------------
    rev_values = [c["mean_rev"] for c in candidates]
    cv_values  = [c["cv"]       for c in candidates]

    rev_min, rev_max = min(rev_values), max(rev_values)
    cv_min,  cv_max  = min(cv_values),  max(cv_values)

    def _norm(value: float, lo: float, hi: float) -> float:
        if hi == lo:
            return 0.5
        return (value - lo) / (hi - lo)

    # ------------------------------------------------------------------
    # Step 4: compute score and sort (descending)
    # ------------------------------------------------------------------
    for c in candidates:
        norm_rev = _norm(c["mean_rev"], rev_min, rev_max)
        norm_cv  = _norm(c["cv"],       cv_min,  cv_max)
        c["score"] = 0.80 * norm_rev + 0.20 * (1.0 - norm_cv)

    # Sort: higher score first; tie-break alphabetically by crop name
    candidates.sort(key=lambda c: (-c["score"], c["crop"]))

    # ------------------------------------------------------------------
    # Step 5: take top 3, assign ranks, strip internal fields
    # ------------------------------------------------------------------
    top3 = candidates[:3]
    result = []
    for rank, c in enumerate(top3, start=1):
        result.append(
            {
                "crop":                 c["crop"],
                "min_revenue_per_acre": c["min_revenue_per_acre"],
                "max_revenue_per_acre": c["max_revenue_per_acre"],
                "cv":                   c["cv"],
                "risk_colour":          c["risk_colour"],
                "rank":                 rank,
            }
        )
    return result
