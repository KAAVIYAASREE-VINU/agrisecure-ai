"""
core/costs.py — AgriSecure AI
==============================

CostEstimator: estimate cultivation cost per acre for a crop/state/season,
scale by land size, and allow the farmer to override individual components.

Design rules
------------
- No Streamlit imports.
- No numbers are invented; all thresholds come from config.py via get_config().
- validate_row is NOT called here — the loader already validated on load.
- Season names arrive already stripped (data_loader.strip_season).
- Crop matching is case-insensitive; CSV stores lowercase names (Requirement 2.2).

Public API
----------
estimate_costs(cost_df, crop, state, season, acres, overrides=None) -> dict
    Returns a dict with keys:
        seed, fertilizer, labour, irrigation, other  — scaled ₹ values
        total                                        — sum of all five
        placeholder                                  — True if any source row
                                                       had note == PLACEHOLDER_TAG

Requirements: 4.1, 4.2, 4.4
"""

import pandas as pd

from config import get_config
from data.clean_data import PLACEHOLDER_TAG


# Ordered list of the five cost components (used throughout for consistency).
class NoDataError(ValueError):
    """Raised by estimate_costs when no CSV rows match the crop/state/season."""


# Ordered list of the five cost components (used throughout for consistency).
COST_COMPONENTS = ["seed", "fertilizer", "labour", "irrigation", "other"]


def estimate_costs(
    cost_df: pd.DataFrame,
    crop: str,
    state: str,
    season: str,
    acres: float,
    overrides: dict | None = None,
) -> dict:
    """Estimate total cultivation cost for the given selection, scaled to *acres*.

    Parameters
    ----------
    cost_df : pd.DataFrame
        Loaded and validated cost DataFrame (from ``data_loader.load_cost``).
        Expected columns: state, season, crop, seed, fertilizer, labour,
        irrigation, other, note.
    crop : str
        Crop name (matched case-insensitively against the lowercase values in
        the CSV).
    state : str
        State name (matched exactly, as stored in the CSV).
    season : str
        Season name (already whitespace-stripped; matched exactly).
    acres : float
        Land size in acres; each per-acre mean cost is multiplied by this.
    overrides : dict | None
        Optional dict mapping component names to farmer-edited values (₹ total,
        not per acre).  Valid keys: ``seed``, ``fertilizer``, ``labour``,
        ``irrigation``, ``other``.  Each value must be within
        ``[COST_COMPONENT_MIN, COST_COMPONENT_MAX]`` from config.py.

    Returns
    -------
    dict
        Keys: ``seed``, ``fertilizer``, ``labour``, ``irrigation``, ``other``,
        ``total`` (float), ``placeholder`` (bool).

    Raises
    ------
    ValueError
        If any override value is outside ``[COST_COMPONENT_MIN,
        COST_COMPONENT_MAX]`` or if an override key is not a valid component.

    Notes
    -----
    Satisfies Requirements 4.1 (named components, scaled by land size),
    4.2 (override range validation), 4.4 (PLACEHOLDER notice when data absent).
    """
    cost_min = get_config("COST_COMPONENT_MIN")
    cost_max = get_config("COST_COMPONENT_MAX")

    # ------------------------------------------------------------------
    # 1. Filter to matching rows (case-insensitive crop match)
    # ------------------------------------------------------------------
    mask = (
        (cost_df["state"] == state)
        & (cost_df["season"] == season)
        & (cost_df["crop"].str.lower() == crop.lower())
    )
    matching = cost_df[mask]

    # ------------------------------------------------------------------
    # 2. No matching rows → raise NoDataError (never return ₹0 silently)
    # ------------------------------------------------------------------
    if matching.empty:
        raise NoDataError(
            f"No cost data for crop=\'{crop}\', state=\'{state}\', season=\'{season}\'. "
            "Verify the CSV contains matching rows or add placeholder data."
        )

    # ------------------------------------------------------------------
    # 3. Compute mean of each component across matching rows, scale by acres
    # ------------------------------------------------------------------
    result = {}
    for component in COST_COMPONENTS:
        per_acre_mean = matching[component].mean()
        result[component] = per_acre_mean * acres

    # ------------------------------------------------------------------
    # 4. Apply overrides (validated against config thresholds)
    # ------------------------------------------------------------------
    if overrides:
        for key, value in overrides.items():
            if key not in COST_COMPONENTS:
                raise ValueError(
                    f"Invalid override key '{key}'. "
                    f"Must be one of: {', '.join(COST_COMPONENTS)}."
                )
            if value < cost_min or value > cost_max:
                raise ValueError(
                    f"Override for '{key}' is {value}, which is outside the "
                    f"allowed range [{cost_min}, {cost_max}]."
                )
            result[key] = float(value)

    # ------------------------------------------------------------------
    # 5. Recalculate total
    # ------------------------------------------------------------------
    result["total"] = sum(result[c] for c in COST_COMPONENTS)

    # ------------------------------------------------------------------
    # 6. Set placeholder flag based on note column in matching rows
    # ------------------------------------------------------------------
    if "note" in matching.columns:
        result["placeholder"] = bool(
            (matching["note"] == PLACEHOLDER_TAG).any()
        )
    else:
        result["placeholder"] = False

    return result
