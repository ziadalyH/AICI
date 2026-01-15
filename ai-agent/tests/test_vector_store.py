"""
Tests for the VectorStore class.
"""
import os
import tempfile
import pytest
from app.vector_store import VectorStore


def test_vector_store_initialization():
    """Test that VectorStore initializes correctly."""
    store = VectorStore()
    assert store.index is not None
    assert store.get_index_size() == 0


def test_embed_and_search():
    """Test embedding documents and performing similarity search."""
    store = VectorStore()
    
    # Embed some test documents
    documents = [
        "The cat sat on the mat.",
        "Dogs are great pets.",
        "Python is a programming language."
    ]
    metadata = [
        {"source": "doc1"},
        {"source": "doc2"},
        {"source": "doc3"}
    ]
    
    store.embed_documents(documents, metadata)
    
    # Verify documents were added
    assert store.get_index_size() == 3
    
    # Search for similar documents
    results = store.similarity_search("feline animals", k=2)
    
    # Should return 2 results
    assert len(results) == 2
    
    # Each result should have text, distance, and metadata
    for text, distance, meta in results:
        assert isinstance(text, str)
        assert isinstance(distance, float)
        assert isinstance(meta, dict)


def test_save_and_load_index():
    """Test saving and loading the FAISS index."""
    store1 = VectorStore()
    
    # Embed documents
    documents = ["Test document 1", "Test document 2"]
    store1.embed_documents(documents)
    
    # Save to temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "test_index")
        store1.save_index(index_path)
        
        # Load into new store
        store2 = VectorStore(index_path=index_path)
        
        # Verify loaded correctly
        assert store2.get_index_size() == 2
        
        # Verify search works
        results = store2.similarity_search("Test", k=1)
        assert len(results) == 1


def test_empty_search():
    """Test searching in an empty index."""
    store = VectorStore()
    results = store.similarity_search("test query", k=5)
    assert len(results) == 0


def test_embed_empty_documents():
    """Test embedding an empty list of documents."""
    store = VectorStore()
    store.embed_documents([])
    assert store.get_index_size() == 0
