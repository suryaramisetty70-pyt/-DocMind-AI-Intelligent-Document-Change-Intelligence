"""
DocMind AI - Base Document Parser
Abstract base class for all document parsers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import hashlib
from datetime import datetime


@dataclass
class DocumentMetadata:
    """Metadata extracted from a document"""
    filename: str
    file_type: str
    file_size: int
    page_count: Optional[int] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentElement:
    """Represents a structural element in a document"""
    element_type: str  # paragraph, table, image, header, footer, etc.
    content: str
    page_number: int = 0
    section: Optional[str] = None
    position: Tuple[float, float, float, float] = (0, 0, 0, 0)  # x1, y1, x2, y2
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class DocumentContent:
    """Complete extracted content from a document"""
    metadata: DocumentMetadata
    text_content: str
    elements: List[DocumentElement] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    structure: Dict[str, Any] = field(default_factory=dict)
    
    def get_word_count(self) -> int:
        """Get total word count"""
        return len(self.text_content.split())
    
    def get_page_count(self) -> int:
        """Get page count"""
        return self.metadata.page_count or 1
    
    def get_summary(self) -> str:
        """Get document summary"""
        return f"Document: {self.metadata.filename}\nPages: {self.get_page_count()}\nWords: {self.get_word_count()}\nElements: {len(self.elements)}"


class BaseDocumentParser(ABC):
    """Abstract base class for document parsers"""
    
    SUPPORTED_EXTENSIONS: List[str] = []
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def parse(self, file_path: Path) -> DocumentContent:
        """Parse a document and return structured content"""
        pass
    
    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """Extract raw text from a document"""
        pass
    
    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """Extract document metadata"""
        stat = file_path.stat()
        return DocumentMetadata(
            filename=file_path.name,
            file_type=file_path.suffix[1:],
            file_size=stat.st_size,
            modified_date=datetime.fromtimestamp(stat.st_mtime)
        )
    
    def calculate_hash(self, file_path: Path) -> str:
        """Calculate file hash for comparison"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate if file can be processed"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix[1:].lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        return True
    
    def preprocess(self, file_path: Path) -> Any:
        """Preprocess file before parsing"""
        return file_path


class DocumentParserFactory:
    """Factory for creating document parsers"""
    
    _parsers: Dict[str, type] = {}
    
    @classmethod
    def register(cls, extensions: List[str], parser_class: type):
        """Register a parser for specific extensions"""
        for ext in extensions:
            cls._parsers[ext.lower()] = parser_class
    
    @classmethod
    def get_parser(cls, file_path: Path) -> BaseDocumentParser:
        """Get appropriate parser for a file"""
        ext = file_path.suffix[1:].lower()
        
        if ext not in cls._parsers:
            raise ValueError(f"No parser registered for: {ext}")
        
        return cls._parsers[ext]()
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of all supported extensions"""
        return list(cls._parsers.keys())