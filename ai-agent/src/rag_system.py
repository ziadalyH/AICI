"""Main RAG system orchestrator.

This module provides the RAGSystem class which coordinates all components
of the RAG chatbot backend: ingestion, processing, retrieval, and response generation.
"""

import logging
from pathlib import Path
from typing import Union, Optional, Dict, Any
from opensearchpy import OpenSearch

from config.config import Config
from .models import PDFResponse, NoAnswerResponse
from .ingestion.pdf_ingester import PDFIngester
from .processing.chunking import ChunkingModule
from .processing.embedding import EmbeddingEngine
from .processing.indexing import VectorIndexBuilder
from .retrieval.query_processor import QueryProcessor
from .retrieval.retrieval_engine import RetrievalEngine
from .retrieval.response_generator import ResponseGenerator
from .llm_inference import LLMInferenceService
from config.knowledge_summary import KnowledgeSummaryGenerator


class RAGSystem:
    """
    Main orchestrator for the RAG Chatbot Backend.
    
    This class coordinates all components of the system:
    - Data ingestion (PDFs only)
    - Text chunking and embedding generation
    - Vector index building and management
    - Query processing and retrieval
    - Response generation with LLM-based answers
    
    The system searches PDF documents and returns relevant answers.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the RAG system with all components.
        
        Args:
            config: Configuration object containing all system settings
        """
        self.config = config
        self.logger = self._setup_logger()
        
        self.logger.info("=" * 80)
        self.logger.info("Initializing RAG System (PDF-only)")
        self.logger.info("=" * 80)
        self.logger.info(f"OpenSearch: {config.opensearch_host}:{config.opensearch_port}")
        
        # Log LLM configuration
        self.logger.info("")
        self.logger.info("🤖 LLM Configuration:")
        self.logger.info(f"  Provider: {config.llm_provider.upper()}")
        self.logger.info(f"  Model: {config.llm_model}")
        self.logger.info(f"  Temperature: {config.llm_temperature}")
        self.logger.info(f"  Max Tokens: {config.llm_max_tokens}")
        self.logger.info("")
        
        # Initialize core components
        self.embedding_engine = EmbeddingEngine(config, self.logger)
        self.vector_index_builder = VectorIndexBuilder(config, self.logger)
        self.opensearch_client = self.vector_index_builder.opensearch_client
        
        # Initialize centralized LLM inference service
        self.llm_service = LLMInferenceService(
            config=config,
            opensearch_client=self.opensearch_client,
            logger=self.logger
        )
        
        # Initialize ingestion components (PDF only)
        self.pdf_ingester = PDFIngester(config, self.logger)
        self.chunking_module = ChunkingModule(config, self.logger)
        
        # Initialize retrieval components
        self.query_processor = QueryProcessor(self.embedding_engine, self.logger)
        self.retrieval_engine = RetrievalEngine(
            self.opensearch_client,
            config,
            self.logger
        )
        self.response_generator = ResponseGenerator(
            config=config,
            logger=self.logger,
            llm_service=self.llm_service
        )
        
        # Initialize knowledge summary generator
        self.knowledge_summary_generator = KnowledgeSummaryGenerator(
            config=config,
            logger=self.logger,
            llm_service=self.llm_service
        )
        
        self.logger.info("RAG System initialized successfully")
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up logger with configured log level.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(self.config.log_level)
        
        # Create console handler if not already configured
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(self.config.log_level)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
        
        return logger
    
    def answer_question(
        self,
        question: str,
        drawing_json: Optional[Dict[str, Any]] = None
    ) -> Union[PDFResponse, NoAnswerResponse]:
        """
        Main entry point for answering questions.
        
        This method implements the complete query pipeline:
        1. Process and embed the query
        2. Retrieve relevant PDF content
        3. Generate natural language answer with LLM (including drawing JSON context)
        4. Return structured response with citations
        
        Args:
            question: User's question as a string
            drawing_json: Optional user's building drawing JSON for context
            
        Returns:
            PDFResponse if PDF content found and LLM can answer
            NoAnswerResponse if no relevant content found or LLM cannot answer
            
        Raises:
            ValueError: If question is empty
            Exception: If any component fails during processing
        """
        self.logger.info(f"Processing question: {question[:100]}...")
        if drawing_json:
            self.logger.info(f"Drawing JSON provided: {drawing_json}")
        
        try:
            # Step 1: Process and embed the query
            self.logger.info("Step 1: Processing query")
            query_embedding = self.query_processor.process_query(question)
            
            # Step 2: Retrieve relevant PDF content
            self.logger.info("Step 2: Retrieving relevant PDF content")
            retrieval_result = self.retrieval_engine.retrieve(query_embedding, question)
            
            # Step 3: Generate response with LLM-based answer (including drawing JSON)
            self.logger.info("Step 3: Generating response")
            response = self.response_generator.generate_response(
                query=question,
                result=retrieval_result,
                drawing_json=drawing_json
            )
            
            self.logger.info(f"Successfully generated {response.answer_type} response")
            return response
            
        except ValueError as e:
            self.logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error answering question: {str(e)}", exc_info=True)
            raise
    
    def build_index(
        self, 
        force_rebuild: bool = False
    ) -> None:
        """
        Build or rebuild the vector index from PDF files.
        
        This method:
        1. Checks what's already indexed (unless force_rebuild=True)
        2. Only indexes missing PDFs (resume capability)
        3. Ingests PDF documents
        4. Chunks the content into segments
        5. Generates embeddings for all chunks
        6. Builds the OpenSearch vector index
        
        Args:
            force_rebuild: If True, delete and rebuild entire index from scratch
            
        Raises:
            Exception: If indexing fails
        """
        self.logger.info("Starting index building process (PDF-only)")
        
        try:
            # Check if we should rebuild from scratch
            if force_rebuild:
                self.logger.info("Force rebuild requested - deleting existing index")
                
                if self.opensearch_client.indices.exists(index=self.config.opensearch_pdf_index):
                    self.opensearch_client.indices.delete(index=self.config.opensearch_pdf_index)
                    self.logger.info(f"Deleted PDF index: {self.config.opensearch_pdf_index}")
            
            # Create index if it doesn't exist
            self.vector_index_builder.create_index_if_not_exists(self.config.opensearch_pdf_index, "pdf")
            
            # Get already indexed files (for resume capability)
            indexed_pdfs = self._get_indexed_files()
            
            self.logger.info(f"Already indexed: {len(indexed_pdfs)} PDFs")
            
            # Step 1: Ingest PDF documents
            self.logger.info("Step 1: Ingesting PDF documents")
            all_pdf_paragraphs = self.pdf_ingester.ingest_directory()
            
            # Filter out already indexed PDFs
            pdf_paragraphs = [p for p in all_pdf_paragraphs if p.pdf_filename not in indexed_pdfs]
            
            # Count paragraphs per PDF for logging
            pdf_counts = {}
            for p in all_pdf_paragraphs:
                pdf_counts[p.pdf_filename] = pdf_counts.get(p.pdf_filename, 0) + 1
            
            new_pdf_count = len(set(p.pdf_filename for p in pdf_paragraphs))
            
            self.logger.info(
                f"Ingested {len(all_pdf_paragraphs)} PDF paragraphs from {len(pdf_counts)} PDFs "
                f"({new_pdf_count} new PDFs, {len(indexed_pdfs)} already indexed)"
            )
            
            # Check if there's anything to index
            if not pdf_paragraphs:
                self.logger.info("All files are already indexed. Nothing to do.")
                self.logger.info("Use force_rebuild=True to reindex everything.")
                return
            
            # Step 2: Chunk PDF paragraphs
            self.logger.info("Step 2: Chunking PDF paragraphs")
            pdf_chunks = self.chunking_module.chunk_pdf_paragraphs(pdf_paragraphs)
            self.logger.info(f"Created {len(pdf_chunks)} PDF chunks")
            
            # Step 3: Build vector index (only for new content)
            self.logger.info("Step 3: Building vector index for new content")
            self.vector_index_builder.build_index(
                transcript_chunks=[],  # No transcripts
                pdf_chunks=pdf_chunks,
                embedding_engine=self.embedding_engine
            )
            
            # Show final status
            final_indexed_pdfs = self._get_indexed_files()
            
            self.logger.info("Index building completed successfully")
            self.logger.info(
                f"Total indexed: {len(final_indexed_pdfs)} PDFs"
            )
            
            # Generate knowledge summary
            self.logger.info("Generating knowledge summary...")
            try:
                # Check if LLM service is available
                if not self.llm_service.is_available():
                    self.logger.warning(
                        "LLM service not available yet. Skipping knowledge summary generation. "
                        "Knowledge summary will be generated on next indexing after LLM setup is complete."
                    )
                else:
                    # Get sample chunks for summary generation
                    sample_chunks = self._get_sample_chunks(pdf_chunks)
                    
                    # Generate summary
                    self.knowledge_summary_generator.generate_summary(
                        pdf_files=list(final_indexed_pdfs),
                        video_ids=[],  # No videos
                        sample_chunks=sample_chunks
                    )
            except Exception as e:
                self.logger.warning(f"Failed to generate knowledge summary: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to build index: {str(e)}", exc_info=True)
            raise
    
    def _get_sample_chunks(self, pdf_chunks):
        """Get sample PDF chunks for summary generation."""
        sample_chunks = {
            'pdf': []
        }
        
        # Get sample PDF chunks
        if pdf_chunks:
            sample_size = min(20, len(pdf_chunks))
            step = max(1, len(pdf_chunks) // sample_size)
            sample_chunks['pdf'] = [chunk.text for chunk in pdf_chunks[::step][:sample_size]]
        
        return sample_chunks
    
    def _get_indexed_files(self):
        """
        Get list of completely indexed PDFs.
        
        Checks max page number in rag-pdf-index.
        
        Returns:
            Set of PDF filenames
        """
        indexed_pdfs = set()
        
        try:
            # Check PDF index
            if self.opensearch_client.indices.exists(index=self.config.opensearch_pdf_index):
                pdf_response = self.opensearch_client.search(
                    index=self.config.opensearch_pdf_index,
                    body={
                        "size": 0,
                        "aggs": {
                            "pdfs": {
                                "terms": {
                                    "field": "pdf_filename",
                                    "size": 10000
                                },
                                "aggs": {
                                    "max_page": {"max": {"field": "page_number"}},
                                    "unique_pages": {"cardinality": {"field": "page_number"}},
                                    "total_chunks": {"value_count": {"field": "page_number"}}
                                }
                            }
                        }
                    }
                )
                
                if 'aggregations' in pdf_response:
                    buckets = pdf_response['aggregations']['pdfs']['buckets']
                    for bucket in buckets:
                        pdf_filename = bucket['key']
                        max_page = int(bucket['max_page']['value'])
                        unique_pages = bucket['unique_pages']['value']
                        total_chunks = bucket['doc_count']
                        
                        # Consider complete if has documents
                        if total_chunks > 0:
                            indexed_pdfs.add(pdf_filename)
                            self.logger.debug(
                                f"PDF {pdf_filename}: {total_chunks} chunks, "
                                f"{unique_pages} pages, max page {max_page}"
                            )
            
        except Exception as e:
            self.logger.warning(f"Error checking indexed files: {e}")
        
        return indexed_pdfs
    
    def check_index_exists(self) -> bool:
        """
        Check if OpenSearch PDF index exists and has documents.
        
        Returns:
            True if PDF index exists and contains documents
            False if index doesn't exist or is empty
        """
        try:
            # Check PDF index
            if self.opensearch_client.indices.exists(index=self.config.opensearch_pdf_index):
                count_response = self.opensearch_client.count(index=self.config.opensearch_pdf_index)
                pdf_count = count_response.get('count', 0)
                if pdf_count > 0:
                    self.logger.info(f"PDF index exists with {pdf_count} documents")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking index existence: {str(e)}")
            return False
