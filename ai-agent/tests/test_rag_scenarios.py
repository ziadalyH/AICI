"""
Comprehensive RAG System Tests - All Scenarios

Tests cover:
1. Pure Retrieval (PDF only)
2. Pure JSON Reasoning (Drawing only)
3. Hybrid RAG (PDF + JSON)
4. Session Updates (Drawing changes)
5. Boundary & Edge Cases
6. Explainability
7. Negative/Out-of-Scope
8. Instruction Following
9. Agentic/Planning (Advanced)
"""

import pytest
import json
from typing import Dict, Any, List


# ============================================================================
# TEST DATA - Sample Drawing JSON
# ============================================================================

SAMPLE_DRAWING_COMPLIANT = [
    {
        "type": "POLYLINE",
        "layer": "Plot Boundary",
        "points": [[-12000, 10000], [12000, 10000], [12000, 42000], [-12000, 42000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Walls",
        "points": [[-6000, 16000], [6000, 16000], [6000, 32000], [-6000, 32000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Extension",
        "points": [[-4000, 32000], [4000, 32000], [4000, 37000], [-4000, 37000]],  # 5m extension - COMPLIANT
        "closed": True
    }
]

SAMPLE_DRAWING_NON_COMPLIANT = [
    {
        "type": "POLYLINE",
        "layer": "Plot Boundary",
        "points": [[-12000, 10000], [12000, 10000], [12000, 42000], [-12000, 42000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Walls",
        "points": [[-6000, 16000], [6000, 16000], [6000, 32000], [-6000, 32000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Extension",
        "points": [[-4000, 32000], [4000, 32000], [4000, 39000], [-4000, 39000]],  # 7m extension - NON-COMPLIANT
        "closed": True
    }
]

SAMPLE_DRAWING_EDGE_CASE = [
    {
        "type": "POLYLINE",
        "layer": "Plot Boundary",
        "points": [[-12000, 10000], [12000, 10000], [12000, 42000], [-12000, 42000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Walls",
        "points": [[-6000, 16000], [6000, 16000], [6000, 32000], [-6000, 32000]],
        "closed": True
    },
    {
        "type": "POLYLINE",
        "layer": "Extension",
        "points": [[-4000, 32000], [4000, 32000], [4000, 38010], [-4000, 38010]],  # 6.01m extension - EDGE CASE
        "closed": True
    }
]


# ============================================================================
# 1️⃣ PURE RETRIEVAL QUESTIONS (PDF ONLY)
# ============================================================================

class TestPureRetrieval:
    """Test document retrieval and grounding without drawing context."""
    
    @pytest.mark.asyncio
    async def test_permitted_development_rules(self, rag_client):
        """Test: What are the permitted development rules for rear extensions?"""
        response = await rag_client.query(
            question="What are the permitted development rules for rear extensions?",
            objects=None,  # No drawing
            top_k=5
        )
        
        # Assertions
        assert response["answer_type"] == "pdf"
        assert "extension" in response["answer"].lower()
        assert "permitted development" in response["answer"].lower()
        assert response["sources"] is not None
        assert len(response["sources"]) > 0
        assert response["drawing_context_used"] is False
        
        # Should NOT mention drawing timestamp
        assert "based on the updated drawing" not in response["answer"].lower()
    
    @pytest.mark.asyncio
    async def test_maximum_extension_depth(self, rag_client):
        """Test: What is the maximum allowed extension depth?"""
        response = await rag_client.query(
            question="What is the maximum allowed extension depth?",
            objects=None,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        assert any(char.isdigit() for char in response["answer"])  # Should contain numbers
        assert "m" in response["answer"] or "metre" in response["answer"].lower()
        assert response["drawing_context_used"] is False
    
    @pytest.mark.asyncio
    async def test_definition_principal_elevation(self, rag_client):
        """Test: Define 'principal elevation' according to the regulations."""
        response = await rag_client.query(
            question="Define 'principal elevation' according to the regulations.",
            objects=None,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        assert "elevation" in response["answer"].lower()
        assert response["sources"] is not None


# ============================================================================
# 2️⃣ PURE JSON REASONING QUESTIONS (DRAWING ONLY)
# ============================================================================

class TestPureJSONReasoning:
    """Test geometry parsing and calculations from drawing JSON only."""
    
    @pytest.mark.asyncio
    async def test_total_plot_area(self, rag_client):
        """Test: What is the total plot area?"""
        response = await rag_client.query(
            question="What is the total plot area?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        # Assertions
        assert response["answer_type"] in ["pdf", "drawing"]
        assert "768" in response["answer"] or "24" in response["answer"]  # 24m x 32m = 768m²
        assert "m²" in response["answer"] or "square" in response["answer"].lower()
        
        # MUST mention drawing timestamp
        assert "based on the updated drawing" in response["answer"].lower()
    
    @pytest.mark.asyncio
    async def test_count_wall_elements(self, rag_client):
        """Test: How many wall elements are in the drawing?"""
        response = await rag_client.query(
            question="How many wall elements are in the drawing?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] in ["pdf", "drawing"]
        # Should identify walls and extension (2 wall-related elements)
        assert any(num in response["answer"] for num in ["2", "3", "two", "three"])
    
    @pytest.mark.asyncio
    async def test_extension_depth(self, rag_client):
        """Test: What is the depth of the rear extension?"""
        response = await rag_client.query(
            question="What is the depth of the rear extension?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] in ["pdf", "drawing"]
        assert "5" in response["answer"]  # 5m extension
        assert "m" in response["answer"]


# ============================================================================
# 3️⃣ HYBRID RAG QUESTIONS (PDF + JSON)
# ============================================================================

class TestHybridRAG:
    """Test true hybrid reasoning combining PDF regulations and drawing data."""
    
    @pytest.mark.asyncio
    async def test_building_compliance(self, rag_client):
        """Test: Does the building comply with permitted development rules?"""
        response = await rag_client.query(
            question="Does the building comply with permitted development rules?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        # Assertions
        assert response["answer_type"] == "pdf"
        assert response["drawing_context_used"] is True
        
        # Should provide structured answer with ✅/⚠️/ℹ️
        answer_lower = response["answer"].lower()
        assert "compliant" in answer_lower or "comply" in answer_lower
        
        # Should mention drawing timestamp
        assert "based on" in answer_lower
        
        # Should reference specific rules
        assert any(word in answer_lower for word in ["extension", "depth", "height", "rule"])
    
    @pytest.mark.asyncio
    async def test_extension_length_check(self, rag_client):
        """Test: Is the rear extension longer than allowed?"""
        # Test with NON-COMPLIANT drawing (7m extension)
        response = await rag_client.query(
            question="Is the rear extension longer than allowed?",
            objects=SAMPLE_DRAWING_NON_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        assert "7" in response["answer"]  # Should mention 7m
        assert "6" in response["answer"]  # Should mention 6m limit
        
        # Should indicate non-compliance
        answer_lower = response["answer"].lower()
        assert any(word in answer_lower for word in ["exceed", "longer", "non-compliant", "not compliant"])
    
    @pytest.mark.asyncio
    async def test_plot_coverage(self, rag_client):
        """Test: Does the building exceed the maximum plot coverage?"""
        response = await rag_client.query(
            question="Does the building exceed the maximum plot coverage?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        assert response["drawing_context_used"] is True
        # Should calculate coverage percentage
        assert "%" in response["answer"] or "percent" in response["answer"].lower()


# ============================================================================
# 4️⃣ SESSION UPDATE / EPHEMERAL STATE QUESTIONS
# ============================================================================

class TestSessionUpdates:
    """Test that updated drawings are correctly used."""
    
    @pytest.mark.asyncio
    async def test_drawing_update_detection(self, rag_client):
        """Test: Drawing updates are reflected in answers."""
        
        # First query with NON-COMPLIANT drawing
        response1 = await rag_client.query(
            question="Is the rear extension compliant?",
            objects=SAMPLE_DRAWING_NON_COMPLIANT,
            drawing_updated_at="2026-01-17T15:00:00.000Z",
            top_k=5
        )
        
        # Second query with COMPLIANT drawing (simulating update)
        response2 = await rag_client.query(
            question="Is the rear extension compliant now?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            drawing_updated_at="2026-01-17T15:30:00.000Z",
            top_k=5
        )
        
        # Assertions
        assert response1["answer_type"] == "pdf"
        assert response2["answer_type"] == "pdf"
        
        # Answers should be different
        assert response1["answer"] != response2["answer"]
        
        # First should indicate non-compliance
        assert any(word in response1["answer"].lower() for word in ["exceed", "non-compliant", "not compliant"])
        
        # Second should indicate compliance or improvement
        assert any(word in response2["answer"].lower() for word in ["compliant", "within", "meets"])


# ============================================================================
# 5️⃣ BOUNDARY & EDGE CASE QUESTIONS
# ============================================================================

class TestBoundaryEdgeCases:
    """Test numerical precision and strict limits."""
    
    @pytest.mark.asyncio
    async def test_edge_case_6_01m(self, rag_client):
        """Test: If the extension is 6.01m deep, is it compliant?"""
        response = await rag_client.query(
            question="If the extension is 6.01m deep, is it compliant?",
            objects=SAMPLE_DRAWING_EDGE_CASE,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        assert "6.01" in response["answer"] or "6" in response["answer"]
        
        # Should indicate non-compliance (exceeds 6m limit)
        answer_lower = response["answer"].lower()
        assert any(word in answer_lower for word in ["exceed", "over", "non-compliant", "not compliant"])
    
    @pytest.mark.asyncio
    async def test_boundary_wall_placement(self, rag_client):
        """Test: Is a wall exactly on the plot boundary allowed?"""
        response = await rag_client.query(
            question="Is a wall exactly on the plot boundary allowed?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        assert "boundary" in response["answer"].lower()


# ============================================================================
# 6️⃣ EXPLAINABILITY QUESTIONS
# ============================================================================

class TestExplainability:
    """Test justification and grounding."""
    
    @pytest.mark.asyncio
    async def test_why_non_compliant(self, rag_client):
        """Test: Why is the building non-compliant?"""
        response = await rag_client.query(
            question="Why is the building non-compliant?",
            objects=SAMPLE_DRAWING_NON_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        
        # Should provide specific reasons
        answer_lower = response["answer"].lower()
        assert any(word in answer_lower for word in ["because", "exceed", "rule", "limit", "regulation"])
        
        # Should cite specific measurements
        assert any(char.isdigit() for char in response["answer"])
    
    @pytest.mark.asyncio
    async def test_which_rule_violated(self, rag_client):
        """Test: Which rule does the rear extension violate?"""
        response = await rag_client.query(
            question="Which rule does the rear extension violate?",
            objects=SAMPLE_DRAWING_NON_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        assert "rule" in response["answer"].lower() or "regulation" in response["answer"].lower()
        assert "extension" in response["answer"].lower()
    
    @pytest.mark.asyncio
    async def test_calculation_explanation(self, rag_client):
        """Test: How was the extension depth calculated?"""
        response = await rag_client.query(
            question="How was the extension depth calculated?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] in ["pdf", "drawing"]
        # Should explain calculation method
        answer_lower = response["answer"].lower()
        assert any(word in answer_lower for word in ["calculate", "measure", "distance", "coordinate"])


# ============================================================================
# 7️⃣ NEGATIVE / OUT-OF-SCOPE QUESTIONS
# ============================================================================

class TestNegativeOutOfScope:
    """Test hallucination resistance."""
    
    @pytest.mark.asyncio
    async def test_fire_safety_out_of_scope(self, rag_client):
        """Test: What fire safety regulations apply here?"""
        response = await rag_client.query(
            question="What fire safety regulations apply here?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        # Should either:
        # 1. Return no_answer
        # 2. Clearly state it's out of scope
        # 3. Only mention what's in the documents (if fire safety is mentioned)
        
        if response["answer_type"] == "no_answer":
            assert True  # Correct behavior
        else:
            answer_lower = response["answer"].lower()
            # Should not hallucinate specific fire safety rules
            assert "cannot" in answer_lower or "not" in answer_lower or "don't" in answer_lower
    
    @pytest.mark.asyncio
    async def test_swimming_pool_out_of_scope(self, rag_client):
        """Test: Is a swimming pool allowed on this plot?"""
        response = await rag_client.query(
            question="Is a swimming pool allowed on this plot?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        # Should not hallucinate swimming pool regulations
        if response["answer_type"] != "no_answer":
            answer_lower = response["answer"].lower()
            # Should indicate uncertainty or lack of information
            assert any(word in answer_lower for word in ["cannot", "don't", "not", "unclear", "information"])


# ============================================================================
# 8️⃣ INSTRUCTION-FOLLOWING QUESTIONS
# ============================================================================

class TestInstructionFollowing:
    """Test prompt obedience."""
    
    @pytest.mark.asyncio
    async def test_ignore_drawing_use_document_only(self, rag_client):
        """Test: Ignore the drawing and answer using the document only."""
        response = await rag_client.query(
            question="Ignore the drawing and answer using the document only: What is the maximum extension depth?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        # Should NOT mention specific measurements from the drawing
        # Should mention general rule (6m for terraced houses)
        assert "6" in response["answer"]
    
    @pytest.mark.asyncio
    async def test_ignore_document_analyze_drawing_only(self, rag_client):
        """Test: Ignore the document and analyze the drawing only."""
        response = await rag_client.query(
            question="Ignore the document and analyze the drawing only: What is the extension depth?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        # Should analyze drawing
        assert "5" in response["answer"]  # 5m extension in sample drawing
        assert "m" in response["answer"]


# ============================================================================
# 9️⃣ AGENTIC / PLANNING QUESTIONS (ADVANCED)
# ============================================================================

class TestAgenticPlanning:
    """Test higher-level reasoning and synthesis."""
    
    @pytest.mark.asyncio
    async def test_suggest_compliance_changes(self, rag_client):
        """Test: What changes would make this design compliant?"""
        response = await rag_client.query(
            question="What changes would make this design compliant?",
            objects=SAMPLE_DRAWING_NON_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        
        # Should provide actionable suggestions
        answer_lower = response["answer"].lower()
        assert any(word in answer_lower for word in ["reduce", "change", "modify", "adjust", "shorten"])
        
        # Should mention specific measurements
        assert any(char.isdigit() for char in response["answer"])
    
    @pytest.mark.asyncio
    async def test_pre_submission_checks(self, rag_client):
        """Test: What checks should be done before submitting this plan?"""
        response = await rag_client.query(
            question="What checks should be done before submitting this plan?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        
        # Should list multiple checks
        answer_lower = response["answer"].lower()
        assert any(word in answer_lower for word in ["check", "verify", "ensure", "confirm"])
    
    @pytest.mark.asyncio
    async def test_maximum_legal_extension(self, rag_client):
        """Test: What is the maximum legal extension possible?"""
        response = await rag_client.query(
            question="What is the maximum legal extension possible?",
            objects=SAMPLE_DRAWING_COMPLIANT,
            top_k=5
        )
        
        assert response["answer_type"] == "pdf"
        
        # Should provide specific measurements
        assert any(char.isdigit() for char in response["answer"])
        assert "m" in response["answer"]
        
        # Should reference regulations
        answer_lower = response["answer"].lower()
        assert any(word in answer_lower for word in ["permitted", "allowed", "maximum", "limit"])


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture
async def rag_client():
    """Fixture to provide RAG client for testing."""
    import httpx
    
    class RAGClient:
        def __init__(self):
            self.base_url = "http://localhost:8001"
            self.client = httpx.AsyncClient(timeout=60.0)
        
        async def query(
            self,
            question: str,
            objects: List[Dict] = None,
            drawing_updated_at: str = None,
            top_k: int = 5
        ) -> Dict[str, Any]:
            """Send query to RAG system."""
            payload = {
                "question": question,
                "drawing_json": objects,
                "drawing_updated_at": drawing_updated_at,
                "top_k": top_k
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/agent/query",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        
        async def close(self):
            await self.client.aclose()
    
    client = RAGClient()
    yield client
    await client.close()


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
