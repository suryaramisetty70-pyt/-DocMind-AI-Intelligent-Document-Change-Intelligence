"""
DocMind AI - FastAPI Application v3.0
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
    return {"name": "DocMind AI API", "version": "3.0", "status": "running"}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "version": "3.0"}

@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    temp_path = TEMP_DIR / f"upload_{uuid.uuid4()}"
    try:
        content = file.file.read()
        temp_path.write_bytes(content)
        file_ext = Path(file.filename or "file").suffix.lower()
        return {"filename": file.filename, "file_type": file_ext, "status": "uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            temp_path.unlink()

@app.post("/api/v1/compare")
async def compare_documents(original_file: UploadFile = File(...), modified_file: UploadFile = File(...)):
    """Compare two documents"""
    try:
        orig_name = original_file.filename or "original"
        mod_name = modified_file.filename or "modified"
        
        # Read file contents
        original_content = original_file.file.read().decode('utf-8', errors='ignore')
        modified_content = modified_file.file.read().decode('utf-8', errors='ignore')
        
        # Simple comparison
        changes = []
        orig_lines = original_content.split('\n')
        mod_lines = modified_content.split('\n')
        
        for i, (o, m) in enumerate(zip(orig_lines, mod_lines)):
            if o != m:
                changes.append({
                    "change_id": i,
                    "type": "modified",
                    "original_content": o,
                    "modified_content": m,
                    "line_number": i + 1
                })
        
        # Count differences
        added = len([l for l in mod_lines if l not in orig_lines])
        removed = len([l for l in orig_lines if l not in mod_lines])
        
        total_lines = max(len(orig_lines), len(mod_lines))
        matches = total_lines - len(changes) if total_lines > 0 else 0
        similarity = (matches / total_lines * 100) if total_lines > 0 else 100
        
        return {
            "status": "success",
            "message": f"Compared: {orig_name} vs {mod_name}",
            "similarity": round(similarity, 2),
            "total_changes": len(changes),
            "insertions": added,
            "deletions": removed,
            "changes": changes[:100]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
