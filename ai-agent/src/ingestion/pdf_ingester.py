"""PDF document ingestion module using PyMuPDF library.

This module extracts all elements per page and groups them into semantic chunks:
- Hierarchical structure preservation (sections → paragraphs)
- Optimal chunk sizes (512-1024 tokens)
- Title context maintained with content
- Chunk overlap for context continuity
- OCR extraction from embedded images
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict
import io
import fitz  # PyMuPDF
import tiktoken

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from ..models import PDFParagraph
from config.config import Config


class PDFIngester:
    """
    Ingests and processes PDF documents using PyMuPDF library.
    
    Features:
    - Extracts text blocks per page with font information
    - Groups content into semantic chunks (512-1024 tokens)
    - Detects titles based on font size and formatting
    - Adds overlap between chunks for context continuity
    - Optimized for RAG retrieval quality
    """
    
    def __init__(self, config: Config, logger: Optional[logging.Logger] = None):
        """
        Initialize the PDFIngester.
        
        Args:
            config: Configuration object containing PDF directory path
            logger: Logger instance for logging operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.pdf_dir = config.pdf_dir
        
        # Chunking parameters (semantic merging with overlap)
        # IMPROVED: Larger chunks for better context and complete rule descriptions
        self.target_chunk_size = 1024  # tokens per chunk (increased from 512)
        self.max_chunk_size = 1536     # tokens (increased from 768)
        self.chunk_overlap = 256       # tokens overlap (increased from 128)
        self.min_chunk_size = 256      # tokens - minimum viable chunk size
        
        # Paragraph extraction settings
        self.min_block_length = 20     # characters - filter noise blocks
        self.merge_small_blocks = True # Merge adjacent blocks into semantic chunks
        
        # OCR settings
        self.enable_ocr = OCR_AVAILABLE
        self.ocr_languages = "eng+deu"  # English and German
        
        if self.enable_ocr:
            self.logger.info("✅ OCR enabled (PIL + pytesseract available)")
            self.logger.info(f"   OCR languages: {self.ocr_languages}")
        else:
            self.logger.warning("⚠️ OCR disabled (PIL or pytesseract not available)")
            self.logger.warning("   Images in PDFs will not be processed")
            self.logger.warning("   Install: pip install Pillow pytesseract")
            self.logger.warning("   System: apt-get install tesseract-ocr")
        
        # Initialize tokenizer for accurate token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        except Exception as e:
            self.logger.warning(f"Failed to load tiktoken, using character approximation: {e}")
            self.tokenizer = None
    
    
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken or character approximation.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximation: ~4 characters per token
            return len(text) // 4
    
    def ingest_directory(self, directory: Optional[Path] = None) -> List[PDFParagraph]:
        """
        Ingest all PDF files from the specified directory.
        
        Args:
            directory: Directory path to ingest from. If None, uses config.pdf_dir
            
        Returns:
            List of PDFParagraph objects extracted from all PDFs
        """
        target_dir = directory or self.pdf_dir
        
        if not target_dir.exists():
            self.logger.error(f"PDF directory does not exist: {target_dir}")
            return []
        
        if not target_dir.is_dir():
            self.logger.error(f"PDF path is not a directory: {target_dir}")
            return []
        
        all_paragraphs = []
        pdf_files = list(target_dir.glob("*.pdf"))
        
        self.logger.info(f"Found {len(pdf_files)} PDF files in {target_dir}")
        
        for pdf_file in pdf_files:
            paragraphs = self.ingest_file(pdf_file)
            if paragraphs:
                all_paragraphs.extend(paragraphs)
                self.logger.info(f"Extracted {len(paragraphs)} chunks from {pdf_file.name}")
        
        self.logger.info(f"Successfully extracted {len(all_paragraphs)} total chunks from {len(pdf_files)} PDF files")
        return all_paragraphs
    
    def ingest_file(self, file_path: Path) -> List[PDFParagraph]:
        """
        Extract semantic chunks from a single PDF file using PyMuPDF.
        
        This method:
        1. Extracts text blocks with font information using PyMuPDF
        2. Detects titles based on font size
        3. Extracts images and performs OCR
        4. Creates semantic chunks (512-1024 tokens)
        5. Preserves title hierarchy
        6. Adds overlap between chunks
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of PDFParagraph objects (semantic chunks)
        """
        paragraphs = []
        
        try:
            self.logger.info(f"Parsing PDF with PyMuPDF: {file_path.name}")
            
            # Open PDF with PyMuPDF
            doc = fitz.open(str(file_path))
            self.logger.info(f"Opened PDF with {len(doc)} pages")
            
            # Process each page and create semantic chunks
            total_chunks_created = 0
            total_image_chunks = 0
            pages_with_no_chunks = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text blocks with font information
                blocks = self._extract_blocks_from_page(page)
                
                # Extract images and perform OCR
                image_chunks = []
                if self.enable_ocr:
                    image_chunks = self._extract_images_from_page(
                        doc, 
                        page_num, 
                        file_path.name
                    )
                    if image_chunks:
                        total_image_chunks += len(image_chunks)
                        self.logger.debug(
                            f"Page {page_num + 1}: Extracted {len(image_chunks)} image chunks via OCR"
                        )
                
                if not blocks and not image_chunks:
                    pages_with_no_chunks.append(page_num + 1)
                    continue
                
                # Create semantic chunks from text blocks (paragraph index resets per page)
                # Note: page_num is 0-indexed (PyMuPDF), we convert to 1-indexed for storage
                page_chunks = self._create_semantic_chunks(
                    file_path.name,
                    page_num + 1,  # Physical page number (1-indexed)
                    blocks,
                    start_index=0  # Reset to 0 for each page
                )
                
                # Add image chunks after text chunks
                # Note: Image chunks are kept separate (not merged) as they represent distinct visual content
                for img_chunk in image_chunks:
                    # Adjust paragraph index to continue from text chunks
                    img_chunk.paragraph_index = len(page_chunks)
                    page_chunks.append(img_chunk)
                
                if page_chunks:
                    self.logger.debug(
                        f"Page {page_num + 1}: Created {len(page_chunks)} total chunks "
                        f"({len(page_chunks) - len(image_chunks)} text, {len(image_chunks)} images)"
                    )
                
                if not page_chunks:
                    pages_with_no_chunks.append(page_num + 1)
                
                paragraphs.extend(page_chunks)
                total_chunks_created += len(page_chunks)
                
                # Log every 50 pages
                if (page_num + 1) % 50 == 0:
                    self.logger.info(
                        f"Progress: Page {page_num + 1}/{len(doc)} - "
                        f"Created {total_chunks_created} chunks so far ({total_image_chunks} from images)"
                    )
            
            doc.close()
            
            if pages_with_no_chunks:
                self.logger.warning(
                    f"Pages with no chunks: {len(pages_with_no_chunks)} pages "
                    f"(e.g., {pages_with_no_chunks[:10]})"
                )
            
            if not paragraphs:
                self.logger.warning(f"No chunks created from {file_path.name}")
            else:
                # Calculate statistics
                total_tokens = sum(self._count_tokens(p.text) for p in paragraphs)
                avg_tokens = total_tokens / len(paragraphs) if paragraphs else 0
                chunks_with_titles = sum(1 for p in paragraphs if p.title)
                
                self.logger.info(
                    f"Successfully created {len(paragraphs)} semantic chunks from {file_path.name}"
                )
                self.logger.info(
                    f"  Text chunks: {len(paragraphs) - total_image_chunks}"
                )
                self.logger.info(
                    f"  Image chunks (OCR): {total_image_chunks}"
                )
                self.logger.info(
                    f"  Average chunk size: {avg_tokens:.0f} tokens"
                )
                self.logger.info(
                    f"  Chunks with titles: {chunks_with_titles}/{len(paragraphs)} "
                    f"({chunks_with_titles/len(paragraphs)*100:.1f}%)"
                )
            
            return paragraphs
            
        except FileNotFoundError:
            self.logger.error(f"PDF file not found: {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing PDF file {file_path}: {e}")
            self.logger.exception("Full traceback:")
            return []
    
    def _extract_blocks_from_page(self, page) -> List[Dict]:
        """
        Extract text blocks from a page with font information.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            List of block dictionaries with 'text', 'font_size', and 'is_title' keys
        """
        blocks = []
        
        # Get text blocks with detailed information
        text_dict = page.get_text("dict")
        
        # Calculate average font size for title detection
        font_sizes = []
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_sizes.append(span.get("size", 0))
        
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
        title_threshold = avg_font_size * 1.15  # 15% larger than average (more sensitive)
        
        self.logger.debug(
            f"Page {page.number + 1}: avg_font_size={avg_font_size:.1f}, "
            f"title_threshold={title_threshold:.1f}"
        )
        
        # Extract blocks with title detection
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                block_text = ""
                max_font_size = 0
                
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                        max_font_size = max(max_font_size, span.get("size", 0))
                    block_text += line_text + " "
                
                block_text = block_text.strip()
                if block_text:  # Keep all blocks, including potential titles
                    is_likely_title = (
                        max_font_size >= title_threshold and 
                        len(block_text) < 200 and  # Titles are usually short
                        not block_text.endswith('.')  # Titles often don't end with period
                    )
                    blocks.append({
                        "text": block_text,
                        "font_size": max_font_size,
                        "is_title": is_likely_title
                    })
        
        return blocks
    
    
    def _create_semantic_chunks(
        self,
        pdf_filename: str,
        page_num: int,
        blocks: List[Dict],
        start_index: int
    ) -> List[PDFParagraph]:
        """
        Create chunks from page blocks - SEMANTIC MERGING with sliding window.
        
        Strategy for better context:
        1. Merge adjacent small blocks into semantic chunks (target: 512-1024 tokens)
        2. Preserve title context with merged content
        3. Split oversized chunks with overlap
        4. Ensure minimum chunk size for meaningful context
        
        Args:
            pdf_filename: Name of the PDF file
            page_num: Page number
            blocks: List of block dictionaries from PyMuPDF
            start_index: Starting paragraph index
            
        Returns:
            List of PDFParagraph objects with better semantic context
        """
        chunks = []
        current_title = None
        paragraph_index = start_index
        
        # Filter and categorize blocks
        content_blocks = []
        for block in blocks:
            text = block["text"].strip()
            is_title = block["is_title"]
            
            # Skip empty or very short blocks
            if not text or len(text) < self.min_block_length:
                continue
            
            # Handle title blocks - update current title context
            if is_title:
                current_title = text
                self.logger.debug(f"Detected title: '{text[:100]}...' (font_size={block['font_size']:.1f})")
                continue
            
            # Collect content blocks for merging
            content_blocks.append(text)
        
        if not content_blocks:
            return chunks
        
        # Merge blocks into semantic chunks
        if self.merge_small_blocks:
            merged_chunks = self._merge_blocks_into_chunks(content_blocks)
        else:
            merged_chunks = content_blocks
        
        # Create PDFParagraph objects from merged chunks
        for chunk_text in merged_chunks:
            text_tokens = self._count_tokens(chunk_text)
            
            # If chunk is within size limits, use it directly
            if text_tokens <= self.max_chunk_size:
                chunks.append(PDFParagraph(
                    pdf_filename=pdf_filename,
                    page_number=page_num,
                    paragraph_index=paragraph_index,
                    text=chunk_text,
                    title=current_title,
                    content_type="text"  # Explicitly mark as text content
                ))
                paragraph_index += 1
            else:
                # Oversized chunk - split with overlap
                sub_chunks = self._split_long_paragraph(chunk_text)
                for sub_text in sub_chunks:
                    chunks.append(PDFParagraph(
                        pdf_filename=pdf_filename,
                        page_number=page_num,
                        paragraph_index=paragraph_index,
                        text=sub_text,
                        title=current_title,
                        content_type="text"  # Explicitly mark as text content
                    ))
                    paragraph_index += 1
        
        return chunks
    
    def _merge_blocks_into_chunks(self, blocks: List[str]) -> List[str]:
        """
        Merge adjacent blocks into semantic chunks of target size.
        
        Strategy:
        - Accumulate blocks until reaching target_chunk_size
        - Ensure minimum chunk size for context
        - Add overlap between chunks for continuity
        
        Args:
            blocks: List of text blocks to merge
            
        Returns:
            List of merged chunk texts
        """
        if not blocks:
            return []
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for block in blocks:
            block_tokens = self._count_tokens(block)
            
            # If adding this block would exceed max size, finalize current chunk
            if current_tokens > 0 and current_tokens + block_tokens > self.target_chunk_size:
                # Finalize current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap from previous chunk
                overlap_text = self._get_overlap_from_text(chunk_text, self.chunk_overlap)
                if overlap_text:
                    current_chunk = [overlap_text, block]
                    current_tokens = self._count_tokens(overlap_text) + block_tokens
                else:
                    current_chunk = [block]
                    current_tokens = block_tokens
            else:
                # Add block to current chunk
                current_chunk.append(block)
                current_tokens += block_tokens
        
        # Add final chunk if it exists
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            # Only add if it meets minimum size (unless it's the only chunk)
            if len(chunks) == 0 or self._count_tokens(chunk_text) >= self.min_chunk_size:
                chunks.append(chunk_text)
            else:
                # Merge with previous chunk if too small
                if chunks:
                    chunks[-1] = chunks[-1] + ' ' + chunk_text
        
        return chunks
    
    def _get_overlap_from_text(self, text: str, overlap_tokens: int) -> str:
        """
        Extract the last N tokens from text for overlap.
        
        Args:
            text: Source text
            overlap_tokens: Number of tokens to extract
            
        Returns:
            Overlap text (last N tokens)
        """
        if not text or overlap_tokens <= 0:
            return ""
        
        if self.tokenizer:
            tokens = self.tokenizer.encode(text)
            if len(tokens) <= overlap_tokens:
                return text
            
            overlap_tokens_list = tokens[-overlap_tokens:]
            return self.tokenizer.decode(overlap_tokens_list)
        else:
            # Fallback: character-based approximation
            overlap_chars = overlap_tokens * 4
            if len(text) <= overlap_chars:
                return text
            return text[-overlap_chars:]
    
    def _split_long_paragraph(self, text: str) -> List[str]:
        """
        Split a long paragraph into overlapping chunks.
        
        Uses sliding window approach to ensure no content is lost.
        
        Args:
            text: Long paragraph text
            
        Returns:
            List of text chunks with overlap
        """
        if not self.tokenizer:
            # Fallback: split by characters with overlap
            chunks = []
            chunk_chars = self.target_chunk_size * 4  # ~4 chars per token
            overlap_chars = self.chunk_overlap * 4
            
            start = 0
            while start < len(text):
                end = start + chunk_chars
                chunk = text[start:end]
                
                # Try to break at sentence boundary
                if end < len(text):
                    last_period = chunk.rfind('. ')
                    if last_period > len(chunk) // 2:  # Only if in second half
                        chunk = chunk[:last_period + 1]
                
                chunks.append(chunk.strip())
                start += chunk_chars - overlap_chars
            
            return chunks
        
        # Use tokenizer for accurate splitting
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        start = 0
        while start < len(tokens):
            end = start + self.target_chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text.strip())
            
            # Move forward with overlap
            start += self.target_chunk_size - self.chunk_overlap
        
        return chunks
    
    def _extract_images_from_page(
        self, 
        pdf_doc, 
        page_number: int, 
        pdf_filename: str
    ) -> List[PDFParagraph]:
        """
        Extract all images from a given page in the PDF and perform OCR on each one.
        
        Creates a separate chunk for each image with OCR text.
        
        Args:
            pdf_doc: PyMuPDF document object
            page_number: Page number (0-indexed)
            pdf_filename: Name of the PDF file
            
        Returns:
            List of PDFParagraph objects containing OCR text from images
        """
        if not self.enable_ocr:
            return []
        
        image_chunks = []
        page = pdf_doc[page_number]
        
        try:
            # Get a list of all image objects on the page
            image_list = page.get_images(full=True)
            
            if not image_list:
                return []
            
            self.logger.debug(f"Page {page_number + 1}: Found {len(image_list)} images")
            
            for img_index, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]
                    
                    # Extract image data based on its cross-reference (xref)
                    base_image = pdf_doc.extract_image(xref)
                    img_bytes = base_image.get("image")
                    
                    if not img_bytes:
                        continue
                    
                    # Convert bytes to a PIL Image object
                    img = Image.open(io.BytesIO(img_bytes))
                    
                    # Perform OCR on the image
                    ocr_text = pytesseract.image_to_string(img, lang=self.ocr_languages)
                    
                    if ocr_text.strip():
                        # Create a chunk for this image
                        # Use "Image N" as the title/metadata instead of paragraph index
                        image_chunk = PDFParagraph(
                            pdf_filename=pdf_filename,
                            page_number=page_number + 1,  # Convert to 1-indexed
                            paragraph_index=img_index,  # Use image index
                            text=ocr_text.strip(),
                            title=f"Image {img_index + 1}",  # Metadata: "Image 1", "Image 2", etc.
                            content_type="image"  # Mark as image content
                        )
                        
                        image_chunks.append(image_chunk)
                        
                        self.logger.debug(
                            f"Page {page_number + 1}, Image {img_index + 1}: "
                            f"Extracted {len(ocr_text.strip())} characters via OCR"
                        )
                
                except Exception as e:
                    self.logger.warning(
                        f"Failed to extract/OCR image {img_index + 1} on page {page_number + 1}: {e}"
                    )
                    continue
        
        except Exception as e:
            self.logger.error(
                f"Image extraction/OCR failed on page {page_number + 1}: {e}"
            )
            return []
        
        return image_chunks

