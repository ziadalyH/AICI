# Hybrid RAG Q&A System

A production-ready question-answering system that combines document knowledge with drawing/session data for intelligent building regulation queries. Built with FastAPI, React, OpenSearch, and OpenAI.

## 🚀 Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Start all services
docker-compose up --build

# 3. Index PDFs (place PDFs in ai-agent/data/pdfs/)
docker exec hybrid-rag-ai-agent python index_pdfs.py

# 4. Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000/docs
# AI Agent API: http://localhost:8001/docs
```

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Component Documentation](#component-documentation)
- [Features](#features)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

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

3. **AI Agent Service (FastAPI + RAG)** - Port 8001
   - OpenSearch vector database for document embeddings
   - Hybrid RAG pipeline combining PDFs with drawing context
   - OpenAI GPT-4o-mini for answer generation
   - OCR image extraction from PDFs

4. **Infrastructure Services**
   - **OpenSearch** (Port 9200) - Vector database with ML plugins
   - **OpenSearch Dashboards** (Port 5601) - Index management UI
   - **MongoDB** (Port 27017) - User and session data storage

## Architecture

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
│  - User accounts     │      │  - RAG Pipeline                  │
│  - Session data      │      │  - Query Preprocessing           │
│  - Drawing JSON      │      │  - Hybrid Retrieval              │
│    Port: 27017       │      │  - OCR Image Extraction          │
└──────────────────────┘      │         Port: 8001               │
                              └──────────┬───────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │ OpenSearch API     │ OpenAI API         │
                    ▼                    ▼
         ┌──────────────────┐  ┌──────────────────────────┐
         │    OpenSearch    │  │   OpenAI GPT-4o-mini     │
         │  - Vector Index  │  │  - Answer Generation     │
         │  - Embeddings    │  │  - Context Synthesis     │
         │   Port: 9200     │  │  - JSON Adjustment       │
         └──────────────────┘  └──────────────────────────┘
```

## Prerequisites

### For Docker Deployment (Recommended)

