"""
core/formatting.py
------------------
Display-formatting utilities for AgriSecure AI.

No numbers are invented here. These functions only reformat values they
are given. All UI text (labels, units) must come from lang/*.json; these
functions return only the numeric-string portion.

Requirements: 2.4, G4
"""

import math


def indian_format(amount: float) -> str:
    """
    Format *amount* as an Indian-numbering-system rupee string.

    The Indian system groups the rightmost three digits, then every two
    digits to the left, separated by commas.

    Examples
    --------
    >>> indian_format(125000)
    '₹1,25,000'
    >>> indian_format(1000)
    '₹1,000'
    >>> indian_format(10000000)
    '₹1,00,00,000'
    >>> indian_format(0)
    '₹0'
    >>> indian_format(-125000)
    '-₹1,25,000'
    """
    # Round to nearest integer; handle negative separately.
    rounded = int(math.floor(abs(amount) + 0.5))
    negative = amount < 0

    s = str(rounded)

    if len(s) <= 3:
        formatted = s
    else:
        # Keep the last 3 digits as the first group.
        last3 = s[-3:]
        rest = s[:-3]
        # Group remaining digits in pairs from the right.
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        groups.reverse()
        formatted = ",".join(groups) + "," + last3

    prefix = "-₹" if negative else "₹"
    return prefix + formatted


def acres_cents(acres: float) -> str:
    """
    Convert a decimal *acres* value to a human-readable "X acres Y cents"
    string where 1 acre = 100 cents.

    Rules
    -----
    - Whole-number acre part uses "acre" (1) vs "acres" (>1 or 0).
    - Cent remainder uses "cent" (1) vs "cents" (otherwise).
    - Zero cents are not shown.
    - Zero acres are not shown when there is a cent component.

    Examples
    --------
    >>> acres_cents(1.5)
    '1 acre 50 cents'
    >>> acres_cents(1.0)
    '1 acre'
    >>> acres_cents(0.25)
    '25 cents'
    >>> acres_cents(2.75)
    '2 acres 75 cents'
    >>> acres_cents(1.01)
    '1 acre 1 cent'
    """
    # Split into whole acres and cent remainder.
    # Round to avoid floating-point drift (e.g. 0.10 → 9.999... cents).
    total_cents = round(acres * 100)
    whole_acres = total_cents // 100
    remaining_cents = total_cents % 100

    parts = []

    if whole_acres > 0:
        acre_word = "acre" if whole_acres == 1 else "acres"
        parts.append(f"{whole_acres} {acre_word}")

    if remaining_cents > 0:
        cent_word = "cent" if remaining_cents == 1 else "cents"
        parts.append(f"{remaining_cents} {cent_word}")

    # Edge case: exactly 0 acres 0 cents
    if not parts:
        return "0 acres"

    return " ".join(parts)
