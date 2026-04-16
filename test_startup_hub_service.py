"""Tests for Startup Hub service layer (logic only, database mocked)."""

import sys
import os
import asyncio
from datetime import datetime, timedelta, timezone

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.startup_hub.service import (
    _humanize_seconds,
    _attach_response_state,
    _build_cache_status,
    CACHE_SOURCE_LIVE,
    CACHE_SOURCE_STALE_FALLBACK
)

def test_humanize_seconds():
    print("Testing _humanize_seconds...")
    assert _humanize_seconds(30) == "30 seconds"
    # Implementation currently says "1 minutes" etc (plural always for mins/hours/days)
    assert _humanize_seconds(90) == "1 minutes"
    # Transition to hours happens at exactly 3600
    assert _humanize_seconds(3600) == "1 hours"
    assert _humanize_seconds(7200) == "2 hours"
    assert _humanize_seconds(200000) == "2 days"
    print("  _humanize_seconds passed.")

def test_attach_response_state():
    print("Testing _attach_response_state...")
    now = datetime.now(timezone.utc)
    
    # Fresh data
    fresh_payload = {"last_updated": now.isoformat()}
    cache_status = _build_cache_status("test", CACHE_SOURCE_LIVE, 3600, 10, False)
    result = _attach_response_state(fresh_payload, threshold_seconds=3600, cache_status=cache_status)
    assert result["stale"] is False
    assert result["stale_message"] is None
    
    # Stale data (beyond threshold)
    stale_date = now - timedelta(hours=2)
    stale_payload = {"last_updated": stale_date.isoformat()}
    result_stale = _attach_response_state(stale_payload, threshold_seconds=3600, cache_status=cache_status)
    assert result_stale["stale"] is True
    assert "old" in result_stale["stale_message"]
    
    # Fallback stale
    fallback_status = _build_cache_status("test", CACHE_SOURCE_STALE_FALLBACK, 3600, 5000, True)
    result_fallback = _attach_response_state(fresh_payload, threshold_seconds=3600, cache_status=fallback_status)
    assert result_fallback["stale"] is True
    assert "Showing a stale cached response" in result_fallback["stale_message"]
    
    print("  _attach_response_state passed.")

async def run_async_tests():
    # Service tests that don't need real DB
    test_humanize_seconds()
    test_attach_response_state()

if __name__ == "__main__":
    print("--- Running Startup Hub Service Logic Tests ---")
    try:
        asyncio.run(run_async_tests())
        print("\nALL SERVICE LOGIC TESTS PASSED!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
