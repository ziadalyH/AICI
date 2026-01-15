# Setup Guide - Hybrid RAG Q&A System

This guide will help you get the Hybrid RAG Q&A System up and running in minutes.

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- 8GB RAM minimum

## Setup Steps

### 1. Configure Environment

```bash
# Navigate to project directory
cd AICI

# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

**Required: Add your OpenAI API key in `.env`:**

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 2. (Optional) Customize Embedding Model

The default embedding model is `all-mpnet-base-v2` (768 dimensions). If you want to use a different model, edit `.env`:

```bash
# Fast and smaller (good for testing)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Multilingual support
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
EMBEDDING_DIMENSION=768
```

**Available Models:**

| Model                                 | Dimension | Speed  | Quality | Best For     |
| ------------------------------------- | --------- | ------ | ------- | ------------ |
| all-mpnet-base-v2 (default)           | 768       | Medium | Best    | Production   |
| all-MiniLM-L6-v2                      | 384       | Fast   | Good    | Development  |
| paraphrase-multilingual-mpnet-base-v2 | 768       | Medium | Best    | Multilingual |

⚠️ **Important:** If you change the model, you must rebuild the index (see step 4).

### 3. Start Services

```bash
docker-compose up --build
```

Wait for all services to start (about 2-3 minutes). You'll see:

- ✓ OpenSearch healthy
- ✓ MongoDB healthy
- ✓ AI Agent started
- ✓ Backend started
- ✓ Frontend started

### 4. Index Your Documents

**Place your PDF files:**

```bash
# Copy your PDFs to the data directory
cp /path/to/your/pdfs/*.pdf ai-agent/data/pdfs/
```

**Run indexing:**

```bash
# Access the AI Agent container
docker exec -it hybrid-rag-ai-agent bash

# Build the index
python -m src build-index

# If you changed the embedding model, use --force-rebuild
python -m src build-index --force-rebuild

# Exit container
exit
```

### 5. Verify Installation

**Check service health:**

```bash
# Backend
curl http://localhost:8000/health

# AI Agent
curl http://localhost:8001/health

# OpenSearch
curl http://localhost:9200/_cluster/health
```

**Check if documents are indexed:**

```bash
curl http://localhost:9200/rag-pdf-index/_count
```

You should see: `{"count": <number_of_chunks>, ...}`

### 6. Access the Application

Open your browser and navigate to:

- **Frontend**: http://localhost
- **Backend API Docs**: http://localhost:8000/docs
- **AI Agent API Docs**: http://localhost:8001/docs
- **OpenSearch Dashboards**: http://localhost:5601

## Quick Test

Test the system with a simple query:

```bash
curl -X POST "http://localhost:8001/api/agent/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main topics in the documents?",
    "drawing_json": {},
    "top_k": 5
  }'
```

You should receive a JSON response with an answer and sources.

## Common Issues

### "No vector index found"

**Solution:** Run the indexing step (step 4 above).

### "OpenAI API key not found"

**Solution:**

1. Check `.env` file has `OPENAI_API_KEY=sk-...`
2. Restart services: `docker-compose restart ai-agent`

### "Connection refused to OpenSearch"

**Solution:**

1. Wait 30 seconds for OpenSearch to fully start
2. Check logs: `docker-compose logs opensearch`
3. Restart: `docker-compose restart opensearch`

### No results from queries

**Solution:**

1. Verify documents are indexed: `curl http://localhost:9200/rag-pdf-index/_count`
2. Lower threshold in `.env`: `RELEVANCE_THRESHOLD=0.5`
3. Rebuild index: `docker exec -it hybrid-rag-ai-agent python -m src build-index --force-rebuild`

## Next Steps

1. **Register a user** via the frontend at http://localhost
2. **Upload drawing JSON** with your building specifications
3. **Ask questions** about regulations and your building
4. **Explore the API** at http://localhost:8000/docs

## Need Help?

- Check the [main README](README.md) for detailed documentation
- See [AI Agent README](ai-agent/README.md) for RAG pipeline details
- See [Backend README](backend/README.md) for API details
- View logs: `docker-compose logs -f <service-name>`

## Stopping the System

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Updating the System

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up --build

# If you changed embedding models, rebuild index
docker exec -it hybrid-rag-ai-agent python -m src build-index --force-rebuild
```
