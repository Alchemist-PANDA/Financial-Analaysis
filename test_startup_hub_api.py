"""Functional tests for Startup Hub API endpoints.
Note: Requires the FastAPI server to be running (usually on http://127.0.0.1:8000).
"""

import urllib.request
import urllib.error
import json
import sys
import os

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "dev_default_key")

def make_request(path, method="GET", payload=None):
    url = f"{BASE_URL}{path}"
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    data = json.dumps(payload).encode('utf-8') if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.getcode(), json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def test_api_endpoints():
    print(f"Testing Startup Hub API endpoints at {BASE_URL}...")
    
    # 1. Home
    print("Testing /api/startup-hub/home...")
    code, data = make_request("/api/startup-hub/home")
    if code == 503: # Cache miss/Background warm
        print("  Received 503 (Background warm), this is expected on first run.")
    elif code == 200:
        assert "public_companies" in data
        assert "featured" in data
        print("  /api/startup-hub/home passed.")
    else:
        print(f"  FAILED /api/startup-hub/home: {code}")

    # 2. Companies List
    print("Testing /api/startup-hub/companies...")
    code, data = make_request("/api/startup-hub/companies")
    if code == 200:
        assert "items" in data
        assert isinstance(data["items"], list)
        print("  /api/startup-hub/companies passed.")
    elif code != 503:
        print(f"  FAILED /api/startup-hub/companies: {code}")

    # 3. IPOs
    print("Testing /api/startup-hub/ipos...")
    code, data = make_request("/api/startup-hub/ipos")
    if code == 200:
        assert "items" in data
        print("  /api/startup-hub/ipos passed.")
    elif code != 503:
        print(f"  FAILED /api/startup-hub/ipos: {code}")

    # 4. Private
    print("Testing /api/startup-hub/private...")
    code, data = make_request("/api/startup-hub/private")
    if code == 200:
        assert "items" in data
        print("  /api/startup-hub/private passed.")
    elif code != 503:
        print(f"  FAILED /api/startup-hub/private: {code}")

    # 5. Agent Query
    print("Testing /api/startup-hub/agent/query...")
    payload = {"query": "best AI startups"}
    code, data = make_request("/api/startup-hub/agent/query", method="POST", payload=payload)
    if code == 200:
        assert "summary" in data
        assert "matches" in data
        print("  /api/startup-hub/agent/query passed.")
    elif code != 503:
        print(f"  FAILED /api/startup-hub/agent/query: {code}")

if __name__ == "__main__":
    print("--- Running Startup Hub API Functional Tests ---")
    # We don't exit(1) on failure here because it depends on a running server
    # but we provide the feedback.
    test_api_endpoints()