- **Docker Engine** 20.10+
- **Docker Compose** 2.0+
- **OpenAI API Key** (required) - [Get one here](https://platform.openai.com/api-keys)
- **8GB RAM minimum** (for OpenSearch and embedding models)

### For Local Development

- **Python 3.9+** (3.11 recommended)
- **Node.js 18+** and npm
- **OpenSearch 2.11+**
- **MongoDB 7.0+**
- **OpenAI API Key** (required)

## Installation

### Step 1: Configure Environment

```bash
cd AICI
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```bash
# REQUIRED
OPENAI_API_KEY=sk-your-actual-api-key-here

# Optional: Customize embedding model
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
```

### Step 2: Start Services

```bash
docker-compose up --build
```

Wait for all services to start (2-3 minutes for first run).

### Step 3: Index PDF Documents

Place your PDF files in `ai-agent/data/pdfs/` and run:

```bash
docker exec hybrid-rag-ai-agent python index_pdfs.py
```

### Step 4: Verify Installation

```bash
# Check services
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:9200/_cluster/health

# Access frontend
open http://localhost
```

## Component Documentation

Each service has its own detailed README:

- **[Frontend Documentation](frontend/README.md)** - React app, components, API client
- **[Backend Documentation](backend/README.md)** - Authentication, sessions, API endpoints
- **[AI Agent Documentation](ai-agent/README.md)** - RAG pipeline, OCR, embeddings, indexing

## Features

### Core Features

✅ **Conversational Memory** - Multi-turn dialogues with context awareness  
✅ **Hybrid RAG** - Combines PDF document retrieval with user's drawing JSON  
✅ **Full Citations** - Returns all relevant sources with selection indicators  
✅ **Session Management** - Maintains conversation history per user session  
✅ **JWT Authentication** - Secure user authentication with password hashing  
✅ **Drawing Analysis** - Analyzes building drawings when no PDF context available

### Advanced Features

✅ **Adjusted JSON Generation** - LLM provides corrected, compliant JSON for non-compliant drawings  
✅ **OCR Image Extraction** - Automatically extracts and indexes text from images in PDFs  
✅ **Auto Logout** - Automatic logout and redirect when JWT token expires  
✅ **Customizable Embeddings** - Support for various sentence-transformer models  
✅ **Docker Deployment** - Full containerization for easy deployment

### How to Use Key Features

**1. Adjusted JSON Generation**

Ask the LLM to fix non-compliant drawings:

```
"My extension is 7m deep but the limit is 6m. Can you provide an adjusted compliant JSON?"
```

The LLM will provide a corrected JSON with explanations of changes made.

**2. OCR Image Extraction**

Images in PDFs are automatically processed during indexing. To verify:

```bash
docker exec hybrid-rag-ai-agent python check_images.py
```

See [ai-agent/README.md](ai-agent/README.md) for details.

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# LLM Model
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3

# RAG Settings
RELEVANCE_THRESHOLD=0.7
MAX_RESULTS=5
```

### Embedding Models

| Model                                 | Dimension | Speed  | Quality | Use Case             |
| ------------------------------------- | --------- | ------ | ------- | -------------------- |
| all-mpnet-base-v2                     | 768       | Medium | Best    | Production (default) |
| all-MiniLM-L6-v2                      | 384       | Fast   | Good    | Development/Testing  |
| paraphrase-multilingual-mpnet-base-v2 | 768       | Medium | Best    | Multilingual         |

To change the embedding model:

1. Edit `.env` with new model and dimension
2. Restart services: `docker-compose restart ai-agent`
3. Rebuild index: `docker exec hybrid-rag-ai-agent python index_pdfs.py`

## Troubleshooting

### Common Issues

**1. "No vector index found"**

```bash
docker exec hybrid-rag-ai-agent python index_pdfs.py
```

**2. OpenAI API Key Error**

```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Restart services
docker-compose restart ai-agent
```

**3. AI Agent Container Restarting (Out of Memory)**

Increase Docker Desktop memory to 8GB:

- Docker Desktop → Settings → Resources → Memory → 8GB
- Apply & Restart

**4. Port Already in Use**

```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

**5. No Results from RAG Query**

```bash
# Check if documents are indexed
curl http://localhost:9200/rag-pdf-index/_count

# Lower relevance threshold in .env
RELEVANCE_THRESHOLD=0.5
```

### Debugging

**View Logs:**

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

# View sample
curl http://localhost:9200/rag-pdf-index/_search?size=1
```

For detailed troubleshooting, see component-specific README files.

## Project Structure

```
AICI/
├── .env.example               # Environment template
├── .env                       # Your configuration (create from .env.example)
├── docker-compose.yml         # Docker orchestration
├── README.md                  # This file
│
├── frontend/                  # React Frontend (Port 80)
│   ├── src/                   # React components
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── README.md             # Frontend documentation
│
├── backend/                   # FastAPI Backend (Port 8000)
│   ├── app/                   # Application code
│   ├── tests/                 # Backend tests
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md             # Backend documentation
│
└── ai-agent/                  # AI Agent Service (Port 8001)
    ├── src/                   # RAG pipeline
    ├── config/                # Configuration
    ├── tests/                 # AI agent tests
    ├── data/
    │   └── pdfs/             # Place PDFs here
    ├── main.py
    ├── index_pdfs.py         # Indexing script
    ├── check_images.py       # Image verification script
    ├── requirements.txt
    ├── Dockerfile
    └── README.md             # AI Agent documentation
```

## API Documentation

### Backend API (Port 8000)

Interactive docs: http://localhost:8000/docs

**Key Endpoints:**

```bash
POST /api/auth/register    # Register new user
POST /api/auth/login       # Login (returns JWT)
GET  /api/auth/me          # Get current user
POST /api/session/objects  # Upload drawing JSON
GET  /api/session/objects  # Retrieve drawing JSON
POST /api/query            # Submit question
```

### AI Agent API (Port 8001)

Interactive docs: http://localhost:8001/docs

**Key Endpoints:**

```bash
POST /api/agent/query      # Process hybrid RAG query
GET  /health               # Health check with index status
```

## Usage Example

```bash
# 1. Register and login
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "architect", "password": "secure123"}'

TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "architect", "password": "secure123"}' \
  | jq -r '.token')

# 2. Upload building drawing
curl -X POST "http://localhost:8000/api/session/objects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[{"type": "BUILDING", "properties": {"height": 15.5, "floors": 3}}]'

# 3. Ask questions
curl -X POST "http://localhost:8000/api/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the height restrictions for residential buildings?"}'
```

## License

[Your License Here]

## Acknowledgments

Built with **FastAPI**, **React**, **OpenSearch**, **OpenAI**, and **sentence-transformers**.
