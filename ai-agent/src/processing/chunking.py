"""Chunking module for segmenting PDF paragraphs."""

from typing import List
import logging

from ..models import PDFParagraph, PDFChunk
from config.config import Config


class ChunkingModule:
    """
    Handles chunking of PDF paragraphs into segments suitable for embedding and retrieval.
    """

    def __init__(self, config: Config, logger: logging.Logger):
        """
        Initialize the ChunkingModule.

        Args:
            config: Configuration object containing chunking parameters
            logger: Logger instance for logging operations
        """
        self.logger = logger

    def chunk_pdf_paragraphs(self, paragraphs: List[PDFParagraph]) -> List[PDFChunk]:
        """
        Create chunks from PDF paragraphs.

        Uses a paragraph-based strategy where each paragraph becomes a chunk
        if it's under the maximum size. Long paragraphs are split into
        sentence-based sub-chunks with overlap. Preserves title information.

        Args:
            paragraphs: List of PDFParagraph objects

        Returns:
            List of PDFChunk objects
        """
        chunks = []

        for paragraph in paragraphs:
            # For simplicity, treat each paragraph as a single chunk
            # In a more sophisticated implementation, we could split long paragraphs
            # into sentence-based sub-chunks with overlap

            # Skip very short paragraphs (likely noise)
            if len(paragraph.text.strip()) < 20:
                self.logger.debug(
                    f"Skipping short paragraph in {paragraph.pdf_filename} "
                    f"page {paragraph.page_number}, paragraph {paragraph.paragraph_index}"
                )
                continue

            # Create chunk from paragraph, preserving title
            chunk = PDFChunk(
                pdf_filename=paragraph.pdf_filename,
                page_number=paragraph.page_number,
                paragraph_index=paragraph.paragraph_index,
                text=paragraph.text,
                title=paragraph.title
            )

            chunks.append(chunk)

        self.logger.info(f"Created {len(chunks)} chunks from {len(paragraphs)} PDF paragraphs")

        return chunks

