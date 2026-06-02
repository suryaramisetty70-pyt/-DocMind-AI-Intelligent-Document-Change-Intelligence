"""
DocMind AI - Text Parser
Handles plain text, CSV, and markdown documents
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import csv
from io import StringIO

from .base_parser import (
    BaseDocumentParser,
    DocumentContent,
    DocumentMetadata,
    DocumentElement,
    DocumentParserFactory
)


class TextParser(BaseDocumentParser):
    """Parser for plain text documents"""
    
    SUPPORTED_EXTENSIONS = ["txt", "md", "rst", "log"]
    
    def __init__(self):
        super().__init__()
        self.encoding = "utf-8"
        self.fallback_encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    
    def parse(self, file_path: Path) -> DocumentContent:
        """Parse text file and extract structured content"""
        self.validate_file(file_path)
        
        metadata = self.extract_metadata(file_path)
        text_content = self.extract_text(file_path)
        elements = self._extract_elements(text_content)
        structure = self._analyze_structure(elements)
        
        return DocumentContent(
            metadata=metadata,
            text_content=text_content,
            elements=elements,
            tables=[],
            images=[],
            structure=structure
        )
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from file with encoding detection"""
        for encoding in self.fallback_encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # Last resort: read as binary and decode with errors='ignore'
        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore')
    
    def _extract_elements(self, text: str) -> List[DocumentElement]:
        """Extract structured elements from text"""
        elements = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            element_type = self._detect_line_type(line)
            
            element = DocumentElement(
                element_type=element_type,
                content=line,
                page_number=1,
                attributes={
                    "line_number": line_num
                }
            )
            elements.append(element)
        
        return elements
    
    def _detect_line_type(self, line: str) -> str:
        """Detect the type of a line"""
        stripped = line.strip()
        
        if not stripped:
            return "blank"
        
        # Markdown headers
        if stripped.startswith('#'):
            return "header"
        
        # Numbered list
        if re.match(r'^\d+\.', stripped):
            return "list_item"
        
        # Bullet list
        if stripped.startswith(('-', '*', '•')):
            return "list_item"
        
        # Code block markers
        if stripped.startswith('```'):
            return "code_block"
        
        # Table separator
        if re.match(r'^[\|\-]+$', stripped):
            return "table_separator"
        
        # Table row
        if stripped.startswith('|'):
            return "table_row"
        
        return "paragraph"
    
    def _analyze_structure(self, elements: List[DocumentElement]) -> Dict[str, Any]:
        """Analyze text document structure"""
        structure = {
            "total_lines": len(elements),
            "paragraphs": len([e for e in elements if e.element_type == "paragraph"]),
            "headers": len([e for e in elements if e.element_type == "header"]),
            "lists": len([e for e in elements if e.element_type == "list_item"]),
            "code_blocks": len([e for e in elements if e.element_type == "code_block"]),
            "tables": len([e for e in elements if e.element_type in ["table_row", "table_separator"]]),
            "sections": []
        }
        
        # Extract section hierarchy from headers
        current_section = None
        for element in elements:
            if element.element_type == "header":
                # Count header level
                level = len(element.content) - len(element.content.lstrip('#'))
                header_text = element.content.lstrip('#').strip()
                
                section = {
                    "level": level,
                    "title": header_text,
                    "line": element.attributes.get("line_number", 0)
                }
                structure["sections"].append(section)
                
                if level == 1:
                    current_section = header_text
        
        return structure


