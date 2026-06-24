"""OCR Engine for scanned document processing."""
from typing import Dict, Any, List
import io
import numpy as np
from PIL import Image
try:
    import pytesseract
except ImportError:
    pytesseract = None
from PyPDF2 import PdfReader
import pdfplumber


class OCREngine:
    """Engine for OCR (Optical Character Recognition) on scanned documents."""
    
    _reader = None
    
    @classmethod
    def get_easyocr_reader(cls):
        """Get or initialize EasyOCR reader."""
        if cls._reader is None:
            try:
                import easyocr
                cls._reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            except ImportError:
                print("EasyOCR not installed. OCR disabled.")
                return None
            except Exception as e:
                print(f"EasyOCR initialization failed: {e}")
                cls._reader = "unavailable"
        return cls._reader if cls._reader != "unavailable" else None

    @staticmethod
    def extract_text_from_image(image_bytes: bytes) -> str:
        """Extract text from an image using Tesseract OCR."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            return f"OCR Error: {str(e)}"

    @staticmethod
    def extract_text_from_image_pdf(pdf_content: bytes) -> str:
        """
        Extract text from a scanned PDF (image-based PDF).
        
        Args:
            pdf_content: PDF file as bytes
        
        Returns:
            Extracted text from all pages
        """
        all_text = []
        
        try:
            # Try pdfplumber first
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for i, page in enumerate(pdf.pages):
                    # Check if page has text
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        all_text.append(page_text)
                    else:
                        # Page might be an image - need OCR
                        try:
                            # Convert page to image
                            from pdf2image import convert_from_bytes
                            images = convert_from_bytes(pdf_content, first_page=i+1, last_page=i+1)
                            for img in images:
                                img_bytes = io.BytesIO()
                                img.save(img_bytes, format='PNG')
                                ocr_text = OCREngine.extract_text_from_image(img_bytes.getvalue())
                                if ocr_text.strip():
                                    all_text.append(f"[Page {i+1} - OCR]\n{ocr_text}")
                        except Exception as e:
                            # Fallback to PyPDF2 images
                            try:
                                reader = PdfReader(io.BytesIO(pdf_content))
                                page = reader.pages[i]
                                if '/XObject' in page['/Resources']:
                                    # Has images but couldn't extract
                                    pass
                            except:
                                pass
        except Exception as e:
            # Fallback to PyPDF2
            try:
                reader = PdfReader(io.BytesIO(pdf_content))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
            except Exception as e2:
                return f"PDF Processing Error: {str(e2)}"
        
        return "\n\n".join(all_text)

    @staticmethod
    def detect_if_scanned(pdf_content: bytes) -> bool:
        """
        Detect if a PDF is a scanned document (image-based).
        
        Returns:
            True if the PDF appears to be scanned
        """
        try:
            reader = PdfReader(io.BytesIO(pdf_content))
            for page in reader.pages:
                text = page.extract_text()
                if text and len(text.strip()) > 50:
                    return False  # Has actual text, not scanned
            return True  # No text found, likely scanned
        except:
            return True

    @staticmethod
    def extract_with_easyocr(image_bytes: bytes) -> str:
        """Extract text using EasyOCR (better for complex images)."""
        reader = OCREngine.get_easyocr_reader()
        if reader is None:
            return OCREngine.extract_text_from_image(image_bytes)
        
        try:
            results = reader.readtext(image_bytes)
            text = " ".join([result[1] for result in results])
            return text
        except Exception as e:
            return f"EasyOCR Error: {str(e)}"