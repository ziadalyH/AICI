"""
Test script for conversational memory feature.

This script tests the conversation history functionality by:
1. Asking an initial question
2. Asking follow-up questions that reference previous context
3. Verifying that the system maintains conversation history
"""
import requests
import json
from typing import Dict, Any

# Configuration
AI_AGENT_URL = "http://localhost:8001"
SESSION_ID = "test_session_123"

# Test drawing JSON
DRAWING_JSON = [
    {
        "type": "POLYLINE",
        "layer": "Walls",
        "points": [[0, 0], [10000, 0], [10000, 8000], [0, 8000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Plot Boundary",
        "points": [[0, 0], [20000, 0], [20000, 20000], [0, 20000]],
        "closed": True
    }
]


def query_agent(question: str, drawing_json: list = None, session_id: str = None) -> Dict[str, Any]:
    """Send a query to the AI agent."""
    payload = {
        "question": question,
        "drawing_json": drawing_json or [],
        "top_k": 5
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    print(f"\n{'='*80}")
    print(f"QUESTION: {question}")
    print(f"Session ID: {session_id or 'None'}")
    print(f"{'='*80}")
    
    response = requests.post(
        f"{AI_AGENT_URL}/api/agent/query",
        json=payload,
        timeout=30
    )
    
    response.raise_for_status()
    result = response.json()
    
    print(f"\nANSWER: {result['answer']}")
    print(f"Answer Type: {result['answer_type']}")
    
    if result.get('sources'):
        print(f"\nSOURCES ({len(result['sources'])} total):")
        for i, source in enumerate(result['sources'], 1):
            selected = "✓ SELECTED" if source.get('selected') else ""
            print(f"  {i}. {source['document']} (Page {source['page']}) {selected}")
    
    return result


def get_session_info(session_id: str) -> Dict[str, Any]:
    """Get session information."""
    response = requests.get(
        f"{AI_AGENT_URL}/api/agent/session-info/{session_id}",
        timeout=5
    )
    response.raise_for_status()
    return response.json()


def clear_history(session_id: str) -> Dict[str, Any]:
    """Clear conversation history."""
    response = requests.post(
        f"{AI_AGENT_URL}/api/agent/clear-history",
        params={"session_id": session_id},
        timeout=5
    )
    response.raise_for_status()
    return response.json()


def main():
    """Run conversation tests."""
    print("\n" + "="*80)
    print("CONVERSATIONAL MEMORY TEST")
    print("="*80)
    
    # Test 1: Initial question without session (no history)
    print("\n\n### TEST 1: Question without session ID (no history)")
    query_agent(
        question="What are the height restrictions for buildings?",
        drawing_json=DRAWING_JSON
    )
    
    # Test 2: Initial question with session (start conversation)
    print("\n\n### TEST 2: Initial question with session ID (start conversation)")
    query_agent(
        question="What are the height restrictions for buildings?",
        drawing_json=DRAWING_JSON,
        session_id=SESSION_ID
    )
    
    # Check session info
    info = get_session_info(SESSION_ID)
    print(f"\nSession Info: {info['exchange_count']} exchanges, {info['message_count']} messages")
    
    # Test 3: Follow-up question (should use history)
    print("\n\n### TEST 3: Follow-up question (should reference previous context)")
    query_agent(
        question="What about for residential zones?",
        drawing_json=DRAWING_JSON,
        session_id=SESSION_ID
    )
    
    # Check session info
    info = get_session_info(SESSION_ID)
    print(f"\nSession Info: {info['exchange_count']} exchanges, {info['message_count']} messages")
    
    # Test 4: Another follow-up with pronoun reference
    print("\n\n### TEST 4: Follow-up with pronoun reference")
    query_agent(
        question="Is that the same for extensions?",
        drawing_json=DRAWING_JSON,
        session_id=SESSION_ID
    )
    
    # Check session info
    info = get_session_info(SESSION_ID)
    print(f"\nSession Info: {info['exchange_count']} exchanges, {info['message_count']} messages")
    
    # Test 5: Drawing-specific follow-up
    print("\n\n### TEST 5: Drawing-specific follow-up")
    query_agent(
        question="How many walls are in my drawing?",
        drawing_json=DRAWING_JSON,
        session_id=SESSION_ID
    )
    
    # Check session info
    info = get_session_info(SESSION_ID)
    print(f"\nSession Info: {info['exchange_count']} exchanges, {info['message_count']} messages")
    
    # Test 6: Clear history
    print("\n\n### TEST 6: Clear conversation history")
    result = clear_history(SESSION_ID)
    print(f"Clear result: {result}")
    
    # Check session info after clear
    info = get_session_info(SESSION_ID)
    print(f"Session Info after clear: {info['exchange_count']} exchanges, {info['message_count']} messages")
    
    # Test 7: Question after clearing (should not have history)
    print("\n\n### TEST 7: Question after clearing history (no context)")
    query_agent(
        question="What about that?",  # This should fail without context
        drawing_json=DRAWING_JSON,
        session_id=SESSION_ID
    )
    
    print("\n\n" + "="*80)
    print("TESTS COMPLETED")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
