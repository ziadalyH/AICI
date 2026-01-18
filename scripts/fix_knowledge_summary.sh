#!/bin/bash
# Diagnostic script for knowledge summary issues

echo "================================"
echo "Knowledge Summary Diagnostic"
echo "================================"
echo ""

# Check if PDFs exist
PDF_COUNT=$(docker exec hybrid-rag-ai-agent find data/pdfs -name "*.pdf" 2>/dev/null | wc -l)

echo "📊 Current Status:"
echo "  PDFs found: $PDF_COUNT"

# Check if index exists
INDEX_EXISTS=$(curl -s http://localhost:9200/rag-pdf-index/_count 2>/dev/null | grep -c "count")

if [ "$INDEX_EXISTS" -eq 0 ]; then
    echo "  OpenSearch index: ❌ Not found"
else
    DOC_COUNT=$(curl -s http://localhost:9200/rag-pdf-index/_count | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])")
    echo "  OpenSearch index: ✅ Found ($DOC_COUNT documents)"
fi

# Check if summary exists
if docker exec hybrid-rag-ai-agent test -f data/knowledge_summary.json; then
    echo "  Knowledge summary: ✅ Exists"
    echo ""
    echo "📄 Current Summary (first 20 lines):"
    docker exec hybrid-rag-ai-agent cat data/knowledge_summary.json | python3 -m json.tool | head -20
else
    echo "  Knowledge summary: ❌ Not found"
fi

echo ""
echo "================================"
echo "Recommended Actions:"
echo "================================"
echo ""

if [ "$PDF_COUNT" -eq 0 ] && [ "$INDEX_EXISTS" -eq 0 ]; then
    echo "⚠️  No PDFs and no index found"
    echo ""
    echo "Option 1: Delete outdated summary (if exists)"
    echo "  docker exec hybrid-rag-ai-agent rm -f data/knowledge_summary.json"
    echo "  docker-compose restart frontend"
    echo ""
    echo "Option 2: Add PDFs and index them (recommended)"
    echo "  # Copy PDFs to container"
    echo "  docker cp /path/to/pdfs/*.pdf hybrid-rag-ai-agent:/app/data/pdfs/"
    echo "  # Index them (will auto-delete old summary and generate new one)"
    echo "  docker exec hybrid-rag-ai-agent python index_pdfs.py"
    echo ""
elif [ "$PDF_COUNT" -gt 0 ] && [ "$INDEX_EXISTS" -eq 0 ]; then
    echo "✅ PDFs found but not indexed"
    echo ""
    echo "Run indexing (will auto-delete old summary and generate new one):"
    echo "  docker exec hybrid-rag-ai-agent python index_pdfs.py"
    echo ""
else
    echo "✅ System is properly configured"
    echo ""
    echo "To regenerate knowledge summary:"
    echo "  docker exec hybrid-rag-ai-agent python index_pdfs.py"
    echo ""
fi

echo "================================"
echo ""
echo "ℹ️  Note: The indexing script now automatically:"
echo "   1. Deletes old knowledge summary at START"
echo "   2. Generates fresh summary at END"
echo "   This ensures summary is always in sync with indexed content"
echo "================================"
