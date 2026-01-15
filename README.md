# Hybrid RAG Q&A System

A production-ready question-answering system that combines document knowledge with drawing/session data for intelligent building regulation queries. Built with FastAPI, React, OpenSearch, and OpenAI.

> **🚀 Quick Start:** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step installation instructions.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Component Documentation](#component-documentation)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Overview

The Hybrid RAG Q&A System is a three-tier application designed for building regulation queries. It combines PDF document knowledge with user drawing data to provide intelligent, context-aware answers.

### System Components

1. **Frontend (React + TypeScript)** - Port 80

   - User interface for authentication and question submission
   - Drawing JSON editor and session management
   - Real-time answer display with source citations

2. **Backend API (FastAPI)** - Port 8000

   - JWT-based authentication and user management
   - MongoDB session storage for drawing data
   - Request routing and service coordination

3. **AI Agent Service (FastAPI + Explaino RAG)** - Port 8001

   - OpenSearch vector database for document embeddings
   - Hybrid RAG pipeline combining PDFs with drawing context
   - OpenAI GPT-4o-mini for answer generation

4. **Infrastructure Services**
   - **OpenSearch** (Port 9200) - Vector database with ML plugins
   - **OpenSearch Dashboards** (Port 5601) - Index management UI
   - **MongoDB** (Port 27017) - User and session data storage

### Key Features

✅ JWT authentication with secure password hashing  
✅ Session-based drawing JSON storage  
✅ PDF document indexing with semantic search  
✅ Hybrid RAG combining documents + drawing context  
✅ Multi-source answer generation with citations  
✅ Docker containerization for easy deployment  
✅ Customizable embedding models  
✅ Health checks and error handling

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)                 │
│  - Authentication UI          - Drawing JSON Editor              │
│  - Question Input             - Answer Display                   │
│                         Port: 80 (nginx)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API + JWT
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                       │
│  - JWT Authentication         - Session Management               │
│  - User Registration/Login    - Drawing JSON Storage             │
│                         Port: 8000                               │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                  │
           │ MongoDB                          │ HTTP API
           ▼                                  ▼
┌──────────────────────┐      ┌──────────────────────────────────┐
│   MongoDB Database   │      │   AI Agent Service (FastAPI)     │
│  - User accounts     │      │  - Explaino RAG Pipeline         │
│  - Session data      │      │  - Query Preprocessing           │
│  - Drawing JSON      │      │  - Hybrid Retrieval              │
│    Port: 27017       │      │         Port: 8001               │
└──────────────────────┘      └──────────┬───────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │ OpenSearch API     │ OpenAI API         │
                    ▼                    ▼
         ┌──────────────────┐  ┌──────────────────────────┐
         │    OpenSearch    │  │   OpenAI GPT-4o-mini     │
         │  - Vector Index  │  │  - Answer Generation     │
         │  - Embeddings    │  │  - Context Synthesis     │
         │   Port: 9200     │  └──────────────────────────┘
         └──────────────────┘
```

### Data Flow

**Query Processing Flow:**

```
User Question → Frontend (+ JWT) → Backend
                                      ↓
                            Retrieve Drawing JSON from MongoDB
                                      ↓
                            Forward to AI Agent (Question + Drawing)
                                      ↓
                            AI Agent Processing:
                            1. Preprocess query (stopwords, etc.)
                            2. Generate embeddings
                            3. Search OpenSearch vector DB
                            4. Retrieve relevant PDF chunks
                            5. Combine PDFs + Drawing JSON
                            6. Send to OpenAI GPT-4o-mini
                            7. Generate answer with sources
                                      ↓
                            Backend → Frontend → User
```

## Prerequisites

### For Docker Deployment (Recommended)

- **Docker Engine** 20.10+
- **Docker Compose** 2.0+
- **OpenAI API Key** (required) - [Get one here](https://platform.openai.com/api-keys)
- **8GB RAM minimum** (for OpenSearch)

### For Local Development

- **Python 3.9+** (3.11 recommended)
- **Node.js 18+** and npm
- **OpenSearch 2.11+** (or Docker)
- **MongoDB 7.0+** (or Docker)
- **OpenAI API Key** (required)

## Quick Start

### Step 1: Configure Environment Variables

**Copy the example environment file:**

```bash
cd AICI
cp .env.example .env
```

**Edit `.env` and add your OpenAI API key:**

```bash
# REQUIRED: Add your OpenAI API key
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Optional: Customize embedding model**

