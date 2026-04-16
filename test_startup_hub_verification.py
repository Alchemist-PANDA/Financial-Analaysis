"""Tests for Startup Hub verification logic."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.startup_hub.verification import (
    verify_public_company,
    verify_ipo_company,
    verify_private_opportunity,
    VERIFICATION_LEVEL_VERIFIED_PUBLIC,
    VERIFICATION_LEVEL_VERIFIED_IPO,
    VERIFICATION_LEVEL_SOURCE_VERIFIED_PRIVATE,
    VERIFICATION_LEVEL_PARTIAL,
    VERIFICATION_LEVEL_UNVERIFIED
)

def test_verify_public_company():
    print("Testing verify_public_company...")
    
    # Fully verified
    company = {"ticker": "AAPL", "exchange": "NASDAQ", "website_url": "https://apple.com"}
    snapshot = {}
    sources = [{"source_name": "SEC", "source_url": "https://sec.gov", "is_official": True}]
    result = verify_public_company(company, snapshot, sources)
    assert result["level"] == VERIFICATION_LEVEL_VERIFIED_PUBLIC
    assert result["is_verified"] is True
    
    # Partial (no website/official source)
    company_partial = {"ticker": "TEST", "exchange": "OTC"}
    result_partial = verify_public_company(company_partial, {}, [])
    assert result_partial["level"] == VERIFICATION_LEVEL_PARTIAL
    assert result_partial["is_verified"] is False
    
    # Unverified
    result_unverified = verify_public_company({}, {}, [])
    assert result_unverified["level"] == VERIFICATION_LEVEL_UNVERIFIED
    
    print("  verify_public_company passed.")

def test_verify_ipo_company():
    print("Testing verify_ipo_company...")
    
    # Verified IPO
    company = {"status_label": "Filed S-1"}
    snapshot = {"data_payload": {"filing_url": "https://sec.gov/s1"}}
    result = verify_ipo_company(company, snapshot, [])
    assert result["level"] == VERIFICATION_LEVEL_VERIFIED_IPO
    
    # Partial IPO
    result_partial = verify_ipo_company({"status_label": "Rumored"}, {}, [])
    assert result_partial["level"] == VERIFICATION_LEVEL_PARTIAL
    
    print("  verify_ipo_company passed.")

def test_verify_private_opportunity():
    print("Testing verify_private_opportunity...")
    
    # Verified Private
    company = {
        "official_source_url": "https://forge.com/deal",
        "source_name": "Forge",
        "research_only": True
    }
    result = verify_private_opportunity(company, {}, [])
    assert result["level"] == VERIFICATION_LEVEL_SOURCE_VERIFIED_PRIVATE
    
    # Partial Private (missing research_only flag)
    company_partial = {
        "official_source_url": "https://forge.com/deal",
        "source_name": "Forge",
        "research_only": False
    }
    result_partial = verify_private_opportunity(company_partial, {}, [])
    assert result_partial["level"] == VERIFICATION_LEVEL_PARTIAL
    
    print("  verify_private_opportunity passed.")

if __name__ == "__main__":
    print("--- Running Startup Hub Verification Tests ---")
    try:
        test_verify_public_company()
        test_verify_ipo_company()
        test_verify_private_opportunity()
        print("\nALL VERIFICATION TESTS PASSED!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
