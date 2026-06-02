"""
DocMind AI - PDF Parser
Handles PDF document parsing with support for text and scanned PDFs
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import io

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pdfplumber = None
    PDFPLUMBER_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    PIL_AVAILABLE = False

from .base_parser import (
    BaseDocumentParser,
    DocumentContent,
    DocumentMetadata,
    DocumentElement,
    DocumentParserFactory
)


class PDFParser(BaseDocumentParser):
    """Parser for PDF documents"""
    
    SUPPORTED_EXTENSIONS = ["pdf"]
    
    def __init__(self):
        super().__init__()
        self.extract_images = True
        self.extract_tables = True
    
    def parse(self, file_path: Path) -> DocumentContent:
        """Parse PDF and extract structured content"""
        self.validate_file(file_path)
        
        metadata = self.extract_metadata(file_path)
        text_content = self.extract_text(file_path)
        elements = self._extract_elements(file_path)
        tables = self._extract_tables(file_path)
        images = self._extract_images(file_path)
        structure = self._analyze_structure(elements)
        
        metadata.page_count = len(elements) if elements else 1
        
        return DocumentContent(
            metadata=metadata,
            text_content=text_content,
            elements=elements,
            tables=tables,
            images=images,
            structure=structure
        )
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from PDF"""
        text_parts = []
        
        if not PDFPLUMBER_AVAILABLE:
            # Try PyPDF2 as fallback
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
            except ImportError:
                return "PDF parsing not available. Install pdfplumber or PyPDF2."
            except Exception:
                return "Failed to parse PDF."
        else:
            try:
                with pdfplumber.open(file_path) as pdf:
                    metadata = pdf.metadata or {}
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"<!-- Page {page_num} -->\n{page_text}")
            except Exception:
                # Fallback to PyPDF2
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                text_parts.append(text)
                except Exception:
                    pass
        
        return "\n\n".join(text_parts) if text_parts else ""
    
    def _extract_elements(self, file_path: Path) -> List[DocumentElement]:
        """Extract structured elements from PDF"""
        elements = []
        
        if not PDFPLUMBER_AVAILABLE:
            return elements
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    words = page.extract_words()
                    
                    for word in words:
                        element = DocumentElement(
                            element_type="text",
                            content=word.get("text", ""),
                            page_number=page_num,
                            position=(word.get("x0", 0), word.get("top", 0), 
                                     word.get("x1", 0), word.get("bottom", 0)),
                            confidence=word.get("confidence", 1.0)
                        )
                        elements.append(element)
                    
                    # Detect tables
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            element = DocumentElement(
                                element_type="table",
                                content=str(table),
                                page_number=page_num
                            )
                            elements.append(element)
        except Exception:
            pass
        
        return elements
    
    def _extract_tables(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract tables from PDF"""
        tables = []
        
        if not PDFPLUMBER_AVAILABLE:
            return tables
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    for idx, table in enumerate(page_tables):
                        tables.append({
                            "page": page_num,
                            "table_index": idx,
                            "data": table,
                            "rows": len(table) if table else 0,
                            "columns": len(table[0]) if table else 0
                        })
        except Exception:
            pass
        
        return tables
    
    def _extract_images(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract images from PDF"""
        images = []
        
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            
            for page_num, page in enumerate(doc, 1):
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    images.append({
                        "page": page_num,
                        "index": img_index,
                        "width": base_image["width"],
                        "height": base_image["height"],
                        "colorspace": base_image["colorspace"],
                        "bpc": base_image["bpc"],
                        "ext": base_image["ext"]
                    })
            
            doc.close()
        except Exception as e:
            pass
        
        return images
    
    def _analyze_structure(self, elements: List[DocumentElement]) -> Dict[str, Any]:
        """Analyze document structure"""
        structure = {
            "total_pages": max([e.page_number for e in elements]) if elements else 1,
            "text_blocks": len([e for e in elements if e.element_type == "text"]),
            "tables": len([e for e in elements if e.element_type == "table"]),
            "headers": [],
            "footers": [],
            "sections": {}
        }
        
        # Analyze for headers/footers
        if elements:
            first_page_elements = [e for e in elements if e.page_number == 1]
            last_page_elements = [e for e in elements if e.page_number == structure["total_pages"]]
            
            if first_page_elements:
                structure["headers"] = [e.content for e in first_page_elements[:5] if e.position[1] < 100]
            if last_page_elements:
                structure["footers"] = [e.content for e in last_page_elements[-5:] if e.position[3] > 700]
        
        return structure
    
    def get_page_text(self, file_path: Path, page_number: int) -> str:
        """Get text from a specific page"""
        with pdfplumber.open(file_path) as pdf:
            if 0 < page_number <= len(pdf.pages):
                return pdf.pages[page_number - 1].extract_text() or ""
        return ""
    
    def get_page_count(self, file_path: Path) -> int:
        """Get total page count"""
        with pdfplumber.open(file_path) as pdf:
            return len(pdf.pages)


class ScannedPDFProcessor:
    """Processor for scanned PDFs using OCR"""
    
    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine
    
    def process(self, file_path: Path, language: str = "en") -> DocumentContent:
        """Process scanned PDF with OCR"""
        import fitz
        
        doc = fitz.open(file_path)
        all_text = []
        elements = []
        
        for page_num, page in enumerate(doc, 1):
            # Render page as image
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Run OCR
            if self.ocr_engine:
                result = self.ocr_engine.read_image(img_data, lang=language)
                page_text = " ".join([line[1] for line in result])
            else:
                page_text = ""
            
            all_text.append(f"<!-- Page {page_num} -->\n{page_text}")
            
            for line in result:
                element = DocumentElement(
                    element_type="text",
                    content=line[1],
                    page_number=page_num,
                    confidence=line[2] if len(line) > 2 else 1.0
                )
                elements.append(element)
        
        doc.close()
        
        metadata = DocumentMetadata(
            filename=file_path.name,
            file_type="pdf",
            file_size=file_path.stat().st_size,
            page_count=len(all_text)
        )
        
        return DocumentContent(
            metadata=metadata,
            text_content="\n\n".join(all_text),
            elements=elements,
            tables=[],
            images=[],
            structure={"scanned": True, "pages": len(all_text)}
        )


# Register parser
DocumentParserFactory.register(["pdf"], PDFParser)