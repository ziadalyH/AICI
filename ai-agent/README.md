# AI Agent Service

Production-ready RAG system with hybrid retrieval combining PDF documents and building drawing JSON for intelligent building regulation queries.

## Features

- **Hybrid RAG Pipeline** - Combines PDF document retrieval with user's building drawing context
- **Agentic Mode** - Multi-step reasoning with autonomous tool use (5 specialized tools)
- **Intelligent Fallback** - 4-tier fallback strategy ensuring users always get meaningful responses
- **OCR Support** - Automatic text extraction from images in PDFs (Tesseract)
- **Semantic Chunking** - Advanced chunking strategy creating 1024-token chunks with 256-token overlap
- **Auto-Indexing** - Automatic PDF indexing on startup

## Quick Start (Docker - Recommended)

The AI Agent is part of the full system. See the main [README](../README.md) for complete setup.

```bash
# From project root
cd AICI
docker-compose up -d ai-agent
```

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export OPENSEARCH_HOST=localhost
export OPENSEARCH_PORT=9200
export OPENAI_API_KEY=your-key-here
export LLM_MODEL=gpt-4o-mini
export EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
export EMBEDDING_DIMENSION=768
```

### 3. Start OpenSearch

```bash
docker run -d \
  --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  -e "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m" \
  opensearchproject/opensearch:latest
