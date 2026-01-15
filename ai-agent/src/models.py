"""Data models for the RAG Chatbot Backend."""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import json


@dataclass
class PDFParagraph:
    """Represents a paragraph extracted from a PDF."""
    pdf_filename: str
    page_number: int
    paragraph_index: int
    text: str
    title: Optional[str] = None  # Section title/heading for this chunk

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFParagraph':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class PDFChunk:
    """Represents a chunk of PDF content for embedding."""
    pdf_filename: str
    page_number: int
    paragraph_index: int
    text: str
    title: Optional[str] = None  # Section title/heading for this chunk

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFChunk':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class PDFResult:
    """Represents a PDF-based retrieval result."""
    pdf_filename: str
    page_number: int
    paragraph_index: int
    source_snippet: str
    score: float
    document_id: str = ""
    title: Optional[str] = None  # Section title/heading for this result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFResult':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class PDFResponse:
    """Represents a PDF-based answer response."""
    answer_type: str = "pdf"
    pdf_filename: str = ""
    page_number: int = 0
    paragraph_index: int = 0
    source_snippet: str = ""
    generated_answer: str = ""
    score: float = 0.0
    document_id: str = ""
    title: Optional[str] = None  # Section title/heading for this response
    all_sources: Optional[List[Dict[str, Any]]] = None  # All sources considered by LLM
    selected_source_index: int = 0  # Which source was selected (0-indexed)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFResponse':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class NoAnswerResponse:
    """Represents a no-answer response with knowledge summary."""
    answer_type: str = "no_answer"
    message: str = "No relevant answer found in the knowledge base."
    knowledge_summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NoAnswerResponse':
        """Create from dictionary."""
        return cls(**data)
