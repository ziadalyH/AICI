# Knowledge Summary Logic

## Overview

The knowledge summary is automatically managed during the indexing process to ensure it's always in sync with the indexed content.

## Automatic Management

### During Indexing (`index_pdfs.py`)

The indexing process now follows this workflow:

```
1. START INDEXING
   ↓
2. DELETE old knowledge_summary.json (if exists)
   ↓
3. Index PDFs (new or existing)
   ↓
4. GENERATE fresh knowledge_summary.json
   ↓
5. END INDEXING
```

### Key Benefits

1. **Always Fresh**: Summary is regenerated every time you index
2. **No Stale Data**: Old summary is deleted before indexing starts
3. **Automatic Sync**: Summary always reflects current indexed content
4. **No Manual Cleanup**: No need to manually delete old summaries

## Implementation Details

### Code Changes

**File**: `AICI/ai-agent/src/rag_system.py`

**Method**: `build_index()`

```python
def build_index(self, force_rebuild: bool = False) -> None:
    # STEP 0: Delete old knowledge summary
    summary_file = Path("data/knowledge_summary.json")
    if summary_file.exists():
        summary_file.unlink()
        logger.info("✓ Old knowledge summary deleted")

    # ... indexing logic ...

    # FINAL STEP: Generate fresh knowledge summary
    self.knowledge_summary_generator.generate_summary(
        pdf_files=list(final_indexed_pdfs),
        video_ids=[],
        sample_chunks=sample_chunks
    )
    logger.info("✓ Fresh knowledge summary generated successfully")
```

## Usage

### Indexing PDFs

```bash
# Run indexing (auto-deletes old summary, generates new one)
docker exec hybrid-rag-ai-agent python index_pdfs.py
```

### What Happens

1. **Before indexing**: Old `data/knowledge_summary.json` is deleted
2. **During indexing**: PDFs are processed and indexed
3. **After indexing**: Fresh summary is generated from indexed content

### No PDFs Scenario

If you run indexing but all PDFs are already indexed:

1. Old summary is still deleted
2. No new indexing happens (resume capability)
3. Fresh summary is generated from existing index

This ensures the summary is always regenerated, even if no new content is indexed.

## Frontend Behavior

### On Login

The frontend loads the knowledge summary from `/api/agent/knowledge-summary`:

- **Summary exists**: Shows overview, topics, and suggested questions
- **Summary missing**: Shows fallback message "Start a conversation..."

### When LLM Refuses to Answer

If the LLM can't answer a question, the knowledge summary is shown:

- Green-themed expandable section
- Overview of available knowledge
- Topics covered
- Clickable suggested questions

## Troubleshooting

### Outdated Summary

**Problem**: Summary references content that's not indexed

**Solution**: Run indexing to regenerate

```bash
docker exec hybrid-rag-ai-agent python index_pdfs.py
```

### Missing Summary

**Problem**: No summary file exists

**Causes**:

1. Never ran indexing
2. No PDFs in system
3. LLM API key not configured

**Solution**:

```bash
# Add PDFs
docker cp /path/to/pdfs/*.pdf hybrid-rag-ai-agent:/app/data/pdfs/

# Run indexing
docker exec hybrid-rag-ai-agent python index_pdfs.py
```

### Summary Not Updating in Frontend

**Problem**: Frontend shows old summary after reindexing

**Solution**: Restart frontend to reload

```bash
docker-compose restart frontend
```

Or hard refresh browser (Cmd+Shift+R / Ctrl+Shift+F5)

## Files Involved

- `AICI/ai-agent/src/rag_system.py` - Main indexing logic
- `AICI/ai-agent/config/knowledge_summary.py` - Summary generator
- `AICI/ai-agent/index_pdfs.py` - Indexing script
- `AICI/ai-agent/data/knowledge_summary.json` - Generated summary file
- `AICI/ai-agent/main.py` - API endpoint for summary
- `AICI/frontend/src/components/ChatInterface.tsx` - Frontend loader

## Best Practices

1. **Always reindex after adding/removing PDFs** to keep summary in sync
2. **Don't manually edit** `knowledge_summary.json` - it will be overwritten
3. **Check logs** during indexing to see summary generation status
4. **Ensure LLM API key** is configured for summary generation

## Migration from Old Behavior

### Old Behavior (Before Fix)

- Summary persisted across rebuilds
- Could become outdated
- Required manual deletion

### New Behavior (After Fix)

- Summary auto-deleted before indexing
- Always fresh and in sync
- No manual intervention needed

### Migration Steps

If you have an old system:

1. Run indexing once: `docker exec hybrid-rag-ai-agent python index_pdfs.py`
2. Old summary will be auto-deleted
3. Fresh summary will be generated
4. Done! Future indexing will follow new logic
