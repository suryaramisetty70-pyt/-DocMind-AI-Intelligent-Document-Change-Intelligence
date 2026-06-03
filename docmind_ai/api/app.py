"""
DocMind AI - FastAPI Application v3.0
Simple and Working
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


@app.get("/")
async def root():
    return {"name": "DocMind AI", "version": "3.0", "status": "running"}


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/v1/compare")
async def compare_documents(original_file: UploadFile = File(...), modified_file: UploadFile = File(...)):
    """Compare two documents"""
    orig_ext = Path(original_file.filename or "original").suffix.lower()
    mod_ext = Path(modified_file.filename or "modified").suffix.lower()
    
    orig_path = TEMP_DIR / f"orig_{uuid.uuid4()}{orig_ext}"
    mod_path = TEMP_DIR / f"mod_{uuid.uuid4()}{mod_ext}"
    
    try:
        # Save files
        orig_path.write_bytes(original_file.file.read())
        mod_path.write_bytes(modified_file.file.read())
        
        # Read as text (for TXT files)
        try:
            original_text = orig_path.read_text(encoding="utf-8", errors="ignore")
            modified_text = mod_path.read_text(encoding="utf-8", errors="ignore")
        except:
            original_text = orig_path.read_text(encoding="latin-1", errors="ignore")
            modified_text = mod_path.read_text(encoding="latin-1", errors="ignore")
        
        # Compare
        orig_lines = [l.strip() for l in original_text.split("\n") if l.strip()]
        mod_lines = [l.strip() for l in modified_text.split("\n") if l.strip()]
        
        changes = []
        max_lines = max(len(orig_lines), len(mod_lines))
        
        for i in range(max_lines):
            orig_line = orig_lines[i] if i < len(orig_lines) else ""
            mod_line = mod_lines[i] if i < len(mod_lines) else ""
            
            if orig_line != mod_line:
                ctype = "modified"
                if not orig_line:
                    ctype = "insertion"
                elif not mod_line:
                    ctype = "deletion"
                
                changes.append({
                    "change_id": i + 1,
                    "type": ctype,
                    "original_content": orig_line[:200] if orig_line else "(empty)",
                    "modified_content": mod_line[:200] if mod_line else "(empty)",
                    "line_number": i + 1
                })
        
        # Calculate similarity
        matching = 0
        for i in range(min(len(orig_lines), len(mod_lines))):
            if orig_lines[i] == mod_lines[i]:
                matching = matching + 1
        
        total = max(len(orig_lines), len(mod_lines))
        if total == 0:
            total = 1
        
        similarity = round((matching / total) * 100, 2)
        
        return {
            "status": "success",
            "similarity": similarity,
            "total_changes": len(changes),
            "insertions": len([c for c in changes if c["type"] == "insertion"]),
            "deletions": len([c for c in changes if c["type"] == "deletion"]),
            "changes": changes[:30]
        }
    
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if orig_path.exists():
            orig_path.unlink()
        if mod_path.exists():
            mod_path.unlink()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
