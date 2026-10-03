"""
core/data_loader.py — AgriSecure AI
=====================================

Pure functions for loading and validating the three project CSVs.

Design rules
------------
- No Streamlit imports. st.cache_data wrappers belong in the UI layer.
- No numbers are invented. Missing or negative values raise ValueError so the
  UI can show a localized message (Requirement 19.2).
- Season names are stripped of whitespace on load (Requirement 2.6 / 19.4).

Public API
----------
validate_row   — check a single row for null/negative numeric fields
strip_season   — strip whitespace from the 'season' column (pure, no mutation)
load_cost      — read data/cost.csv and validate
load_yield_price — read data/yield_price.csv and validate
load_msp       — read data/msp.csv and validate
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Row validation
# ---------------------------------------------------------------------------

def validate_row(row: pd.Series, numeric_fields: list[str], row_index: int) -> None:
    """Validate that all *numeric_fields* in *row* are non-null and non-negative.

    Parameters
    ----------
    row : pd.Series
        A single DataFrame row (from ``df.iterrows()`` or similar).
    numeric_fields : list[str]
        Column names that must be numeric, non-null, and >= 0.
    row_index : int
        The integer row index used in error messages so the caller can
        locate the offending row in the source CSV.

    Raises
    ------
    ValueError
        If a field is null/NaN: ``"Row {row_index}: field '{field}' is null"``
        If a field is negative: ``"Row {row_index}: field '{field}' is negative ({value})"``

    Notes
    -----
    Satisfies Requirement 19.2: "raise ValueError naming the field, row and problem."
    """
    for field in numeric_fields:
        value = row[field]
        if pd.isna(value):
            raise ValueError(f"Row {row_index}: field '{field}' is null")
        if value < 0:
            raise ValueError(
                f"Row {row_index}: field '{field}' is negative ({value})"
            )


# ---------------------------------------------------------------------------
# Season whitespace stripping
# ---------------------------------------------------------------------------

def strip_season(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with leading/trailing whitespace removed from the
    ``season`` column.

    If the ``season`` column does not exist the DataFrame is returned unchanged.
    This is a pure function — the input *df* is not mutated.

    Parameters
    ----------
    df : pd.DataFrame
        Any DataFrame that may contain a ``season`` column.

    Returns
    -------
    pd.DataFrame
        A new DataFrame (copy) with the ``season`` column stripped.

    Notes
    -----
    Satisfies Requirements 2.6 and 19.4: "strip whitespace from Season names."
    """
    df = df.copy()
    if "season" in df.columns:
        df["season"] = df["season"].str.strip()
    return df


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------

def load_cost(path: str) -> pd.DataFrame:
    """Load and validate ``data/cost.csv``.

    Steps
    -----
    1. Read the CSV from *path*.
    2. Strip whitespace from the ``season`` column via :func:`strip_season`.
    3. Validate every row: ``seed``, ``fertilizer``, ``labour``,
       ``irrigation``, and ``other`` must be non-null and non-negative.

    Parameters
    ----------
    path : str
        Filesystem path to the cost CSV file.

    Returns
    -------
    pd.DataFrame
        Cleaned cost DataFrame ready for use by ``CostEstimator``.

    Raises
    ------
    ValueError
        If any numeric field in any row is null or negative (via
        :func:`validate_row`).
    FileNotFoundError
        If *path* does not exist.
    """
    df = pd.read_csv(path)
    df = strip_season(df)
    numeric_fields = ["seed", "fertilizer", "labour", "irrigation", "other"]
    for idx, row in df.iterrows():
        validate_row(row, numeric_fields, idx)
    return df


def load_yield_price(path: str) -> pd.DataFrame:
    """Load and validate ``data/yield_price.csv``.

    Steps
    -----
    1. Read the CSV from *path*.
    2. Strip whitespace from the ``season`` column.
    3. Validate ``yield_quintal_per_acre`` and ``price_per_quintal`` for every
       row: must be non-null and non-negative.

    Parameters
    ----------
    path : str
        Filesystem path to the yield/price CSV file.

    Returns
    -------
    pd.DataFrame
        Cleaned yield-price DataFrame ready for use by ``CropAdvisor`` and
        ``RiskEngine``.

    Raises
    ------
    ValueError
        If any numeric field in any row is null or negative.
    FileNotFoundError
        If *path* does not exist.
    """
    df = pd.read_csv(path)
    df = strip_season(df)
    numeric_fields = ["yield_quintal_per_acre", "price_per_quintal"]
    for idx, row in df.iterrows():
        validate_row(row, numeric_fields, idx)
    return df


def load_msp(path: str) -> pd.DataFrame:
    """Load and validate ``data/msp.csv``.

    Steps
    -----
    1. Read the CSV from *path*.
    2. Validate ``msp_per_quintal`` for every row: must be non-null and
       non-negative.

    Parameters
    ----------
    path : str
        Filesystem path to the MSP CSV file.

    Returns
    -------
    pd.DataFrame
        Cleaned MSP DataFrame ready for use by ``CropAdvisor``.

    Raises
    ------
    ValueError
        If any numeric field in any row is null or negative.
    FileNotFoundError
        If *path* does not exist.
    """
    df = pd.read_csv(path)
    numeric_fields = ["msp_per_quintal"]
    for idx, row in df.iterrows():
        validate_row(row, numeric_fields, idx)
    return df
