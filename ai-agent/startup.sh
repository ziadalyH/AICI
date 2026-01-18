#!/bin/bash
set -e

echo "=========================================="
echo "AI Agent Startup Script"
echo "=========================================="

# Wait for OpenSearch to be ready
echo "Waiting for OpenSearch to be ready..."
until curl -s http://opensearch:9200/_cluster/health > /dev/null 2>&1; do
    echo "OpenSearch is unavailable - sleeping"
    sleep 2
done
echo "✓ OpenSearch is ready"

# Check if PDFs exist
PDF_DIR="/app/data/pdfs"
PDF_COUNT=$(find "$PDF_DIR" -name "*.pdf" 2>/dev/null | wc -l)

echo "Found $PDF_COUNT PDF file(s) in $PDF_DIR"

# Check for force re-index flag
if [ "$FORCE_REINDEX" = "true" ]; then
    echo "🔄 FORCE_REINDEX=true - Deleting existing index and re-indexing..."
    curl -X DELETE http://opensearch:9200/rag-pdf-index 2>/dev/null || true
    if [ "$PDF_COUNT" -gt 0 ]; then
        python index_pdfs.py
    else
        echo "⚠️  No PDFs found to index"
    fi
else
    # Check if index exists
    INDEX_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" http://opensearch:9200/rag-pdf-index)

    if [ "$INDEX_EXISTS" = "200" ]; then
        echo "✓ Index 'rag-pdf-index' already exists"
        
        # Check document count in index
        DOC_COUNT=$(curl -s http://opensearch:9200/rag-pdf-index/_count 2>/dev/null | grep -o '"count":[0-9]*' | grep -o '[0-9]*' || echo "0")
        echo "  Index contains $DOC_COUNT documents"
        
        if [ "$DOC_COUNT" = "0" ] && [ "$PDF_COUNT" -gt 0 ]; then
            echo "⚠️  Index is empty but PDFs exist. Re-indexing..."
            python index_pdfs.py
        else
            echo "✓ Index is populated, skipping indexing"
        fi
    else
        echo "⚠️  Index 'rag-pdf-index' does not exist"
        
        if [ "$PDF_COUNT" -gt 0 ]; then
            echo "📚 Indexing PDFs..."
            python index_pdfs.py
        else
            echo "⚠️  No PDFs found to index. Please add PDFs to $PDF_DIR"
        fi
    fi
fi

echo "=========================================="
echo "Starting AI Agent Service"
echo "=========================================="

# Start the FastAPI application
exec uvicorn main:app --host 0.0.0.0 --port 8001
