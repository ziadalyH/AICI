#!/usr/bin/env python3
"""Simple script to index PDFs in the AI Agent."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import Config
from src.rag_system import RAGSystem

if __name__ == "__main__":
    print("=" * 80)
    print("PDF Indexing Script")
    print("=" * 80)
    
    # Load configuration
    config = Config.from_env()
    
    # Initialize RAG system
    rag_system = RAGSystem(config)
    
    # Build index
    print("\nStarting PDF indexing...")
    rag_system.build_index(force_rebuild=False)
    
    print("\n" + "=" * 80)
    print("Indexing complete!")
    print("=" * 80)
