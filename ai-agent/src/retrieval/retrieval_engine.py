"""Retrieval engine module for searching OpenSearch."""

import logging
from typing import List, Union, Optional, Dict, Any
import numpy as np
from opensearchpy import OpenSearch

from ..models import PDFResult
from config.config import Config


class RetrievalEngine:
    """
    Search OpenSearch vector index for PDF documents.
    
    This class handles:
    - Searching PDF chunks using k-NN similarity
    - Filtering results by relevance threshold
    - Parsing OpenSearch responses and extracting metadata
    
    Uses pure k-NN search for consistent scoring (0.0 to 1.0).
    """
    
    def __init__(
        self,
        opensearch_client: OpenSearch,
        config: Config,
        logger: logging.Logger
    ):
        """
        Initialize the RetrievalEngine.
        
        Args:
            opensearch_client: OpenSearch client instance
            config: Configuration object containing retrieval settings
            logger: Logger instance for logging operations
        """
        self.opensearch_client = opensearch_client
        self.pdf_index_name = config.opensearch_pdf_index
        self.relevance_threshold = config.relevance_threshold
        self.max_results = config.max_results
        self.logger = logger
    
    def retrieve(
        self,
        query_embedding: np.ndarray,
        query_text: str = ""
    ) -> Union[List[PDFResult], None]:
        """
        Execute retrieval using OpenSearch k-NN search.
        
        Strategy:
        1. Search PDF embeddings using k-NN search
        2. If top result score >= relevance_threshold, return top N PDF results
        3. Otherwise, return None (no answer)
        
        Args:
            query_embedding: Query vector embedding
            query_text: Original query text (unused, kept for compatibility)
            
        Returns:
            List[PDFResult] if PDF matches found above threshold
            None if no results above threshold
        """
        self.logger.info("Starting PDF retrieval")
        
        # Search PDF documents with k-NN search
        self.logger.debug("Searching PDF documents with k-NN search")
        pdf_results = self.search_pdfs(query_embedding, query_text)
        
        if pdf_results:
            top_pdf = pdf_results[0]
            self.logger.info(
                f"Top PDF result: filename={top_pdf.pdf_filename}, "
                f"score={top_pdf.score:.4f}, threshold={self.relevance_threshold}"
            )
            
            if top_pdf.score >= self.relevance_threshold:
                self.logger.info(f"PDF result exceeds threshold, returning top {len(pdf_results)} PDF results")
                return pdf_results
            else:
                self.logger.info(
                    f"PDF result below threshold ({top_pdf.score:.4f} < "
                    f"{self.relevance_threshold}), no answer found"
                )
        else:
            self.logger.info("No PDF results found")
        
        self.logger.info("No results above threshold in either source")
        return None
    
    def search_pdfs(self, query_embedding: np.ndarray, query_text: str = "") -> List[PDFResult]:
        """
        Search PDF document chunks in OpenSearch using k-NN search.
        
        Args:
            query_embedding: Query vector embedding
            query_text: Original query text (not used, kept for backward compatibility)
            
        Returns:
            List of PDFResult objects, sorted by score (descending)
        """
        self.logger.debug("Executing k-NN search for PDF documents")
        
        try:
            # Execute k-NN search
            raw_results = self.knn_search(
                query_embedding=query_embedding,
                k=self.max_results
            )
            
            # Parse results into PDFResult objects
            pdf_results = []
            for hit in raw_results:
                source = hit.get("_source", {})
                score = hit.get("_score", 0.0)
                document_id = hit.get("_id", "")
                
                pdf_result = PDFResult(
                    pdf_filename=source.get("pdf_filename", ""),
                    page_number=source.get("page_number", 0),
                    paragraph_index=source.get("paragraph_index", 0),
                    source_snippet=source.get("text", ""),
                    score=score,
                    document_id=document_id,
                    title=source.get("title")  # Extract title
                )
                pdf_results.append(pdf_result)
            
            self.logger.info(f"Found {len(pdf_results)} PDF results")
            
            # Print all results before filtering
            if pdf_results:
                self.logger.info("="*80)
                self.logger.info("PDF SEARCH RESULTS (before threshold filtering):")
                self.logger.info("="*80)
                for i, result in enumerate(pdf_results, 1):
                    self.logger.info(f"\nResult {i}:")
                    self.logger.info(f"  PDF: {result.pdf_filename}")
                    self.logger.info(f"  Score: {result.score:.4f}")
                    self.logger.info(f"  Page: {result.page_number}, Paragraph: {result.paragraph_index}")
                    self.logger.info(f"  Title: {result.title or 'No title'}")
                    self.logger.info(f"  Snippet: {result.source_snippet[:200]}...")
                self.logger.info("="*80)
            
            # Filter by threshold
            filtered_results = self.filter_by_threshold(pdf_results, self.relevance_threshold)
            self.logger.info(
                f"After threshold filtering ({self.relevance_threshold}): {len(filtered_results)} PDF results"
            )
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error searching PDFs: {str(e)}")
            return []
    
    def search_pdfs_by_filename(
        self, 
        query_embedding: np.ndarray, 
        pdf_filename: str,
        query_text: str = ""
    ) -> List[PDFResult]:
        """
        Search PDF document chunks filtered by specific filename.
        
        This method enables targeted PDF search for a specific document,
        improving relevance and reducing noise from unrelated documents.
        
        Args:
            query_embedding: Query vector embedding
            pdf_filename: Name of the PDF file to search (e.g., "customers_guide.pdf")
            query_text: Original query text (not used, kept for backward compatibility)
            
        Returns:
            List of PDFResult objects from the specified PDF, sorted by score (descending)
        """
        self.logger.info(f"Executing targeted PDF search for: {pdf_filename}")
        
        try:
            # Execute k-NN search with pdf_filename filter
            raw_results = self.knn_search_with_filter(
                query_embedding=query_embedding,
                k=self.max_results,
                filter_field="pdf_filename",
                filter_value=pdf_filename
            )
            
            # Parse results into PDFResult objects
            pdf_results = []
            for hit in raw_results:
                source = hit.get("_source", {})
                score = hit.get("_score", 0.0)
                document_id = hit.get("_id", "")
                
                pdf_result = PDFResult(
                    pdf_filename=source.get("pdf_filename", ""),
                    page_number=source.get("page_number", 0),
                    paragraph_index=source.get("paragraph_index", 0),
                    source_snippet=source.get("text", ""),
                    score=score,
                    document_id=document_id,
                    title=source.get("title")
                )
                pdf_results.append(pdf_result)
            
            self.logger.info(f"Found {len(pdf_results)} results in {pdf_filename}")
            
            # Print all results before filtering
            if pdf_results:
                self.logger.info("="*80)
                self.logger.info(f"TARGETED PDF SEARCH RESULTS ({pdf_filename}):")
                self.logger.info("="*80)
                for i, result in enumerate(pdf_results, 1):
                    self.logger.info(f"\nResult {i}:")
                    self.logger.info(f"  PDF: {result.pdf_filename}")
                    self.logger.info(f"  Score: {result.score:.4f}")
                    self.logger.info(f"  Page: {result.page_number}, Paragraph: {result.paragraph_index}")
                    self.logger.info(f"  Title: {result.title or 'No title'}")
                    self.logger.info(f"  Snippet: {result.source_snippet[:200]}...")
                self.logger.info("="*80)
            
            # Filter by threshold
            filtered_results = self.filter_by_threshold(pdf_results, self.relevance_threshold)
            self.logger.info(
                f"After threshold filtering ({self.relevance_threshold}): "
                f"{len(filtered_results)} results from {pdf_filename}"
            )
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error searching PDF {pdf_filename}: {str(e)}")
            return []
    
    def knn_search(
        self,
        query_embedding: np.ndarray,
        k: int
    ) -> List[Dict[str, Any]]:
        """
        Perform k-NN search in OpenSearch PDF index.
        
        Args:
            query_embedding: Query vector embedding
            k: Number of nearest neighbors to retrieve
            
        Returns:
            List of raw hit dictionaries from OpenSearch response
        """
        # Use PDF index
        index_name = self.pdf_index_name
        
        self.logger.debug(
            f"Executing k-NN search: index={index_name}, k={k}"
        )
        
        # Convert numpy array to list for JSON serialization
        query_vector = query_embedding.tolist()
        
        # Build k-NN query
        query_body = {
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": k
                    }
                }
            }
        }
        
        try:
            # Execute search
            response = self.opensearch_client.search(
                index=index_name,
                body=query_body
            )
            
            # Extract hits
            hits = response.get("hits", {}).get("hits", [])
            
            self.logger.debug(
                f"k-NN search returned {len(hits)} results from {index_name}"
            )
            
            return hits
            
        except Exception as e:
            self.logger.error(
                f"k-NN search failed for index {index_name}: {str(e)}"
            )
            raise
    
    def knn_search_with_filter(
        self,
        query_embedding: np.ndarray,
        k: int,
        filter_field: str,
        filter_value: str
    ) -> List[Dict[str, Any]]:
        """
        Perform k-NN search with metadata filtering in OpenSearch.
        
        This method combines vector similarity search with exact metadata filtering,
        enabling targeted searches within document subsets (e.g., specific PDFs).
        
        Args:
            query_embedding: Query vector embedding
            k: Number of nearest neighbors to retrieve
            filter_field: Metadata field to filter on (e.g., "pdf_filename")
            filter_value: Value to match for the filter field
            
        Returns:
            List of raw hit dictionaries from OpenSearch response
        """
        # Use PDF index
        index_name = self.pdf_index_name
        
        self.logger.debug(
            f"Executing k-NN search with filter: index={index_name}, k={k}, "
            f"{filter_field}={filter_value}"
        )
        
        # Convert numpy array to list for JSON serialization
        query_vector = query_embedding.tolist()
        
        # Build k-NN query with bool filter
        query_body = {
            "size": k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_vector,
                                    "k": k
                                }
                            }
                        }
                    ],
                    "filter": [
                        {
                            "term": {
                                filter_field: filter_value
                            }
                        }
                    ]
                }
            }
        }
        
        try:
            # Execute search
            response = self.opensearch_client.search(
                index=index_name,
                body=query_body
            )
            
            # Extract hits
            hits = response.get("hits", {}).get("hits", [])
            
            self.logger.debug(
                f"k-NN search with filter returned {len(hits)} results from {index_name}"
            )
            
            return hits
            
        except Exception as e:
            self.logger.error(
                f"k-NN search with filter failed for index {index_name}: {str(e)}"
            )
            raise
    
    def filter_by_threshold(
        self,
        results: List[PDFResult],
        threshold: float
    ) -> List[PDFResult]:
        """
        Filter results below relevance threshold.
        
        Args:
            results: List of PDFResult objects
            threshold: Minimum score threshold
            
        Returns:
            Filtered list containing only results with score >= threshold
        """
        if not results:
            return []
        
        filtered = [r for r in results if r.score >= threshold]
        
        self.logger.debug(
            f"Filtered {len(results)} results to {len(filtered)} "
            f"above threshold {threshold}"
        )
        
        return filtered
