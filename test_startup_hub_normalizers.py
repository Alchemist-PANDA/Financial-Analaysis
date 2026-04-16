"""Tests for Startup Hub normalizers."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.startup_hub.normalizers import (
    safe_float,
    safe_int,
    clean_company_name,
    build_slug,
    compute_data_completeness_score,
    normalize_public_company,
    normalize_ipo_company,
    normalize_private_opportunity
)

def test_safe_float():
    print("Testing safe_float...")
    assert safe_float(None) is None
    assert safe_float("123.45") == 123.45
    assert safe_float("1,234.56") == 1234.56
    assert safe_float("$100.00") == 100.00
    assert safe_float("10%") == 10.0
    assert safe_float("(50.0)") == -50.0
    assert safe_float("1.5M") == 1500000.0
    assert safe_float("2.1B") == 2100000000.0
    assert safe_float("invalid") is None
    assert safe_float(True) is None
    print("  safe_float passed.")

def test_safe_int():
    print("Testing safe_int...")
    assert safe_int("100") == 100
    assert safe_int("100.6") == 101
    assert safe_int(None) is None
    print("  safe_int passed.")

def test_clean_company_name():
    print("Testing clean_company_name...")
    assert clean_company_name("  Apple Inc.  ") == "Apple Inc."
    assert clean_company_name("Apple &amp; Pear") == "Apple & Pear"
    val = clean_company_name("Quotes 'n' \"Double\"")
    # implementation strips quotes if they are at the very start/end
    assert val == "Quotes 'n' \"Double", f"Got {repr(val)}"
    print("  clean_company_name passed.")

def test_build_slug():
    print("Testing build_slug...")
    assert build_slug("Apple Inc.") == "apple-inc"
    assert build_slug("C3.ai") == "c3-ai"
    assert build_slug("Scale AI & Co") == "scale-ai-and-co"
    assert build_slug("  ") == "unknown-company"
    print("  build_slug passed.")

def test_completeness_score():
    print("Testing compute_data_completeness_score...")
    data = {"name": "Test", "sector": "Tech", "empty": "", "missing": None}
    score = compute_data_completeness_score(data, required_fields=["name", "sector", "empty", "missing"])
    # name and sector are present (2/4 = 0.5)
    assert score == 0.5
    print("  compute_data_completeness_score passed.")

def test_normalizers():
    print("Testing normalization pipelines...")
    
    # Public
    print("  Subtest: Public...")
    raw_public = {
        "company_name": "Test Public",
        "ticker": "TPUB",
        "revenue_growth_pct": "15.5%",
        "z_score": "2.5"
    }
    norm_public = normalize_public_company(raw_public)
    assert norm_public["company_name"] == "Test Public"
    assert norm_public["ticker"] == "TPUB"
    
    # IPO
    print("  Subtest: IPO...")
    raw_ipo = {
        "name": "Test IPO",
        "filing_status": "filed",
        "proposed_exchange": "nasdaq"
    }
    norm_ipo = normalize_ipo_company(raw_ipo)
    assert norm_ipo["company_name"] == "Test IPO"
    # In normalize_ipo_company, filing_status is explicitly set from the input
    assert norm_ipo["filing_status"] == "filed"
    
    # Private
    print("  Subtest: Private...")
    raw_private = {
        "title": "Test Private",
        "valuation_usd": "1.2B"
    }
    norm_private = normalize_private_opportunity(raw_private)
    assert norm_private["company_name"] == "Test Private"
    assert norm_private["valuation_usd"] == 1200000000.0
    
    print("  Normalization pipelines passed.")

if __name__ == "__main__":
    print("--- Running Startup Hub Normalizer Tests ---")
    try:
        test_safe_float()
        test_safe_int()
        test_clean_company_name()
        test_build_slug()
        test_completeness_score()
        test_normalizers()
        print("\nALL NORMALIZER TESTS PASSED!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