The default embedding model is `sentence-transformers/all-mpnet-base-v2` (768 dimensions). You can change it in `.env`:

```bash
# Popular options:
# - all-mpnet-base-v2 (768 dim, best quality) - DEFAULT
# - all-MiniLM-L6-v2 (384 dim, faster, smaller)
# - paraphrase-multilingual-mpnet-base-v2 (768 dim, multilingual)

EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
```

⚠️ **Important:** If you change the embedding model:

1. Update `EMBEDDING_DIMENSION` to match the model's output dimension
2. Rebuild the index after starting services (see Step 3)

### Step 2: Start Services with Docker

```bash
docker-compose up --build
```

This starts all services:

- **OpenSearch** (vector database) - Port 9200
- **OpenSearch Dashboards** - Port 5601
- **MongoDB** (user/session storage) - Port 27017
- **AI Agent Service** - Port 8001
- **Backend API** - Port 8000
- **Frontend** - Port 80

### Step 3: Index Your PDF Documents

Place your PDF files in `ai-agent/data/pdfs/` and run:

```bash
# Access the AI Agent container
docker exec -it hybrid-rag-ai-agent bash

# Run indexing
python -m src build-index

# If you changed the embedding model, force rebuild:
python -m src build-index --force-rebuild

# Exit container
exit
```

### Step 4: Access the Application

- **Frontend**: http://localhost
- **Backend API Docs**: http://localhost:8000/docs
- **AI Agent API Docs**: http://localhost:8001/docs
- **OpenSearch Dashboards**: http://localhost:5601

### Verify Services

```bash
# Backend
curl http://localhost:8000/health

# AI Agent
curl http://localhost:8001/health

# OpenSearch
curl http://localhost:9200/_cluster/health
```

## Component Documentation

For detailed information about each component, see their respective README files:

### 📘 [Frontend Documentation](frontend/README.md)

- React component structure
- API client configuration
- Building and deployment
- Development workflow

### 📗 [Backend API Documentation](backend/README.md)

- Authentication system
- Session management
- MongoDB schema
- API endpoints
- Testing

### 📙 [AI Agent Documentation](ai-agent/README.md)

- Explaino RAG architecture
- Embedding model configuration
- PDF indexing process
- Query processing pipeline
- OpenSearch integration
- Troubleshooting

## API Documentation

### Backend API (Port 8000)

**Interactive Documentation:**

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Key Endpoints:**

```bash
# Authentication
POST /api/auth/register    # Register new user
POST /api/auth/login       # Login (returns JWT)
GET  /api/auth/me          # Get current user

# Session Management
POST /api/session/objects  # Upload drawing JSON
GET  /api/session/objects  # Retrieve drawing JSON

# Query Processing
POST /api/query            # Submit question
```

### AI Agent API (Port 8001)

**Interactive Documentation:**

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

**Key Endpoints:**

```bash
# Query Processing
POST /api/agent/query      # Process hybrid RAG query
GET  /health               # Health check with index status
```

**Example Request:**

```bash
curl -X POST "http://localhost:8001/api/agent/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are height restrictions?",
    "drawing_json": {
      "properties": {"height": 15.5, "floors": 3}
    },
    "top_k": 5
  }'
```

## Usage Examples

### Example 1: Complete Workflow

**1. Register and Login**

```bash
# Register
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "architect", "password": "secure123"}'

# Login and save token
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "architect", "password": "secure123"}' \
  | jq -r '.token')
```

**2. Upload Building Drawing**

```bash
curl -X POST "http://localhost:8000/api/session/objects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "type": "BUILDING",
      "properties": {
        "height": 15.5,
        "floors": 3,
        "zone": "residential"
      }
    }
  ]'
```

**3. Ask Questions**

```bash
# Question about regulations
curl -X POST "http://localhost:8000/api/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the height restrictions for residential buildings?"}'

# Question about your building
curl -X POST "http://localhost:8000/api/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Does my building comply with height restrictions?"}'
```

### Example 2: Drawing JSON Formats

**Simple Building:**

```json
{
  "properties": {
    "height": 15.5,
    "floors": 3,
    "zone": "residential"
  }
}
```

**Detailed CAD Drawing:**

