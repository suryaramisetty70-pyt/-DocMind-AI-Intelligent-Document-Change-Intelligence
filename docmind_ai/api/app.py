"""
DocMind AI - FastAPI Application v3.0
Full DOCX, PDF, Excel, TXT Support
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid
from pathlib import Path
import tempfile

app = FastAPI(title="DocMind AI API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = Path(tempfile.gettempdir()) / "docmind_ai"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def extract_text(file_path: Path, file_ext: str) -> str:
    """Extract text from files"""
    
    # TXT files
    if file_ext in ['.txt', '.text']:
        try:
            return file_path.read_text(encoding='utf-8', errors='ignore')
        except:
            return file_path.read_text(encoding='latin-1', errors='ignore')
    
    # DOCX files - USE python-docx!
    elif file_ext == '.docx':
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            return '\n'.join(paragraphs)
        except ImportError:
            return "ERROR: Install python-docx - run: pip install python-docx"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    # PDF files
    elif file_ext == '.pdf':
        try:
            import pdfplumber
            pages_text = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
            return '\n\n'.join(pages_text)
        except ImportError:
            return "ERROR: Install pdfplumber - run: pip install pdfplumber"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    # Excel files
    elif file_ext in ['.xlsx', '.xls']:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            all_content = []
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                sheet_data = [f"Sheet: {sheet_name}"]
                for row in ws.iter_rows(values_only=True):
                    cells = [str(c) if c else '' for c in row]
                    row_text = ' | '.join(cells).strip()
                    if row_text:
                        sheet_data.append(row_text)
                all_content.append('\n'.join(sheet_data))
            return '\n\n'.join(all_content)
        except ImportError:
            return "ERROR: Install openpyxl - run: pip install openpyxl"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    else:
        return f"ERROR: Unsupported file type: {file_ext}"


@app.get("/")
async def root():
    return {"name": "DocMind AI", "version": "3.0", "status": "running"}


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "version": "3.0"}


@app.post("/api/v1/compare")
async def compare_documents(original_file: UploadFile = File(...), modified_file: UploadFile = File(...)):
    orig_ext = Path(original_file.filename or "original").suffix.lower()
    mod_ext = Path(modified_file.filename or "modified").suffix.lower()
    
    orig_path = TEMP_DIR / f"orig_{uuid.uuid4()}{orig_ext}"
    mod_path = TEMP_DIR / f"mod_{uuid.uuid4()}{mod_ext}"
    
    try:
        # Save uploaded files
        orig_path.write_bytes(original_file.file.read())
        mod_path.write_bytes(modified_file.file.read())
        
        # Extract text from files
        original_text = extract_text(orig_path, orig_ext)
        modified_text = extract_text(mod_path, mod_ext)
        
        # Check for errors
        if original_text.startswith("ERROR:"):
            return {"error": f"Original file error: {original_text}"}
        if modified_text.startswith("ERROR:"):
            return {"error": f"Modified file error: {modified_text}"}
        
        # Split into lines for comparison
        orig_lines = [l.strip() for l in original_text.split('\n') if l.strip()]
        mod_lines = [l.strip() for l in modified_text.split('\n') if l.strip()]
        
        # Find changes
        changes = []
        max_lines = max(len(orig_lines), len(mod_lines))
        
        for i in range(max_lines):
            orig_line = orig_lines[i] if i < len(orig_lines) else ""
            mod_line = mod_lines[i] if i < len(mod_lines) else ""
            
            if orig_line != mod_line:
                change_type = "modified"
                if not orig_line:
                    change_type = "insertion"
                elif not mod_line:
                    change_type = "deletion"
                
                changes.append({
                    "change_id": i + 1,
                    "type": change_type,
                    "original_content": orig_line[:200] if orig_line else "(empty)",
                    "modified_content": mod_line[:200] if mod_line else "(empty)",
                    "line_number": i + 1
                })
        
        # Calculate similarity
        matching = sum(1 for i in range(min(len(orig_lines), len(mod_lines))) 
                      if orig_lines[i] == mod_lines[i])
        total = max(len(orig_lines), len(mod_lines)) if max_lines > 0 else 1
        similarity = round((matching / total) * 100, 2) if total > 0 else 100
        
        return {
            "status": "success",
            "message": f"Compared: {original_file.filename} vs {modified_file.filename}",
            "similarity": similarity,
            "total_changes": len(changes),
            "insertions": len([c for c in changes if c['type'] == 'insertion']),
            "deletions": len([c for c in changes if c['type'] == 'deletion']),
            "modifications": len([c for c in changes if c['type'] == 'modified']),
            "changes": changes[:30]
        }
    
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if orig_path.exists(): orig_path.unlink()
        if mod_path.exists(): mod_path.unlink()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
