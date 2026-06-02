"""
DocMind AI - Core Module
"""

from .document_processing import (
    BaseDocumentParser,
    DocumentContent,
    DocumentMetadata,
    DocumentElement,
    DocumentParserFactory,
    PDFParser,
    ExcelParser,
    TextParser,
    CSVParser
)

from .comparison import ComparisonEngine, Change, ComparisonResult, ChangeType, ChangeSeverity

from .semantic import SemanticComparisonEngine, SemanticComparisonResult

from .similarity import SimilarityEngine, DocumentSimilarity

from .change_intelligence import ChangeIntelligenceEngine, ChangeIntelligenceReport

from .reporting import (
    ReportGenerator,
    ReportSection,
    PDFReportGenerator,
    ExcelReportGenerator,
    AuditReportGenerator
)

from .ocr import OCRPipeline, OCRResult, DocumentLayout

__all__ = [
    # Document processing
    "BaseDocumentParser",
    "DocumentContent",
    "DocumentMetadata",
    "DocumentElement",
    "DocumentParserFactory",
    "PDFParser",
    "ExcelParser",
    "TextParser",
    "CSVParser",
    
    # Comparison
    "ComparisonEngine",
    "Change",
    "ComparisonResult",
    "ChangeType",
    "ChangeSeverity",
    
    # Semantic
    "SemanticComparisonEngine",
    "SemanticComparisonResult",
    
    # Similarity
    "SimilarityEngine",
    "DocumentSimilarity",
    
    # Change intelligence
    "ChangeIntelligenceEngine",
    "ChangeIntelligenceReport",
    
    # Reporting
    "ReportGenerator",
    "ReportSection",
    "PDFReportGenerator",
    "ExcelReportGenerator",
    "AuditReportGenerator",
    
    # OCR
    "OCRPipeline",
    "OCRResult",
    "DocumentLayout"
]