```

### 4. Index Your PDFs

```bash
# Place PDFs in data/pdfs/
mkdir -p data/pdfs
cp /path/to/your/pdfs/*.pdf data/pdfs/

# Run indexing
python index_pdfs.py
```

### 5. Start the Service

```bash
python main.py
```

The service will be available at `http://localhost:8001`

## API Endpoints

### Standard Query (Fast)

```bash
POST /api/agent/query
```

Single-shot inference for simple questions.

**Request:**

```json
{
  "question": "What are the height restrictions for residential buildings?",
  "drawing_json": [
    {
      "type": "POLYLINE",
      "layer": "Walls",
      "points": [
        [0, 0],
        [10000, 0],
        [10000, 10000],
        [0, 10000]
      ],
      "closed": true
    },
    {
      "type": "POLYLINE",
      "layer": "Plot Boundary",
      "points": [
        [0, 0],
        [20000, 0],
        [20000, 20000],
        [0, 20000]
      ],
      "closed": true
    }
  ],
  "drawing_updated_at": "2026-01-18T10:30:00Z",
  "session_id": "session_123",
  "top_k": 10
}
```

**Response:**

```json
{
  "answer": "Based on the regulations and your drawing from 18/01/2026, 10:30:00...",
  "answer_type": "pdf",
  "sources": [
    {
      "type": "pdf",
      "document": "building_regulations.pdf",
      "page": 5,
      "paragraph": 2,
      "snippet": "Height restrictions for residential...",
      "relevance": 0.89,
      "title": "Section 3.2",
      "content_type": "text",
      "selected": true
    }
  ],
  "drawing_context_used": true,
  "reasoning_steps": null
}
```

### Agentic Query (Advanced)

```bash
POST /api/agent/query-agentic
```

Multi-step reasoning with autonomous tool use for complex tasks.

**Request:** Same as standard query

**Response:** Same as standard query, but includes `reasoning_steps` array showing all tool calls:

```json
{
  "answer": "...",
  "reasoning_steps": [
    {
      "step": 1,
      "action": "retrieve_regulations",
      "arguments": {"query": "height restrictions", "top_k": 5},
      "result": {"success": true, "count": 5, "regulations": [...]}
    },
    {
      "step": 2,
      "action": "analyze_drawing_compliance",
      "arguments": {"regulations": [...]},
      "result": {"success": true, "violations": [...], "compliant": [...]}
    }
  ]
}
```

### Knowledge Summary

```bash
GET /api/agent/knowledge-summary
```

Returns overview of available topics and suggested questions.

## Configuration

All configuration is done via environment variables.

### Required Settings

- `OPENAI_API_KEY` - Your OpenAI API key (required)

### OpenSearch Settings

- `OPENSEARCH_HOST` - OpenSearch hostname (default: localhost)
- `OPENSEARCH_PORT` - OpenSearch port (default: 9200)
- `OPENSEARCH_PDF_INDEX` - PDF index name (default: rag-pdf-index)
- `OPENSEARCH_USE_SSL` - Use SSL (default: false)
- `OPENSEARCH_VERIFY_CERTS` - Verify certificates (default: false)

### LLM Settings

- `LLM_MODEL` - Model to use (default: gpt-4o-mini)
- `LLM_TEMPERATURE` - Temperature (default: 0.3)
- `LLM_MAX_TOKENS` - Max tokens (default: 500)

### Embedding Settings

- `EMBEDDING_MODEL` - Model name (default: sentence-transformers/all-mpnet-base-v2)
- `EMBEDDING_DIMENSION` - Dimension (default: 768)

### Retrieval Settings

- `RELEVANCE_THRESHOLD` - Minimum relevance score (default: 0.7)
- `MAX_RESULTS` - Max documents to retrieve (default: 5)

### Indexing Settings

- `FORCE_REINDEX` - Force re-index on startup (default: false)

## Project Structure

```
ai-agent/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image definition
├── src/                   # RAG core
│   ├── rag_system.py     # Main orchestrator
│   ├── llm_inference.py  # LLM service
│   ├── models.py         # Data models
│   ├── ingestion/        # PDF/transcript ingestion
│   ├── processing/       # Chunking, embedding, indexing
│   └── retrieval/        # Query processing, retrieval
├── config/               # Configuration
│   └── config.py        # Config management
└── data/                # Data directory
    ├── pdfs/           # Place PDFs here
    └── transcripts/    # Optional video transcripts
```

## Development

### Rebuilding Index

```bash
# Manual re-index
python index_pdfs.py

# Or force re-index on startup
FORCE_REINDEX=true docker-compose restart ai-agent
```

### Checking Index Status

```bash
# Check if index exists
curl http://localhost:9200/rag-pdf-index/_count

# View sample documents
curl http://localhost:9200/rag-pdf-index/_search?size=1

# Check index health
curl http://localhost:9200/_cat/indices?v
```

### Checking OCR Status

```bash
# Run OCR test
docker-compose exec ai-agent python test_ocr.py
```

## Troubleshooting

### "No vector index found"

PDFs are auto-indexed on startup. If index is missing:

```bash
# Check if PDFs exist
ls -la data/pdfs/

# Force re-index
docker-compose exec ai-agent python index_pdfs.py
```

### "OpenSearch connection refused"

Make sure OpenSearch is running:

```bash
curl http://localhost:9200/_cluster/health
```

### "No results found"

- Check if PDFs are indexed: `curl http://localhost:9200/rag-pdf-index/_count`
- Lower `RELEVANCE_THRESHOLD` (default: 0.7)
- Verify PDF content quality
- Check logs for retrieval details

### "LLM API error"

- Check `OPENAI_API_KEY` is set correctly
- Verify API quota/rate limits
- Check model name is correct (gpt-4o-mini)
- Review logs for detailed error messages

### OCR not working

```bash
# Check OCR status
docker-compose logs ai-agent | grep -i ocr

# Should see: "✅ OCR enabled"
# If not, rebuild: docker-compose build --no-cache ai-agent
```

## Architecture

The AI Agent uses a modular architecture:

- **RAG System** (`src/rag_system.py`) - Main orchestrator
- **Agentic System** (`src/agentic_system.py`) - Multi-step reasoning with tools
- **LLM Inference** (`src/llm_inference.py`) - Centralized LLM service
- **Ingestion** (`src/ingestion/`) - PDF parsing with PyMuPDF + OCR
- **Processing** (`src/processing/`) - Chunking, embedding, indexing
- **Retrieval** (`src/retrieval/`) - Query processing, retrieval, response generation

## Key Features Explained

### Semantic Chunking

- Target chunk size: 1024 tokens (~750-800 words)
- Chunk overlap: 256 tokens for context continuity
- Title preservation with content
- Intelligent merging of adjacent blocks

### Fallback

1. **Tier 1**: Full hybrid (PDF + Drawing)
2. **Tier 2**: Drawing-only analysis
3. **Tier 3**: Regulations-only response
4. **Tier 4**: Knowledge summary with suggested questions

### Agentic Tools

1. `retrieve_regulations` - Search regulations
2. `analyze_drawing_compliance` - Check compliance
3. `calculate_drawing_dimensions` - Calculate measurements
4. `generate_compliant_design` - Create compliant version
5. `verify_compliance` - Validate compliance

See main [README](../README.md) for complete documentation.
