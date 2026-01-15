"""
Integration tests for the Hybrid RAG Pipeline.
Tests the interaction between PromptBuilder, VectorStore, and HybridRAGPipeline.
"""
import pytest
from app.prompt_builder import PromptBuilder
from app.vector_store import VectorStore
from app.rag_pipeline import HybridRAGPipeline


class TestPromptBuilder:
    """Test the PromptBuilder module."""
    
    def test_prompt_builder_initialization(self):
        """Test that PromptBuilder initializes correctly."""
        pb = PromptBuilder()
        assert pb.system_prompt is not None
        assert len(pb.system_prompt) > 0
    
    def test_format_embeddings_empty(self):
        """Test formatting empty embeddings list."""
        pb = PromptBuilder()
        result = pb.format_embeddings([])
        assert "No relevant documents found" in result
    
    def test_format_embeddings_with_data(self):
        """Test formatting embeddings with actual data."""
        pb = PromptBuilder()
        embeddings = ["Document 1 content", "Document 2 content"]
        result = pb.format_embeddings(embeddings)
        assert "RETRIEVED DOCUMENTS" in result
        assert "Document 1 content" in result
        assert "Document 2 content" in result
    
    def test_format_objects_empty(self):
        """Test formatting empty objects list."""
        pb = PromptBuilder()
        result = pb.format_objects([])
        assert "No ephemeral objects provided" in result
    
    def test_format_objects_with_data(self):
        """Test formatting objects with actual data."""
        pb = PromptBuilder()
        objects = [{"id": "obj_1", "type": "test", "value": 42}]
        result = pb.format_objects(objects)
        assert "EPHEMERAL OBJECTS" in result
        assert "obj_1" in result
        assert "test" in result
    
    def test_build_prompt_complete(self):
        """Test building a complete prompt with all components."""
        pb = PromptBuilder()
        query = "What is the answer?"
        embeddings = ["Relevant document text"]
        objects = [{"id": "obj_1", "data": "test"}]
        
        prompt = pb.build_prompt(query, embeddings, objects)
        
        # Verify all components are present
        assert pb.system_prompt in prompt
        assert query in prompt
        assert "Relevant document text" in prompt
        assert "obj_1" in prompt
        assert "USER QUESTION" in prompt
    
    def test_build_prompt_with_metadata(self):
        """Test building prompt with metadata."""
        pb = PromptBuilder()
        query = "Test query"
        embeddings = ["Doc 1", "Doc 2"]
        objects = [{"id": "1"}, {"id": "2"}]
        
        result = pb.build_prompt_with_metadata(query, embeddings, objects)
        
        assert 'prompt' in result
        assert 'metadata' in result
        assert result['metadata']['num_embeddings'] == 2
        assert result['metadata']['num_objects'] == 2


class TestHybridRAGPipelineWithoutLLM:
    """Test HybridRAGPipeline without requiring LLM API."""
    
    def test_retrieve_embeddings(self):
        """Test retrieving embeddings from vector store."""
        # Create a vector store with test data
        vector_store = VectorStore()
        test_docs = [
            "This is a document about Python programming.",
            "This document discusses machine learning.",
            "This is about web development with React."
        ]
        vector_store.embed_documents(test_docs)
        
        # Create a mock LLM client (we won't call it)
        class MockLLMClient:
            def generate_response(self, prompt):
                return "Mock response"
        
        llm_client = MockLLMClient()
        
        # Create pipeline
        pipeline = HybridRAGPipeline(vector_store, llm_client, top_k=2)
        
        # Test retrieval
        query = "Tell me about Python"
        embeddings = pipeline.retrieve_embeddings(query)
        
        assert len(embeddings) <= 2
        assert all(isinstance(emb, str) for emb in embeddings)
    
    def test_retrieve_embeddings_with_metadata(self):
        """Test retrieving embeddings with metadata."""
        vector_store = VectorStore()
        test_docs = ["Document 1", "Document 2"]
        test_metadata = [{"source": "doc1.pdf"}, {"source": "doc2.pdf"}]
        vector_store.embed_documents(test_docs, test_metadata)
        
        class MockLLMClient:
            def generate_response(self, prompt):
                return "Mock response"
        
        llm_client = MockLLMClient()
        pipeline = HybridRAGPipeline(vector_store, llm_client)
        
        embeddings, metadata = pipeline.retrieve_embeddings_with_metadata("test query")
        
        assert len(embeddings) == len(metadata)
        assert all('distance' in m for m in metadata)
    
    def test_build_prompt_through_pipeline(self):
        """Test building prompt through the pipeline."""
        vector_store = VectorStore()
        
        class MockLLMClient:
            def generate_response(self, prompt):
                return "Mock response"
        
        llm_client = MockLLMClient()
        pipeline = HybridRAGPipeline(vector_store, llm_client)
        
        query = "What is this?"
        embeddings = ["Retrieved text"]
        objects = [{"id": "obj_1"}]
        
        prompt = pipeline.build_prompt(query, embeddings, objects)
        
        assert query in prompt
        assert "Retrieved text" in prompt
        assert "obj_1" in prompt
    
    def test_generate_answer_with_mock(self):
        """Test answer generation with mock LLM."""
        vector_store = VectorStore()
        
        class MockLLMClient:
            def generate_response(self, prompt):
                return "This is a mock answer"
        
        llm_client = MockLLMClient()
        pipeline = HybridRAGPipeline(vector_store, llm_client)
        
        prompt = "Test prompt"
        answer = pipeline.generate_answer(prompt)
        
        assert answer == "This is a mock answer"
    
    def test_process_query_end_to_end_mock(self):
        """Test complete query processing with mock LLM."""
        # Set up vector store with test data
        vector_store = VectorStore()
        test_docs = ["Python is a programming language.", "React is a JavaScript library."]
        vector_store.embed_documents(test_docs)
        
        # Mock LLM client
        class MockLLMClient:
            def generate_response(self, prompt):
                return "Mock answer based on the prompt"
        
        llm_client = MockLLMClient()
        pipeline = HybridRAGPipeline(vector_store, llm_client, top_k=1)
        
        # Process query
        query = "What is Python?"
        objects = [{"id": "obj_1", "type": "test"}]
        answer = pipeline.process_query(query, objects)
        
        assert answer == "Mock answer based on the prompt"
    
    def test_set_top_k(self):
        """Test updating top_k parameter."""
        vector_store = VectorStore()
        
        class MockLLMClient:
            def generate_response(self, prompt):
                return "Mock"
        
        llm_client = MockLLMClient()
        pipeline = HybridRAGPipeline(vector_store, llm_client, top_k=5)
        
        assert pipeline.top_k == 5
        
        pipeline.set_top_k(10)
        assert pipeline.top_k == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
