"""Tests for Startup Hub ranking calculations."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.startup_hub.ranking import (
    compute_growth_score,
    compute_quality_score,
    compute_risk_score,
    compute_verification_score,
    compute_momentum_score,
    compute_total_ranking_score
)

def test_growth_score():
    print("Testing compute_growth_score...")
    
    # Strong growth
    company = {"metrics": {"revenue_growth_pct": 50.0, "user_growth_pct": 40.0}, "data_completeness_score": 1.0}
    score = compute_growth_score(company)
    # revenue_growth 50 -> high score, user_growth 40 -> high score. Average * 0.85 + completeness * 0.15
    assert score > 70
    
    # Zero growth, but complete data
    company_none = {"metrics": {}, "data_completeness_score": 1.0}
    score_none = compute_growth_score(company_none)
    # completeness * 0.35 = 35.0
    assert score_none == 35.0
    
    print("  compute_growth_score passed.")

def test_quality_score():
    print("Testing compute_quality_score...")
    
    # High quality (SaaS-like margins)
    company = {"metrics": {"gross_margin_pct": 80.0, "retention_pct": 120.0}, "data_completeness_score": 1.0}
    score = compute_quality_score(company)
    assert score > 80
    
    # Negative margins
    company_bad = {"metrics": {"gross_margin_pct": 10.0, "ebitda_margin_pct": -50.0}, "data_completeness_score": 0.5}
    score_bad = compute_quality_score(company_bad)
    assert score_bad < 30
    
    print("  compute_quality_score passed.")

def test_risk_score():
    print("Testing compute_risk_score...")
    
    # Low risk (high Z-score, low leverage)
    company = {"metrics": {"z_score": 4.5, "debt_to_ebitda": 0.5}, "data_completeness_score": 1.0}
    score = compute_risk_score(company)
    assert score > 80
    
    # High risk (distressed Z-score, high leverage)
    company_risk = {"metrics": {"z_score": 0.5, "debt_to_ebitda": 10.0}, "data_completeness_score": 1.0}
    score_risk = compute_risk_score(company_risk)
    assert score_risk < 30
    
    print("  compute_risk_score passed.")

def test_total_score():
    print("Testing compute_total_ranking_score...")
    
    # Healthy balanced company
    company = {
        "entity_type": "public_stock",
        "ticker": "TEST",
        "exchange": "NASDAQ",
        "website_url": "https://test.com",
        "metrics": {
            "revenue_growth_pct": 25.0,
            "gross_margin_pct": 65.0,
            "z_score": 3.0,
            "price_momentum_pct": 10.0
        },
        "data_completeness_score": 0.9
    }
    result = compute_total_ranking_score(company)
    assert "total_score" in result
    assert result["total_score"] > 50
    assert "growth_score" in result
    assert "explanation" in result
    assert len(result["top_drivers"]) > 0
    
    print("  compute_total_ranking_score passed.")

if __name__ == "__main__":
    print("--- Running Startup Hub Ranking Tests ---")
    try:
        test_growth_score()
        test_quality_score()
        test_risk_score()
        test_total_score()
        print("\nALL RANKING TESTS PASSED!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
