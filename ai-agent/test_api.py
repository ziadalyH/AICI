#!/usr/bin/env python3
"""
Simple test script for the Hybrid RAG AI Agent API.
"""
import requests
import json
import sys

# API endpoint
BASE_URL = "http://localhost:8001"

def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_root():
    """Test the root endpoint."""
    print("\nTesting root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_query_simple():
    """Test a simple query without drawing JSON."""
    print("\nTesting simple query...")
    try:
        payload = {
            "question": "What are the building height restrictions?",
            "top_k": 3
        }
        response = requests.post(
            f"{BASE_URL}/api/agent/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_query_with_drawing():
    """Test a query with drawing JSON."""
    print("\nTesting query with drawing JSON...")
    try:
        payload = {
            "question": "Does my building comply with height regulations?",
            "drawing_json": {
                "id": "building_001",
                "type": "residential",
                "properties": {
                    "height": 15.5,
                    "floors": 3,
                    "zone": "residential",
                    "area": 250
                }
            },
            "top_k": 5
        }
        response = requests.post(
            f"{BASE_URL}/api/agent/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 80)
    print("Hybrid RAG AI Agent API Test Suite")
    print("=" * 80)
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("Simple Query", test_query_simple),
        ("Query with Drawing JSON", test_query_with_drawing),
    ]
    
    results = []
    for name, test_func in tests:
        print("\n" + "=" * 80)
        result = test_func()
        results.append((name, result))
        print("=" * 80)
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    # Exit code
    all_passed = all(result for _, result in results)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
