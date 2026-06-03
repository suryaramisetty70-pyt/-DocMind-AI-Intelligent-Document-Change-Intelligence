"""
DocMind AI - API v3.0
"""
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uuid
from pathlib import Path
import tempfile

app = FastAPI(title="DocMind AI", version="3.0")

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
    return {"name": "DocMind AI", "version": "3.0"}


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/v1/compare")
async def compare_documents(original_file: UploadFile = File(...), modified_file: UploadFile = File(...)):
    orig_path = TEMP_DIR / f"orig_{uuid.uuid4()}"
    mod_path = TEMP_DIR / f"mod_{uuid.uuid4()}"
    
    try:
        orig_path.write_bytes(original_file.file.read())
        mod_path.write_bytes(modified_file.file.read())
        
        original_text = orig_path.read_text(encoding="utf-8", errors="ignore")
        modified_text = mod_path.read_text(encoding="utf-8", errors="ignore")
        
        orig_lines = [l.strip() for l in original_text.split("\n") if l.strip()]
        mod_lines = [l.strip() for l in modified_text.split("\n") if l.strip()]
        
        changes = []
        max_lines = max(len(orig_lines), len(mod_lines))
        
        for i in range(max_lines):
            orig_line = orig_lines[i] if i < len(orig_lines) else ""
            mod_line = mod_lines[i] if i < len(mod_lines) else ""
            
            if orig_line != mod_line:
                changes.append({
                    "change_id": i + 1,
                    "type": "modified" if orig_line and mod_line else "insertion" if not orig_line else "deletion",
                    "original_content": orig_line[:200] if orig_line else "(empty)",
                    "modified_content": mod_line[:200] if mod_line else "(empty)",
                    "line_number": i + 1
                })
        
        matching = sum(1 for i in range(min(len(orig_lines), len(mod_lines))) if orig_lines[i] == mod_lines[i])
        total = max(len(orig_lines), len(mod_lines)) or 1
        similarity = round((matching / total) * 100, 2)
        
        return {
            "status": "success",
            "similarity": similarity,
            "total_changes": len(changes),
            "insertions": len([c for c in changes if c["type"] == "insertion"]),
            "deletions": len([c for c in changes if c["type"] == "deletion"]),
            "changes": changes[:30]
        }
    
    finally:
        if orig_path.exists():
            orig_path.unlink()
        if mod_path.exists():
            mod_path.unlink()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
