
from app.api import build_response_payload

def test_build_response_payload_none_metrics():
    print("Testing build_response_payload with metrics=None...")
    try:
        result = build_response_payload("AAPL", "Apple Inc.", None, {"flags": []})
        print("SUCCESS: Handled metrics=None")
        print(f"Result keys: {result.keys()}")
    except Exception as e:
        print(f"FAILED: {e}")

def test_build_response_payload_none_analysis():
    print("\nTesting build_response_payload with analysis=None...")
    try:
        result = build_response_payload("AAPL", "Apple Inc.", {"current_z_score": 3.5}, None)
        print("SUCCESS: Handled analysis=None")
        print(f"Result keys: {result.keys()}")
        print(f"Analysis: {result['analysis']}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_build_response_payload_none_metrics()
    test_build_response_payload_none_analysis()
