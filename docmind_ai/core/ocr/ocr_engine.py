"""
DocMind AI - OCR Engine
Optical Character Recognition with EasyOCR and Tesseract support
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import io
import base64

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False


@dataclass
class OCRResult:
    """Result from OCR processing"""
    text: str
    confidence: float
    bounding_box: Tuple[int, int, int, int]
    language: str
    block_type: str = "text"


@dataclass
class DocumentLayout:
    """Document layout analysis result"""
    text_regions: List[Dict[str, Any]] = field(default_factory=list)
    table_regions: List[Dict[str, Any]] = field(default_factory=list)
    image_regions: List[Dict[str, Any]] = field(default_factory=list)
    signature_regions: List[Dict[str, Any]] = field(default_factory=list)
    stamp_regions: List[Dict[str, Any]] = field(default_factory=list)
    handwriting_regions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class OCRAnalysis:
    """Complete OCR analysis result"""
    full_text: str
    results: List[OCRResult]
    layout: DocumentLayout
    language: str
    overall_confidence: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ImagePreprocessor:
    """Preprocess images for better OCR accuracy"""
    
    @staticmethod
    def preprocess(image, method: str = "adaptive"):
        """Apply preprocessing to improve OCR results"""
        if image is None:
            return None
        
        if not CV2_AVAILABLE or not cv2:
            return image
        
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            if method == "adaptive":
                processed = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
            elif method == "otsu":
                _, processed = cv2.threshold(
                    gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
            elif method == "binarize":
                _, processed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            else:
                processed = gray
            
            return processed
        except Exception:
            return image
    
    @staticmethod
    def denoise(image):
        """Remove noise from image"""
        if not CV2_AVAILABLE or image is None:
            return image
        try:
            return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        except Exception:
            return image
    
    @staticmethod
    def deskew(image):
        """Deskew the image"""
        if not CV2_AVAILABLE or image is None:
            return image
        try:
            coords = np.column_stack(np.where(image > 0))
            if len(coords) == 0:
                return image
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) < 0.5:
                return image
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rotated
        except Exception:
            return image
    
    @staticmethod
    def remove_borders(image):
        """Remove dark borders from scanned documents"""
        if image is None:
            return image
        try:
            h, w = image.shape[:2]
            crop_h = int(h * 0.02)
            crop_w = int(w * 0.02)
            return image[crop_h:h-crop_h, crop_w:w-crop_w]
        except Exception:
            return image
    
    @staticmethod
    def increase_contrast(image):
        """Increase image contrast"""
        if not CV2_AVAILABLE or image is None:
            return image
        try:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB) if len(image.shape) == 3 else None
            if lab is not None:
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                lab = cv2.merge([l, a, b])
                return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            return image
        except Exception:
            return image


class EasyOCREngine:
    """EasyOCR integration for document text extraction"""
    
    def __init__(self, languages: List[str] = None, gpu: bool = True):
        self.languages = languages or ["en"]
        self.gpu = gpu
        self._reader = None
    
    def _initialize(self):
        """Lazy initialization of OCR reader"""
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(
                    self.languages,
                    gpu=self.gpu,
                    model_storage_directory="./models/easyocr"
                )
            except ImportError:
                raise ImportError("EasyOCR not installed. Run: pip install easyocr")
    
    def read_text(self, image: Union[Any, Path, str]) -> List[OCRResult]:
        """Extract text from image"""
        self._initialize()
        
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))
        
        results = self._reader.readtext(image)
        ocr_results = []
        
        for bbox, text, confidence in results:
            x1, y1 = bbox[0]
            x2, y2 = bbox[2]
            
            ocr_results.append(OCRResult(
                text=text.strip(),
                confidence=confidence,
                bounding_box=(int(x1), int(y1), int(x2), int(y2)),
                language=self.languages[0] if self.languages else "en",
                block_type="text"
            ))
        
        return ocr_results
    
    def read_image(self, image_data: bytes, lang: str = "en") -> List[List]:
        """Read image from bytes data"""
        self._initialize()
        
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if lang != self.languages[0]:
            # Update language if different
            self.languages = [lang]
            self._reader = None
            self._initialize()
        
        results = self._reader.readtext(image)
        return results


class TesseractEngine:
    """Tesseract OCR engine integration"""
    
    def __init__(self, language: str = "eng"):
        self.language = language
        self._config = "--oem 3 --psm 6"
    
    def read_text(self, image: Union[Any, Path, str]) -> List[OCRResult]:
        """Extract text from image using Tesseract"""
        try:
            import pytesseract
        except ImportError:
            raise ImportError("pytesseract not installed. Run: pip install pytesseract")
        
        if isinstance(image, (str, Path)):
            image = cv2.imread(str(image))
        
        # Get detailed data with bounding boxes
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        ocr_results = []
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text:
                conf = float(data['conf'][i]) / 100 if data['conf'][i] != "-1" else 0.5
                
                ocr_results.append(OCRResult(
                    text=text,
                    confidence=conf,
                    bounding_box=(
                        data['left'][i],
                        data['top'][i],
                        data['left'][i] + data['width'][i],
                        data['top'][i] + data['height'][i]
                    ),
                    language=self.language,
                    block_type="text"
                ))
        
        return ocr_results
    
    def get_detailed_data(self, image: Any) -> Dict[str, Any]:
        """Get detailed OCR data including boxes and confidence"""
        import pytesseract
        
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        return data


class LayoutAnalyzer:
    """Analyze document layout to detect different regions"""
    
    def __init__(self):
        self.signature_detector = SignatureDetector()
        self.stamp_detector = StampDetector()
        self.table_detector = TableDetector()
    
    def analyze(self, image: Any) -> DocumentLayout:
        """Analyze document layout"""
        layout = DocumentLayout()
        
        # Detect text regions using connected components
        layout.text_regions = self._detect_text_regions(image)
        
        # Detect tables
        layout.table_regions = self._detect_table_regions(image)
        
        # Detect images
        layout.image_regions = self._detect_image_regions(image)
        
        # Detect signatures
        layout.signature_regions = self.signature_detector.detect(image)
        
        # Detect stamps
        layout.stamp_regions = self.stamp_detector.detect(image)
        
        # Detect handwriting
        layout.handwriting_regions = self._detect_handwriting(image)
        
        return layout
    
    def _detect_text_regions(self, image: Any) -> List[Dict[str, Any]]:
        """Detect text regions in the document"""
        regions = []
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size (text regions should be relatively small and wide)
            if w > 20 and h > 5 and w / h > 2:
                regions.append({
                    "bbox": (x, y, x + w, y + h),
                    "width": w,
                    "height": h,
                    "aspect_ratio": w / h
                })
        
        return regions
    
    def _detect_table_regions(self, image: Any) -> List[Dict[str, Any]]:
        """Detect table regions using line detection"""
        regions = []
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Detect horizontal and vertical lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        
        processed = cv2.dilate(cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1], horizontal_kernel, iterations=2)
        horizontal_lines = cv2.morphologyEx(processed, cv2.MORPH_OPEN, horizontal_kernel)
        
        processed = cv2.dilate(cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1], vertical_kernel, iterations=2)
        vertical_lines = cv2.morphologyEx(processed, cv2.MORPH_OPEN, vertical_kernel)
        
        # Combine horizontal and vertical lines
        table_mask = cv2.add(horizontal_lines, vertical_lines)
        
        # Find contours of detected tables
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 50 and h > 50:
                regions.append({
                    "bbox": (x, y, x + w, y + h),
                    "rows": int(h / 20),
                    "columns": int(w / 30)
                })
        
        return regions
    
    def _detect_image_regions(self, image: Any) -> List[Dict[str, Any]]:
        """Detect image regions"""
        regions = []
        
        # Edge detection
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            if len(approx) == 4 and cv2.contourArea(contour) > 5000:
                x, y, w, h = cv2.boundingRect(approx)
                if 0.3 < w / h < 3:  # Image-like aspect ratio
                    regions.append({
                        "bbox": (x, y, x + w, y + h),
                        "area": cv2.contourArea(contour)
                    })
        
        return regions
    
    def _detect_handwriting(self, image: Any) -> List[Dict[str, Any]]:
        """Detect handwriting regions (simplified detection)"""
        regions = []
        
        # This is a simplified implementation
        # Real handwriting detection would use ML models
        
        return regions


class SignatureDetector:
    """Detect signatures in documents"""
    
    def detect(self, image: Any) -> List[Dict[str, Any]]:
        """Detect signature regions"""
        signatures = []
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Signature detection using heuristics
        # 1. Look for horizontal strokes (signatures often have long horizontal strokes)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
        horizontal = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, horizontal_kernel)
        
        # Find contours
        _, binary = cv2.threshold(horizontal, 50, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Signatures typically have specific characteristics
            if w > 100 and h > 20 and 0.1 < h / w < 0.5 and area > 2000:
                signatures.append({
                    "bbox": (x, y, x + w, y + h),
                    "confidence": 0.7,
                    "type": "signature"
                })
        
        return signatures


class StampDetector:
    """Detect stamps in documents"""
    
    def detect(self, image: Any) -> List[Dict[str, Any]]:
        """Detect stamp regions"""
        stamps = []
        
        if len(image.shape) == 3:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        else:
            hsv = cv2.cvtColor(cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2HSV)
        
        # Detect red/magenta stamps (most common stamp colors)
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red, upper_red)
        
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Morphological operations to clean up
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if area > 500:  # Stamps are typically larger than signatures
                x, y, w, h = cv2.boundingRect(contour)
                circularity = (4 * np.pi * area) / (cv2.arcLength(contour, True) ** 2)
                
                stamps.append({
                    "bbox": (x, y, x + w, y + h),
                    "confidence": 0.8,
                    "type": "stamp",
                    "circularity": circularity
                })
        
        return stamps


class TableDetector:
    """Detect and extract tables from documents"""
    
    def detect(self, image: Any) -> List[Dict[str, Any]]:
        """Detect table regions"""
        tables = []
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Detect horizontal and vertical lines
        horizontal = self._detect_lines(gray, horizontal=True)
        vertical = self._detect_lines(gray, horizontal=False)
        
        # Find intersections (table grid)
        grid = cv2.bitwise_and(horizontal, vertical)
        
        # Find contours of grid cells
        contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            if w > 30 and h > 20:
                tables.append({
                    "bbox": (x, y, x + w, y + h),
                    "rows_estimate": int(h / 25),
                    "columns_estimate": int(w / 60)
                })
        
        return tables
    
    def _detect_lines(self, image: Any, horizontal: bool) -> Any:
        """Detect horizontal or vertical lines"""
        if horizontal:
            structure = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        else:
            structure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        result = cv2.morphologyEx(image, cv2.MORPH_OPEN, structure)
        result = cv2.dilate(result, structure, iterations=2)
        
        return result


class OCRPipeline:
    """Complete OCR pipeline for document processing"""
    
    def __init__(self, engine: str = "easyocr", languages: List[str] = None):
        self.engine_name = engine
        self.languages = languages or ["en"]
        self.preprocessor = ImagePreprocessor()
        self.layout_analyzer = LayoutAnalyzer()
        
        if engine == "easyocr":
            self.engine = EasyOCREngine(languages)
        else:
            self.engine = TesseractEngine(languages[0] if languages else "eng")
    
    def process_document(self, image: Any, preprocess: bool = True) -> OCRAnalysis:
        """Process document with full OCR pipeline"""
        import time
        start_time = time.time()
        
        # Preprocessing
        if preprocess:
            processed = self.preprocessor.preprocess(image)
            processed = self.preprocessor.denoise(processed)
        else:
            processed = image
        
        # Layout analysis
        layout = self.layout_analyzer.analyze(processed)
        
        # Text extraction
        results = self.engine.read_text(processed)
        
        # Calculate overall confidence
        confidences = [r.confidence for r in results]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Combine text
        full_text = " ".join([r.text for r in results])
        
        processing_time = time.time() - start_time
        
        return OCRAnalysis(
            full_text=full_text,
            results=results,
            layout=layout,
            language=self.languages[0] if self.languages else "en",
            overall_confidence=overall_confidence,
            processing_time=processing_time,
            metadata={
                "engine": self.engine_name,
                "preprocessing": preprocess,
                "regions_detected": {
                    "text": len(layout.text_regions),
                    "tables": len(layout.table_regions),
                    "images": len(layout.image_regions),
                    "signatures": len(layout.signature_regions),
                    "stamps": len(layout.stamp_regions)
                }
            }
        )
    
    def process_pdf(self, pdf_path: Path, preprocess: bool = True) -> List[OCRAnalysis]:
        """Process all pages of a PDF"""
        import fitz
        
        analyses = []
        
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Render page as image
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to numpy array
            nparr = np.frombuffer(img_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Process page
            analysis = self.process_document(image, preprocess)
            analyses.append(analysis)
        
        doc.close()
        
        return analyses


class HandwritingDetector:
    """Detect and analyze handwritten content"""
    
    def detect(self, image: Any) -> List[Dict[str, Any]]:
        """Detect handwriting regions"""
        handwriting = []
        
        # This would require a trained model for accurate detection
        # For now, return empty list (placeholder implementation)
        
        return handwriting
    
    def classify_region(self, region: Any) -> str:
        """Classify if a region contains handwriting"""
        # Placeholder for ML-based classification
        return "handwritten" if np.std(region) > 50 else "printed"


class LogoDetector:
    """Detect company logos in documents"""
    
    def detect(self, image: Any) -> List[Dict[str, Any]]:
        """Detect logo regions"""
        logos = []
        
        # Convert to RGB if needed
        if len(image.shape) == 2:
            rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            rgb = image.copy()
        
        # Simple heuristic: logos are typically rectangular and high contrast
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Logos are typically in specific size ranges
            if 1000 < area < 50000 and 0.5 < w / h < 2:
                logos.append({
                    "bbox": (x, y, x + w, y + h),
                    "confidence": 0.6,
                    "type": "logo"
                })
        
        return logos