class CSVParser(BaseDocumentParser):
    """Parser for CSV files"""
    
    SUPPORTED_EXTENSIONS = ["csv", "tsv"]
    
    def __init__(self):
        super().__init__()
        self.delimiter = ','
        self.encoding = "utf-8"
    
    def parse(self, file_path: Path) -> DocumentContent:
        """Parse CSV file"""
        self.validate_file(file_path)
        
        metadata = self.extract_metadata(file_path)
        text_content = self.extract_text(file_path)
        elements = self._extract_elements(file_path)
        tables = self._extract_tables(file_path)
        structure = self._analyze_structure(file_path)
        
        return DocumentContent(
            metadata=metadata,
            text_content=text_content,
            elements=elements,
            tables=tables,
            images=[],
            structure=structure
        )
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from CSV"""
        lines = []
        
        # Detect delimiter
        with open(file_path, 'r', encoding=self.encoding, newline='') as f:
            sample = f.read(4096)
            f.seek(0)
            
            try:
                dialect = csv.Sniffer().sniff(sample)
                self.delimiter = dialect.delimiter
            except csv.Error:
                pass
            
            reader = csv.reader(f, delimiter=self.delimiter)
            for row in reader:
                lines.append(self.delimiter.join(str(cell) for cell in row))
        
        return '\n'.join(lines)
    
    def _extract_elements(self, file_path: Path) -> List[DocumentElement]:
        """Extract structured elements from CSV"""
        elements = []
        
        with open(file_path, 'r', encoding=self.encoding, newline='') as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            
            for row_num, row in enumerate(reader, 1):
                for col_name, value in row.items():
                    element = DocumentElement(
                        element_type="cell",
                        content=str(value),
                        page_number=1,
                        attributes={
                            "column": col_name,
                            "row": row_num
                        }
                    )
                    elements.append(element)
        
        return elements
    
    def _extract_tables(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract tables from CSV"""
        tables = []
        
        with open(file_path, 'r', encoding=self.encoding, newline='') as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            
            rows = []
            headers = None
            
            for row in reader:
                if headers is None:
                    headers = list(row.keys())
                rows.append(list(row.values()))
            
            if headers and rows:
                tables.append({
                    "sheet": "csv_data",
                    "sheet_index": 1,
                    "headers": headers,
                    "data": rows,
                    "rows": len(rows),
                    "columns": len(headers)
                })
        
        return tables
    
    def _analyze_structure(self, file_path: Path) -> Dict[str, Any]:
        """Analyze CSV structure"""
        structure = {
            "total_rows": 0,
            "columns": [],
            "has_header": True,
            "delimiter": self.delimiter
        }
        
        with open(file_path, 'r', encoding=self.encoding, newline='') as f:
            reader = csv.DictReader(f, delimiter=self.delimiter)
            structure["columns"] = reader.fieldnames or []
            structure["total_rows"] = sum(1 for _ in reader)
        
        return structure


class MarkdownParser(TextParser):
    """Enhanced parser for Markdown documents"""
    
    def _detect_line_type(self, line: str) -> str:
        """Detect Markdown-specific line types"""
        stripped = line.strip()
        
        if not stripped:
            return "blank"
        
        # Headers
        if stripped.startswith('#'):
            return "header"
        
        # Horizontal rule
        if re.match(r'^[-*_]{3,}$', stripped):
            return "horizontal_rule"
        
        # Blockquote
        if stripped.startswith('>'):
            return "blockquote"
        
        # Link or image
        if re.match(r'!?\[.*\]\(.*\)', stripped):
            return "link"
        
        return super()._detect_line_type(line)
    
    def _analyze_structure(self, elements: List[DocumentElement]) -> Dict[str, Any]:
        """Analyze Markdown structure with TOC generation"""
        structure = super()._analyze_structure(elements)
        
        # Generate table of contents
        structure["table_of_contents"] = []
        for section in structure.get("sections", []):
            structure["table_of_contents"].append({
                "level": section["level"],
                "title": section["title"],
                "anchor": self._generate_anchor(section["title"])
            })
        
        # Count different elements
        structure["links"] = len([e for e in elements if e.element_type == "link"])
        structure["blockquotes"] = len([e for e in elements if e.element_type == "blockquote"])
        structure["horizontal_rules"] = len([e for e in elements if e.element_type == "horizontal_rule"])
        
        return structure
    
    def _generate_anchor(self, text: str) -> str:
        """Generate anchor for header"""
        anchor = text.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'[\s]+', '-', anchor)
        return anchor


# Register parsers
DocumentParserFactory.register(["txt", "md", "rst", "log"], TextParser)
DocumentParserFactory.register(["csv", "tsv"], CSVParser)
# MarkdownParser is an enhanced TextParser, registered with text extensions