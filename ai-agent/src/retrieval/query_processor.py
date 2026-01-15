"""Query processing module for user queries.

This module handles processing user queries, including validation,
preprocessing, and embedding generation using OpenAI.
"""

import logging
import string
import numpy as np
import nltk
from nltk.corpus import stopwords

from ..processing.embedding import EmbeddingEngine

# Download stopwords on first import (will be cached)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


class QueryProcessor:
    """Process user queries and generate query embeddings.
    
    This class handles query validation, text preprocessing, and embedding
    generation using the same embedding model as content chunks to ensure
    semantic similarity search works correctly.
    """
    
    def __init__(self, embedding_engine: EmbeddingEngine, logger: logging.Logger):
        """Initialize the query processor.
        
        Args:
            embedding_engine: EmbeddingEngine instance for generating embeddings
            logger: Logger instance for logging operations
        """
        self.embedding_engine = embedding_engine
        self.logger = logger
        
        # Load English stop words
        self.stop_words = set(stopwords.words('english'))
    
    def process_query(self, query: str) -> np.ndarray:
        """Process and embed a user query.
        
        This method validates the query and generates a vector embedding.
        For semantic search with embeddings, we preserve the full query
        to maintain semantic meaning.
        
        Args:
            query: User's question as a string
            
        Returns:
            Numpy array containing the query embedding vector
            
        Raises:
            ValueError: If query is empty or whitespace-only
            Exception: If embedding generation fails
        """
        # Validate non-empty query
        if not query or not query.strip():
            self.logger.error("Received empty or whitespace-only query")
            raise ValueError("Query cannot be empty")
        
        self.logger.info(f"Processing query: {query[:100]}...")
        
        # Generate embedding directly from the query
        # No preprocessing needed for semantic search
        try:
            query_embedding = self.embedding_engine.embed_text(query)
            self.logger.info(
                f"Successfully generated query embedding of dimension {len(query_embedding)}"
            )
            return query_embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate query embedding: {str(e)}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """Normalize and clean query text.
        
        This method:
        1. Removes punctuation (?, !, ., etc.)
        2. Removes stop words (what, is, the, etc.)
        3. Normalizes whitespace
        
        Example: "What is OpenStax?" -> "OpenStax"
        
        Args:
            text: Raw query text
            
        Returns:
            Preprocessed query text with stop words and punctuation removed
        """
        original_text = text
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        self.logger.info(f"After removing punctuation: '{text}'")
        
        # Tokenize and remove stop words
        words = text.split()
        self.logger.info(f"Words before filtering: {words}")
        
        filtered_words = [word for word in words if word.lower() not in self.stop_words]
        self.logger.info(f"Words after filtering stop words: {filtered_words}")
        
        # Join back together
        text = ' '.join(filtered_words)
        
        # Normalize internal whitespace (in case of multiple spaces)
        text = ' '.join(text.split())
        
        self.logger.info(f"Final preprocessed: '{original_text}' -> '{text}'")
        
        return text
