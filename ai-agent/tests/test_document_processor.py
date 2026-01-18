"""
Tests for the DocumentProcessor class.
"""
import os
import pytest
from app.document_processor import DocumentProcessor


def test_document_processor_initialization():
    """Test that DocumentProcessor initializes with correct parameters."""
    processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
    assert processor.chunk_size == 500
    assert processor.chunk_overlap == 50
    assert processor.tokenizer is not None


def test_chunk_text():
    """Test text chunking functionality."""
    processor = DocumentProcessor(chunk_size=10, chunk_overlap=2)
    
    # Create a text that will be split into multiple chunks
    text = "This is a test document. " * 20
    
    chunks = processor.chunk_text(text, source_document="test.txt")
        
    # Should have multiple chunks
    assert len(chunks) > 1
    
    # Each chunk should have text and metadata
    for chunk in chunks:
        assert 'text' in chunk
        assert 'metadata' in chunk
        assert chunk['metadata']['source'] == "test.txt"
        assert 'start_token' in chunk['metadata']
        assert 'end_token' in chunk['metadata']


def test_load_pdf():
    """Test loading a PDF file."""
    processor = DocumentProcessor()
    
    # Use the actual PDF from the workspace
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    pdf_path = os.path.join(workspace_root, '240213 Permitted Development Rights.pdf')
    
    if os.path.exists(pdf_path):
        text = processor.load_pdf(pdf_path)
        
        # Should have extracted some text
        assert len(text) > 0
        assert isinstance(text, str)
    else:
        pytest.skip("PDF file not found in workspace")


def test_process_pdf():
    """Test processing a PDF file into chunks."""
    processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
    
    # Use the actual PDF from the workspace
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    pdf_path = os.path.join(workspace_root, '240213 Permitted Development Rights.pdf')
    
    if os.path.exists(pdf_path):
        chunks = processor.process_pdf(pdf_path)
        
        # Should have generated chunks
        assert len(chunks) > 0
        
        # Each chunk should have the correct structure
        for chunk in chunks:
            assert 'text' in chunk
            assert 'metadata' in chunk
            assert chunk['metadata']['source'] == '240213 Permitted Development Rights.pdf'
    else:
        pytest.skip("PDF file not found in workspace")


def test_load_nonexistent_pdf():
    """Test that loading a non-existent PDF raises an error."""
    processor = DocumentProcessor()
    
    with pytest.raises(FileNotFoundError):
        processor.load_pdf("nonexistent_file.pdf")


def test_chunk_text_with_overlap():
    """Test that chunks have proper overlap."""
    processor = DocumentProcessor(chunk_size=20, chunk_overlap=5)
    
    text = "word " * 100  # Create a long text
    chunks = processor.chunk_text(text)
    
    # Should have multiple chunks
    assert len(chunks) > 1
    
    # Verify overlap exists (end of one chunk should relate to start of next)
    for i in range(len(chunks) - 1):
        current_end = chunks[i]['metadata']['end_token']
        next_start = chunks[i + 1]['metadata']['start_token']
        
        # The overlap should be approximately chunk_overlap tokens
        overlap = current_end - next_start
        assert overlap >= 0  # There should be some overlap
