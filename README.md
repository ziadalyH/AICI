# Hybrid RAG Q&A System

A production-ready question-answering system that combines document knowledge with drawing/session data for intelligent building regulation queries. Built with FastAPI, React, OpenSearch, and OpenAI.

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ziadalyH/AICI.git
cd AICI/

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start all services
docker-compose up --build

# 4. Index PDFs (place PDFs in ai-agent/data/pdfs/)
docker exec hybrid-rag-ai-agent python index_pdfs.py

# 5. Access the application
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

## AI Strategy & Intelligent Fallback System

The system uses a sophisticated multi-tier AI strategy with intelligent fallbacks to ensure users always get meaningful responses.

### Primary AI Strategy: Hybrid RAG

The core AI approach combines three information sources:

1. **PDF Document Retrieval** - Vector search through indexed building regulations using OpenSearch
2. **Drawing Context Integration** - User's building specifications from uploaded JSON drawings
3. **Conversation History** - Multi-turn dialogue context for coherent conversations

**How it works:**

- User asks a question (e.g., "Is my extension compliant?")
- System retrieves top 5-10 most relevant regulation chunks using semantic search
- LLM (GPT-4o-mini) analyzes retrieved regulations + user's drawing specifications
- Generates contextual answer citing specific sources and comparing against user's design

### Intelligent Fallback Strategy

The system implements a cascading fallback strategy to handle edge cases gracefully:

**Tier 1: Full Hybrid Response (Ideal)**

- PDF regulations found + Drawing data available
- LLM generates answer combining both contexts
- Includes source citations and compliance analysis