```json
[
  {
    "type": "POLYLINE",
    "layer": "Walls",
    "points": [
      [0, 0],
      [10, 0],
      [10, 10],
      [0, 10]
    ],
    "closed": true,
    "properties": {
      "height": 3.0,
      "material": "concrete"
    }
  }
]
```

## Configuration

### Environment Variables

All configuration is done via the `.env` file. See `.env.example` for all available options.

**Key Configuration Options:**

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Embedding Model (customizable)
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# LLM Model
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3

# RAG Settings
RELEVANCE_THRESHOLD=0.7
MAX_RESULTS=5
```

### Changing Embedding Models

The system supports various sentence-transformer models:

| Model                                 | Dimension | Speed  | Quality | Use Case             |
| ------------------------------------- | --------- | ------ | ------- | -------------------- |
| all-mpnet-base-v2                     | 768       | Medium | Best    | Production (default) |
| all-MiniLM-L6-v2                      | 384       | Fast   | Good    | Development/Testing  |
| paraphrase-multilingual-mpnet-base-v2 | 768       | Medium | Best    | Multilingual         |

**To change the embedding model:**

1. Edit `.env`:

   ```bash
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   EMBEDDING_DIMENSION=384
   ```

2. Restart services:

   ```bash
   docker-compose restart ai-agent
   ```

3. Rebuild the index:
   ```bash
   docker exec -it hybrid-rag-ai-agent python -m src build-index --force-rebuild
   ```

### Production Recommendations

1. **Change SECRET_KEY:**

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Enable OpenSearch Security:**

   ```bash
   OPENSEARCH_USE_SSL=true
   OPENSEARCH_USERNAME=admin
   OPENSEARCH_PASSWORD=strong_password
   ```

3. **Configure CORS** in `backend/app/__init__.py`:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

## Troubleshooting

### Common Issues

#### 1. "No vector index found"

**Solution:**

```bash
docker exec -it hybrid-rag-ai-agent python -m src build-index
```

#### 2. OpenAI API Key Error

**Solution:**

```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Restart services
docker-compose restart ai-agent
```

#### 3. OpenSearch Connection Refused

**Solution:**

```bash
# Check OpenSearch status
curl http://localhost:9200

# Restart OpenSearch
docker-compose restart opensearch
```

#### 4. No Results from RAG Query

**Solutions:**

- Check if documents are indexed:

  ```bash
  curl http://localhost:9200/rag-pdf-index/_count
  ```

- Lower relevance threshold in `.env`:

  ```bash
  RELEVANCE_THRESHOLD=0.5
  ```

- Rebuild index:
  ```bash
  docker exec -it hybrid-rag-ai-agent python -m src build-index --force-rebuild
  ```

#### 5. Port Already in Use

**Solution:**

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Debugging Tips

**View Service Logs:**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ai-agent
```

**Check Service Health:**

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:9200/_cluster/health
```

**Inspect OpenSearch Index:**

```bash
# Count documents
curl http://localhost:9200/rag-pdf-index/_count

# View sample documents
curl http://localhost:9200/rag-pdf-index/_search?size=1
```

For more detailed troubleshooting, see the [AI Agent README](ai-agent/README.md).

## Project Structure

```
AICI/
├── .env.example               # Environment template (COPY THIS!)
├── .env                       # Your configuration (create from .env.example)
├── docker-compose.yml         # Docker orchestration
├── README.md                  # This file
│
├── frontend/                  # React Frontend (Port 80)
│   ├── src/                   # React components
│   ├── package.json
│   ├── Dockerfile
│   └── README.md             # Frontend documentation
│
├── backend/                   # FastAPI Backend (Port 8000)
│   ├── app/                   # Application code
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md             # Backend documentation
│
└── ai-agent/                  # AI Agent Service (Port 8001)
    ├── main.py
    ├── config/                # Configuration
    ├── src/                   # Explaino RAG
    ├── data/
    │   ├── pdfs/             # Place PDFs here
    │   └── transcripts/      # Optional video transcripts
    ├── requirements.txt
    ├── Dockerfile
    └── README.md             # AI Agent documentation
```

## License

## Acknowledgments

- Built with **FastAPI**, **React**, **OpenSearch**, and **OpenAI**
- Implements **sentence-transformers** for local embeddings
- Containerized with **Docker** and **Docker Compose**
