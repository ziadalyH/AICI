#!/usr/bin/env python3
"""
Simple script to index PDFs in the AI Agent.

This script will:
1. Delete any existing knowledge summary
2. Index all PDFs in the data/pdfs directory
3. Generate a fresh knowledge summary based on indexed content
"""

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
    print()
    print("This will:")
    print("  1. Delete old knowledge summary")
    print("  2. Index PDFs (resume from last run)")
    print("  3. Generate fresh knowledge summary")
    print()
    
    # Load configuration
    config = Config.from_env()
    
    # Initialize RAG system
    rag_system = RAGSystem(config)
    
    # Build index (this will delete old summary and generate new one)
    print("Starting PDF indexing...")
    rag_system.build_index(force_rebuild=False)
    
    print("\n" + "=" * 80)
    print("Indexing complete!")
    print("=" * 80)
