"""
DocMind AI - OCR Module
"""

from .ocr_engine import (
    OCRResult,
    DocumentLayout,
    OCRAnalysis,
    OCRPipeline,
    ImagePreprocessor,
    EasyOCREngine,
    TesseractEngine,
    LayoutAnalyzer,
    SignatureDetector,
    StampDetector,
    TableDetector,
    HandwritingDetector,
    LogoDetector
)

__all__ = [
    "OCRResult",
    "DocumentLayout",
    "OCRAnalysis",
    "OCRPipeline",
    "ImagePreprocessor",
    "EasyOCREngine",
    "TesseractEngine",
    "LayoutAnalyzer",
    "SignatureDetector",
    "StampDetector",
    "TableDetector",
    "HandwritingDetector",
    "LogoDetector"
]