# Hybrid RAG AI Agent

Production-ready RAG system enhanced with drawing JSON integration for building regulation queries.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Copy `.env.example` or set these variables:

```bash
export OPENSEARCH_HOST=localhost
export OPENSEARCH_PORT=9200
export OPENAI_API_KEY=your-key-here
export LLM_MODEL=gpt-4o-mini
```

### 3. Start OpenSearch

```bash
docker run -d \
  --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  opensearchproject/opensearch:2.11.0
```

### 4. Index Your PDFs

```bash
# Place PDFs in data/pdfs/
mkdir -p data/pdfs
cp /path/to/your/pdfs/*.pdf data/pdfs/

# Run indexing
python -m src build-index
```

### 5. Start the Service

```bash
python main.py
```

The service will be available at `http://localhost:8001`

## API Usage

### Query Endpoint

```bash
POST /api/agent/query
```

**Request:**

```json
{
  "question": "What are the height restrictions for residential buildings?",
  "drawing_json": {
    "properties": {
      "height": 15.5,
      "floors": 3,
      "zone": "residential"
    }
  },
  "top_k": 5
}
```

**Response:**

```json
{
  "answer": "Based on the regulations...",
  "answer_type": "pdf",
  "sources": [
    {
      "type": "pdf",
      "document": "building_regulations.pdf",
      "page": 5,
      "relevance": 0.89
    }
  ],
  "drawing_context_used": true
}
```

## Configuration

All configuration is done via environment variables. See `.env` file for full list.

### Key Settings

- `OPENSEARCH_HOST` - OpenSearch hostname (default: localhost)
- `OPENSEARCH_PORT` - OpenSearch port (default: 9200)
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `LLM_MODEL` - Model to use (default: gpt-4o-mini)
- `RELEVANCE_THRESHOLD` - Minimum relevance score (default: 0.7)
- `MAX_RESULTS` - Max documents to retrieve (default: 5)

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

### Running Tests

```bash
pytest tests/
```

### Rebuilding Index

```bash
# Force rebuild (deletes existing index)
python -m src build-index --force-rebuild

# Index only PDFs
python -m src build-index --pdfs-only

# Index only videos
python -m src build-index --videos-only
```

### Checking Index Status

```bash
# Check if index exists
curl http://localhost:9200/rag-pdf-index/_count

# View sample documents
curl http://localhost:9200/rag-pdf-index/_search?size=1
```

## Troubleshooting

### "No vector index found"

Run indexing first:

```bash
python -m src build-index
```

### "OpenSearch connection refused"

Make sure OpenSearch is running:

```bash
curl http://localhost:9200
```

### "No results found"

- Check if PDFs are indexed: `curl http://localhost:9200/rag-pdf-index/_count`
- Lower `RELEVANCE_THRESHOLD` in `.env`
- Verify PDF content quality

### "LLM API error"

- Check `OPENAI_API_KEY` is set correctly
- Verify API quota/rate limits
- Check logs for detailed error

## Architecture

See [AI_AGENT_INTEGRATION.md](../AI_AGENT_INTEGRATION.md) for detailed architecture documentation.

## License

MIT
