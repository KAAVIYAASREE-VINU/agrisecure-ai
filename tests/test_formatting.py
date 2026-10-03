"""
tests/test_formatting.py
------------------------
Unit tests for core/formatting.py (indian_format and acres_cents).

Requirements: 2.4, G4
"""

import pytest
from core.formatting import indian_format, acres_cents


# ---------------------------------------------------------------------------
# indian_format
# ---------------------------------------------------------------------------

class TestIndianFormat:
    """Tests for indian_format()."""

    # --- zero and small values ---
    def test_zero(self):
        assert indian_format(0) == "₹0"

    def test_one_hundred(self):
        assert indian_format(100) == "₹100"

    def test_below_thousand(self):
        assert indian_format(999) == "₹999"

    # --- thousands boundary ---
    def test_one_thousand(self):
        assert indian_format(1000) == "₹1,000"

    def test_below_ten_thousand(self):
        assert indian_format(9999) == "₹9,999"

    def test_ten_thousand(self):
        assert indian_format(10000) == "₹10,000"

    # --- lakhs range ---
    def test_below_lakh(self):
        assert indian_format(99999) == "₹99,999"

    def test_one_lakh(self):
        assert indian_format(100000) == "₹1,00,000"

    def test_one_lakh_twenty_five_thousand(self):
        assert indian_format(125000) == "₹1,25,000"

    # --- ten lakhs / million ---
    def test_ten_lakh(self):
        assert indian_format(1000000) == "₹10,00,000"

    # --- crore ---
    def test_one_crore(self):
        assert indian_format(10000000) == "₹1,00,00,000"

    # --- negative numbers ---
    def test_negative_small(self):
        assert indian_format(-100) == "-₹100"

    def test_negative_lakh(self):
        assert indian_format(-125000) == "-₹1,25,000"

    def test_negative_crore(self):
        assert indian_format(-10000000) == "-₹1,00,00,000"

    # --- float rounding ---
    def test_float_rounds_down(self):
        assert indian_format(1000.4) == "₹1,000"

    def test_float_rounds_up(self):
        assert indian_format(1000.5) == "₹1,001"

    def test_float_large(self):
        assert indian_format(124999.9) == "₹1,25,000"

    def test_float_negative_rounds(self):
        assert indian_format(-999.6) == "-₹1,000"


# ---------------------------------------------------------------------------
# acres_cents
# ---------------------------------------------------------------------------

class TestAcresCents:
    """Tests for acres_cents()."""

    # --- whole acres ---
    def test_one_acre_exactly(self):
        assert acres_cents(1.0) == "1 acre"

    def test_two_acres_exactly(self):
        assert acres_cents(2.0) == "2 acres"

    def test_large_whole_acres(self):
        assert acres_cents(100.0) == "100 acres"

    # --- with cents ---
    def test_one_and_a_half_acres(self):
        assert acres_cents(1.5) == "1 acre 50 cents"

    def test_quarter_acre(self):
        assert acres_cents(0.25) == "25 cents"

    def test_two_and_three_quarter_acres(self):
        assert acres_cents(2.75) == "2 acres 75 cents"

    def test_tenth_of_an_acre(self):
        assert acres_cents(0.10) == "10 cents"

    def test_one_acre_ten_cents(self):
        assert acres_cents(1.10) == "1 acre 10 cents"

    # --- singular cent ---
    def test_one_cent_only(self):
        assert acres_cents(0.01) == "1 cent"

    def test_one_acre_one_cent(self):
        assert acres_cents(1.01) == "1 acre 1 cent"

    # --- plural acre, plural cents ---
    def test_plural_acres_plural_cents(self):
        assert acres_cents(3.50) == "3 acres 50 cents"

    # --- no zero cents shown ---
    def test_no_zero_cents(self):
        result = acres_cents(5.0)
        assert "cent" not in result
        assert result == "5 acres"

    # --- floating-point safety ---
    def test_float_precision_tenth(self):
        # 0.1 is a classic floating-point pitfall
        assert acres_cents(0.1) == "10 cents"

    def test_float_precision_1_1(self):
        assert acres_cents(1.1) == "1 acre 10 cents"
