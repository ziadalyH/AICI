# Quick Fix Guide - Knowledge Summary

## What Changed?

The knowledge summary now **automatically deletes and regenerates** every time you run indexing.

## How to Use

### Option 1: You Have PDFs to Index

```bash
# Copy PDFs to container
docker cp /path/to/your/pdfs/*.pdf hybrid-rag-ai-agent:/app/data/pdfs/

# Run indexing (auto-deletes old summary, generates new one)
docker exec hybrid-rag-ai-agent python index_pdfs.py

# Restart frontend to see new summary
docker-compose restart frontend
```

### Option 2: You Don't Have PDFs Yet

```bash
# Just delete the outdated summary
docker exec hybrid-rag-ai-agent rm -f data/knowledge_summary.json

# Restart frontend
docker-compose restart frontend
```

The frontend will show a fallback message instead of outdated questions.

## What Happens During Indexing?

```
1. 🗑️  Delete old knowledge_summary.json
2. 📚 Index PDFs (new or existing)
3. ✨ Generate fresh knowledge_summary.json
```

## Verify It Works

```bash
# Check current summary
docker exec hybrid-rag-ai-agent cat data/knowledge_summary.json | head -20

# Run indexing
docker exec hybrid-rag-ai-agent python index_pdfs.py

# Check new summary (should be different)
docker exec hybrid-rag-ai-agent cat data/knowledge_summary.json | head -20
```

## Diagnostic Script

Run this to check your system status:

```bash
bash AICI/scripts/fix_knowledge_summary.sh
```

It will show:

- How many PDFs are in the system
- If OpenSearch index exists
- If knowledge summary exists
- Recommended actions

## No More Manual Cleanup!

You never need to manually delete `knowledge_summary.json` anymore. Just run indexing and it handles everything automatically.

## Questions?

See full documentation: `AICI/KNOWLEDGE_SUMMARY_LOGIC.md`
