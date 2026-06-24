"""PDF comparison engine."""
from typing import Dict, Any, Optional
import io
from PyPDF2 import PdfReader
import pdfplumber


class PDFComparisonEngine:
    """Engine for comparing PDF documents."""

    @staticmethod
    def extract_text_from_pdf(pdf_content: bytes) -> str:
        """Extract text from PDF bytes."""
        text = ""
        try:
            # Try pdfplumber first (better for structured text)
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            # Fallback to PyPDF2
            try:
                reader = PdfReader(io.BytesIO(pdf_content))
                for page in reader.pages:
                    text += page.extract_text() or ""
            except Exception:
                pass
        return text

    @staticmethod
    def compare_pdfs(pdf1_content: bytes, pdf2_content: bytes, ocr_enabled: bool = False) -> Dict[str, Any]:
        """
        Compare two PDF files.
        
        Args:
            pdf1_content: First PDF as bytes
            pdf2_content: Second PDF as bytes
            ocr_enabled: Whether to use OCR for scanned PDFs
        
        Returns:
            Comparison results
        """
        # If OCR is needed, use the OCR engine
        if ocr_enabled:
            from services.ocr_engine import OCREngine
            text1 = OCREngine.extract_text_from_image_pdf(pdf1_content)
            text2 = OCREngine.extract_text_from_image_pdf(pdf2_content)
        else:
            text1 = PDFComparisonEngine.extract_text_from_pdf(pdf1_content)
            text2 = PDFComparisonEngine.extract_text_from_pdf(pdf2_content)
        
        # Get page counts
        try:
            with pdfplumber.open(io.BytesIO(pdf1_content)) as pdf1:
                pages1 = len(pdf1.pages)
            with pdfplumber.open(io.BytesIO(pdf2_content)) as pdf2:
                pages2 = len(pdf2.pages)
        except:
            try:
                reader1 = PdfReader(io.BytesIO(pdf1_content))
                reader2 = PdfReader(io.BytesIO(pdf2_content))
                pages1 = len(reader1.pages)
                pages2 = len(reader2.pages)
            except:
                pages1 = pages2 = 0
        
        # Compare the extracted text
        from services.text_comparison import TextComparisonEngine
        text_result = TextComparisonEngine._compare_word(text1, text2)
        
        return {
            "type": "pdf",
            "pages_file1": pages1,
            "pages_file2": pages2,
            "text_file1": text1[:500] + "..." if len(text1) > 500 else text1,
            "text_file2": text2[:500] + "..." if len(text2) > 500 else text2,
            "full_text1": text1,
            "full_text2": text2,
            "similarity_score": text_result["similarity_score"],
            "total_additions": text_result["total_additions"],
            "total_deletions": text_result["total_deletions"],
            "word_comparison": text_result,
            "ocr_used": ocr_enabled
        }

    @staticmethod
    def get_pdf_metadata(pdf_content: bytes) -> Dict[str, Any]:
        """Extract PDF metadata."""
        metadata = {}
        try:
            reader = PdfReader(io.BytesIO(pdf_content))
            pdf_metadata = reader.metadata
            if pdf_metadata:
                metadata = {
                    "title": pdf_metadata.get("/Title", ""),
                    "author": pdf_metadata.get("/Author", ""),
                    "subject": pdf_metadata.get("/Subject", ""),
                    "creator": pdf_metadata.get("/Creator", ""),
                    "producer": pdf_metadata.get("/Producer", ""),
                    "pages": len(reader.pages)
                }
        except Exception as e:
            metadata["error"] = str(e)
        return metadata