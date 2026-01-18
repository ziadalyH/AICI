"""
Test script for the Agentic AI System.

This script demonstrates the agentic workflow with various example queries.
"""

import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8001"
AGENTIC_ENDPOINT = f"{BASE_URL}/api/agent/query-agentic"
STANDARD_ENDPOINT = f"{BASE_URL}/api/agent/query"


def print_separator(title: str = ""):
    """Print a visual separator."""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def print_response(response: Dict[str, Any], show_reasoning: bool = True):
    """Pretty print the response."""
    print("📝 ANSWER:")
    print("-" * 80)
    print(response.get("answer", "No answer"))
    print("-" * 80)
    
    if response.get("sources"):
        print("\n📚 SOURCES:")
        for i, source in enumerate(response["sources"], 1):
            print(f"\n  {i}. {source.get('document', 'Unknown')}")
            print(f"     Page: {source.get('page', 'N/A')}")
            print(f"     Relevance: {source.get('relevance', 0):.2f}")
    
    if show_reasoning and response.get("reasoning_steps"):
        print("\n🧠 REASONING STEPS:")
        for step in response["reasoning_steps"]:
            print(f"\n  Step {step['step']}: {step['action']}")
            print(f"  Arguments: {json.dumps(step['arguments'], indent=4)[:200]}...")
            result_preview = str(step['result'])[:150]
            print(f"  Result: {result_preview}...")


def test_query(
    question: str,
    drawing_json: Any = None,
    use_agentic: bool = True,
    description: str = ""
):
    """Test a query with the agentic or standard endpoint."""
    print_separator(description or question)
    
    endpoint = AGENTIC_ENDPOINT if use_agentic else STANDARD_ENDPOINT
    mode = "🤖 AGENTIC" if use_agentic else "📋 STANDARD"
    
    print(f"Mode: {mode}")
    print(f"Question: {question}")
    if drawing_json:
        print(f"Drawing: Provided ({len(drawing_json)} elements)")
    print()
    
    payload = {
        "question": question,
        "drawing_json": drawing_json,
        "drawing_updated_at": "2026-01-18T10:30:00Z"
    }
    
    try:
        print("⏳ Sending request...")
        response = requests.post(endpoint, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        print("✅ Response received\n")
        print_response(result, show_reasoning=use_agentic)
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (agent may be taking too long)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")


# Example drawing JSON
EXAMPLE_DRAWING = [
    {
        "type": "POLYLINE",
        "layer": "Walls",
        "points": [[0, 0], [10000, 0], [10000, 8000], [0, 8000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Walls",
        "points": [[3000, 8000], [7000, 8000], [7000, 15000], [3000, 15000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Plot Boundary",
        "points": [[0, 0], [20000, 0], [20000, 20000], [0, 20000]],
        "closed": True
    }
]

# Non-compliant drawing (7m extension)
NON_COMPLIANT_DRAWING = [
    {
        "type": "POLYLINE",
        "layer": "Walls",
        "points": [[0, 0], [10000, 0], [10000, 8000], [0, 8000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Walls",
        "points": [[3000, 8000], [7000, 8000], [7000, 15000], [3000, 15000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Plot Boundary",
        "points": [[0, 0], [20000, 0], [20000, 20000], [0, 20000]],
        "closed": True
    }
]


def main():
    """Run all test cases."""
    print_separator("🤖 AGENTIC AI SYSTEM TEST SUITE")
    print("This script demonstrates the agentic workflow capabilities.")
    print("Make sure the AI agent service is running on http://localhost:8001")
    
    input("\nPress Enter to start tests...")
    
    # Test 1: Simple compliance check
    test_query(
        question="Is my building extension compliant with regulations?",
        drawing_json=EXAMPLE_DRAWING,
        use_agentic=True,
        description="TEST 1: Simple Compliance Check (Agentic)"
    )
    
    input("\nPress Enter for next test...")
    
    # Test 2: Generate compliant design
    test_query(
        question="My extension is 7m deep but the limit is 6m. Can you provide an adjusted compliant JSON?",
        drawing_json=NON_COMPLIANT_DRAWING,
        use_agentic=True,
        description="TEST 2: Generate Compliant Design (Agentic)"
    )
    
    input("\nPress Enter for next test...")
    
    # Test 3: Calculate dimensions
    test_query(
        question="What are the dimensions of my plot and extension?",
        drawing_json=EXAMPLE_DRAWING,
        use_agentic=True,
        description="TEST 3: Calculate Dimensions (Agentic)"
    )
    
    input("\nPress Enter for next test...")
    
    # Test 4: Complex multi-step query
    test_query(
        question="Analyze my building for all permitted development criteria and tell me what needs to be fixed",
        drawing_json=NON_COMPLIANT_DRAWING,
        use_agentic=True,
        description="TEST 4: Complex Multi-Step Analysis (Agentic)"
    )
    
    input("\nPress Enter for next test...")
    
    # Test 5: Compare with standard mode
    test_query(
        question="What are the extension depth limits?",
        drawing_json=None,
        use_agentic=False,
        description="TEST 5: Simple Question (Standard Mode for Comparison)"
    )
    
    input("\nPress Enter for final test...")
    
    # Test 6: Same question with agentic mode
    test_query(
        question="What are the extension depth limits?",
        drawing_json=None,
        use_agentic=True,
        description="TEST 6: Same Question (Agentic Mode)"
    )
    
    print_separator("✅ ALL TESTS COMPLETED")
    print("Review the reasoning steps to see how the agent autonomously:")
    print("  - Retrieves relevant regulations")
    print("  - Calculates dimensions")
    print("  - Analyzes compliance")
    print("  - Generates solutions")
    print("  - Verifies results")


if __name__ == "__main__":
    main()
