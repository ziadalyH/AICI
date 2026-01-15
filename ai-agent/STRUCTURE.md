# AI Agent Folder Structure

## Clean Structure

```
ai-agent/
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker container definition
├── README.md                  # Quick start guide
├── test_api.py               # API test script
├── .gitignore                # Git ignore rules
├── .dockerignore             # Docker ignore rules
│
├── config/                   # Configuration modules
│   ├── __init__.py
│   ├── config.py            # Main configuration (env-based)
│   ├── knowledge_summary.py # Knowledge summary generator
│   ├── api.py               # API configuration
│   ├── cli.py               # CLI configuration
│   └── opensearch_ml/       # OpenSearch ML setup scripts
│
├── src/                     # Explaino RAG core modules
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── rag_system.py        # Main RAG orchestrator
│   ├── llm_inference.py     # LLM service
│   ├── models.py            # Data models
│   │
│   ├── ingestion/           # Data ingestion
│   │   ├── __init__.py
│   │   ├── pdf_ingester.py
│   │   └── transcript_ingester.py
│   │
│   ├── processing/          # Data processing
│   │   ├── __init__.py
│   │   ├── chunking.py      # Text chunking strategies
│   │   ├── embedding.py     # Embedding generation
│   │   └── indexing.py      # Vector index building
│   │
│   └── retrieval/           # Query and retrieval
│       ├── __init__.py
│       ├── query_processor.py    # Query preprocessing
│       ├── retrieval_engine.py   # Vector search
│       └── response_generator.py # Answer generation
│
├── data/                    # Data directory
│   ├── pdfs/               # Place PDF documents here
│   │   └── .gitkeep
│   └── transcripts/        # Place video transcripts here (optional)
│       └── .gitkeep
│
└── tests/                  # Test suite
    ├── __init__.py
    ├── test_api.py
    ├── test_document_processor.py
    ├── test_rag_pipeline_integration.py
    └── test_vector_store.py
```

## Removed Files/Folders

The following unnecessary files and folders have been removed:

### Old Implementation

- ❌ `app/` - Old custom RAG implementation (replaced by Explaino)
- ❌ `hybrid_rag_main.py` - Duplicate main file
- ❌ `hybrid_rag_pipeline.py` - Duplicate pipeline file
- ❌ `verify_api.py` - Old verification script

### Duplicate Explaino Copies

- ❌ `explaino_src/` - Duplicate of src/
- ❌ `explaino_config/` - Duplicate of config/

### Development Files

- ❌ `venv/` - Virtual environment (should be local)
- ❌ `.pytest_cache/` - Test cache
- ❌ `scripts/` - Old scripts

### Old Data

- ❌ `data/faiss_index.faiss` - Old FAISS index (now using OpenSearch)
- ❌ `data/faiss_index.pkl` - Old FAISS metadata

### Documentation

- ❌ `RAG_PIPELINE_IMPLEMENTATION.md` - Old implementation doc

## Key Files

### Entry Points

- **`main.py`** - FastAPI application with `/api/agent/query` endpoint
- **`src/__main__.py`** - CLI for indexing: `python -m src build-index`

### Configuration

- **`config/config.py`** - Loads from environment variables
- **`.env`** (root) - Environment configuration

### Core Logic

- **`src/rag_system.py`** - Orchestrates entire RAG pipeline
- **`src/llm_inference.py`** - Handles LLM calls (OpenAI)
- **`src/retrieval/retrieval_engine.py`** - Vector search with OpenSearch

### Testing

- **`test_api.py`** - Quick API tests
- **`tests/`** - Full test suite

## Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Place PDFs

```bash
cp your-pdfs/*.pdf data/pdfs/
```

### 3. Index Documents

```bash
python -m src build-index
```

### 4. Start Service

```bash
python main.py
```

### 5. Test API

```bash
python test_api.py
```

## Clean and Organized!

The folder is now clean with only the essential Explaino RAG components and our custom FastAPI integration. No duplicates, no old implementations, just what we need! 🎯