**Tier 2: Drawing-Only Analysis (Fallback #1)**

- No relevant PDF regulations found
- Question is about the drawing (detected via keywords: "my building", "plot", "dimensions")
- LLM analyzes drawing data alone and describes specifications

**Tier 3: Regulations-Only Response (Fallback #2)**

- PDF regulations found but no drawing data
- LLM answers based solely on regulations
- Standard Q&A without personalized compliance checking

**Tier 4: Knowledge Summary (Final Fallback)**

- No relevant regulations found AND question not about drawing
- OR LLM refuses to answer due to insufficient context
- Returns knowledge summary showing available topics and suggested questions
- Helps users understand system capabilities and rephrase queries

### LLM Refusal Detection

The system detects when the LLM cannot confidently answer using refusal phrases like "i cannot answer", "not enough information", "insufficient information", "doesn't contain". When detected, triggers Tier 4 fallback with knowledge summary.

### AI Modes

**Standard Mode (⚡ Fast):**

- Single-shot inference
- Best for simple questions
- Faster response time, lower API cost

**Agentic Mode (🤖 Advanced):**

- Multi-step reasoning with autonomous tool use
- Agent breaks down complex tasks (retrieve → analyze → calculate → verify)
- Self-verification and iteration
- Full reasoning trace returned to user
- Best for complex tasks requiring planning

**Compliance with Adjustment Mode:**

- Triggered by keywords: "adjust", "fix", "make compliant", "provide compliant JSON"
- LLM analyzes drawing against regulations
- Generates corrected, compliant JSON with explanations

### UI Toggle for AI Modes

The chat interface includes a toggle switch to select between Standard and Agentic modes:

1. Toggle the switch in the chat header
2. Ask your question
3. System automatically routes to the selected mode
4. View reasoning steps in agentic mode responses

**API Endpoints:**

- Standard: `POST /api/query` → `POST /api/agent/query`
- Agentic: `POST /api/query-agentic` → `POST /api/agent/query-agentic`

## Agentic System Tools & Functions

The agentic AI system uses OpenAI function calling with 5 specialized tools:

### Available Tools

1. **retrieve_regulations** - Searches vector database for relevant building regulations
   - Parameters: `query` (search query), `top_k` (number of results, default: 5)
   - Returns: List of relevant regulation chunks with document, page, content, and relevance scores

2. **analyze_drawing_compliance** - Analyzes user's building drawing against regulations
   - Parameters: `regulations` (list of relevant regulations to check against)
   - Uses drawing from current context automatically
   - Returns: Structured analysis with violations, compliant aspects, and measurements

3. **calculate_drawing_dimensions** - Calculates specific dimensions from building drawing
   - Parameters: `dimension_type` (one of: "plot_area", "extension_depth", "building_height", "all")
   - Uses drawing from current context automatically
   - Returns: Calculated dimensions in meters/square meters

4. **generate_compliant_design** - Creates adjusted, compliant version of building drawing
   - Parameters: `original_drawing` (current drawing), `violations` (issues to fix), `regulations` (rules to follow)
   - Returns: Corrected JSON with explanations of changes made and compliance verification

5. **verify_compliance** - Validates if building drawing complies with regulations
   - Parameters: `regulations` (regulations to verify against)
   - Uses drawing from current context automatically
   - Returns: Compliance status (true/false), detailed explanation, and any remaining issues

### How Agentic Mode Works

1. **Planning Phase** - Agent analyzes question and decides which tools to use
2. **Execution Phase** - Agent calls tools autonomously in sequence (max 10 iterations)
3. **Synthesis Phase** - Agent combines tool results into comprehensive answer
4. **Response Phase** - Returns answer with full reasoning trace showing all tool calls

Example workflow for "Fix my non-compliant extension":

1. Agent calls `retrieve_regulations` to find relevant extension regulations
2. Agent calls `analyze_drawing_compliance` to identify violations
3. Agent calls `calculate_drawing_dimensions` to get current measurements
4. Agent calls `generate_compliant_design` to create corrected version
5. Agent calls `verify_compliance` to validate the fix
6. Agent returns corrected JSON with full explanation and reasoning steps

## Chunking Strategy

The system uses a semantic merging strategy to create meaningful, context-rich chunks from PDFs.

### Key Parameters

```python
target_chunk_size = 1024 tokens  # ~750-800 words
max_chunk_size = 1536 tokens     # Upper limit
chunk_overlap = 256 tokens       # 25% overlap for continuity
min_chunk_size = 256 tokens      # Minimum viable chunk
```

### Algorithm

1. **Extract blocks** from PDF page using PyMuPDF with font information
2. **Identify titles** based on font size (>1.15x average font size)
3. **Filter noise** blocks (less than 20 characters)
4. **Merge adjacent blocks** into semantic chunks:
   - Accumulate blocks until reaching target_chunk_size (1024 tokens)
   - Add overlap from previous chunk (256 tokens) for context continuity
   - Ensure minimum chunk size (256 tokens) for meaningful context
5. **Split oversized chunks** with overlap if they exceed max_chunk_size
6. **Preserve title context** - attach section titles to content chunks
7. **Create embeddings** for each chunk using sentence-transformers

### Benefits

- **Better Retrieval Quality** - Chunks contain complete thoughts and rule descriptions
- **Improved Answer Quality** - LLM receives sufficient context to understand regulations
- **Reduced Chunk Count** - Fewer, more meaningful chunks (typically 200-300 vs 1000+)
- **Context Continuity** - 256-token overlap ensures no information loss at boundaries
- **Title Preservation** - Section titles maintained with content for better understanding

### OCR Image Extraction

Images in PDFs are automatically processed during indexing:

- **PyMuPDF** extracts embedded images from each page
- **Tesseract OCR** extracts text from images (English + German support)
- Image text is stored as separate chunks with title "Image N"
- Each image chunk gets its own embedding and is searchable
- Failed extractions are logged but don't stop indexing

**Content Type Tracking:**

- Text chunks: `content_type: "text"`
- Image chunks: `content_type: "image"`
- Frontend can display different icons/styling based on content type

**OCR Configuration:**

- Languages: English (eng) + German (deu)
- Automatic detection and processing on startup
- Graceful fallback if OCR dependencies unavailable

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

### Step 1: Clone the Repository

```bash
git clone https://github.com/ziadalyH/AICI.git
cd AICI/
```

### Step 2: Configure Environment

```bash
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

### Step 3: Start Services

```bash
docker-compose up --build
```

Wait for all services to start (2-3 minutes for first run).

### Step 4: Index PDF Documents

Place your PDF files in `ai-agent/data/pdfs/` and run:

```bash
docker exec hybrid-rag-ai-agent python index_pdfs.py
```

### Step 5: Verify Installation

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
✅ **Multi-Step Reasoning** - Agent autonomously breaks down complex tasks  
✅ **Tool Use** - 5 specialized tools (retrieve, analyze, calculate, generate, verify)  
✅ **Self-Verification** - Agent checks and iterates on its own solutions  
✅ **Autonomous Planning** - Agent decides which tools to use and when  
✅ **Transparent Reasoning** - Full trace of agent's decision-making process

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
