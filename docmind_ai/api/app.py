"""
DocMind AI - API v3.0 PRO
Next-Level Document Intelligence
"""
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uuid
from pathlib import Path
import tempfile
import random
from datetime import datetime
from typing import List, Dict

app = FastAPI(title="DocMind AI PRO", version="3.0")

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
    return {
        "name": "DocMind AI PRO",
        "version": "3.0",
        "status": "running",
        "features": ["Document Comparison", "AI Analysis", "Risk Detection", "Fraud Detection"]
    }


@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "version": "3.0"}


def analyze_change_type(line: str) -> str:
    """AI analyzes what type of change this is"""
    line_lower = line.lower()
    
    if any(word in line_lower for word in ['amount', 'price', 'cost', '$', '₹', 'rs']):
        return "financial"
    elif any(word in line_lower for word in ['date', 'deadline', 'due', 'expire']):
        return "date_change"
    elif any(word in line_lower for word in ['sign', 'signature', 'authorize']):
        return "signature_related"
    elif any(word in line_lower for word in ['delete', 'remove', 'remove', 'cancel']):
        return "deletion"
    elif any(word in line_lower for word in ['add', 'new', 'include', 'insert']):
        return "addition"
    elif len(line) > 100:
        return "major_change"
    else:
        return "minor_change"


def generate_ai_explanation(change_type: str, orig: str, mod: str) -> str:
    """Generate AI explanation for the change"""
    explanations = {
        "financial": f"Financial change detected: Value changed from '{orig[:30]}' to '{mod[:30]}'. This may impact cost calculations.",
        "date_change": f"Date modification found: Timeline adjustment from '{orig[:30]}' to '{mod[:30]}'.",
        "signature_related": f"Authorization change: Document signing section modified.",
        "deletion": f"Content removed: '{orig[:50]}...'. This section was deleted.",
        "addition": f"New content added: '{mod[:50]}...'. This is a new addition to the document.",
        "major_change": f"Significant modification: Large section changed. Review required.",
        "minor_change": f"Minor change: Small text modification detected."
    }
    return explanations.get(change_type, "Change detected in document.")


def calculate_risk_score(changes: List[Dict]) -> Dict:
    """Calculate overall risk score"""
    risk_factors = []
    risk_score = 0
    
    for change in changes:
        ctype = change.get("type", "")
        orig = change.get("original_content", "")
        mod = change.get("modified_content", "")
        
        # Financial changes increase risk
        if any(word in orig.lower() + mod.lower() for word in ['amount', 'price', '$', '₹', 'cost', 'fee']):
            risk_score += 15
            risk_factors.append("💰 Financial change detected")
        
        # Date changes
        if any(word in orig.lower() + mod.lower() for word in ['date', 'deadline', 'due']):
            risk_score += 10
            risk_factors.append("📅 Date modification")
        
        # Deletions
        if ctype == "deletion":
            risk_score += 8
            risk_factors.append("🗑️ Content deleted")
        
        # Long changes
        if len(orig) > 50 or len(mod) > 50:
            risk_score += 5
            risk_factors.append("📝 Major text section changed")
    
    # Normalize to 0-100
    risk_score = min(100, risk_score)
    
    if risk_score >= 70:
        level = "HIGH"
        emoji = "🔴"
    elif risk_score >= 40:
        level = "MEDIUM"
        emoji = "🟡"
    else:
        level = "LOW"
        emoji = "🟢"
    
    return {
        "score": risk_score,
        "level": level,
        "emoji": emoji,
        "factors": risk_factors[:5]
    }


def detect_fraud_indicators(changes: List[Dict]) -> List[Dict]:
    """Detect potential fraud indicators"""
    fraud_alerts = []
    
    for change in changes:
        orig = change.get("original_content", "")
        mod = change.get("modified_content", "")
        
        # Check for amount manipulation
        if '$' in orig and '$' not in mod:
            fraud_alerts.append({
                "type": "amount_removal",
                "severity": "HIGH",
                "message": "Currency symbol removed - verify if amount is legitimate",
                "original": orig[:50],
                "modified": mod[:50]
            })
        
        # Check for date manipulation
        if ('2024' in orig or '2025' in orig) and ('2026' in mod):
            fraud_alerts.append({
                "type": "date_shift",
                "severity": "MEDIUM",
                "message": "Year changed - possible timeline manipulation",
                "original": orig[:50],
                "modified": mod[:50]
            })
        
        # Check for signature removal
        if any(word in orig.lower() for word in ['sign', 'agree', 'accept', 'approve']):
            if not any(word in mod.lower() for word in ['sign', 'agree', 'accept', 'approve']):
                fraud_alerts.append({
                    "type": "consent_removal",
                    "severity": "HIGH",
                    "message": "Agreement clause removed - verify consent is maintained",
                    "original": orig[:50],
                    "modified": mod[:50]
                })
        
        # Check for percentage changes
        if '%' in orig and '%' not in mod:
            fraud_alerts.append({
                "type": "percentage_change",
                "severity": "MEDIUM",
                "message": "Percentage removed - review calculations",
                "original": orig[:50],
                "modified": mod[:50]
            })
    
    return fraud_alerts


def generate_health_score(changes: List[Dict], similarity: float) -> Dict:
    """Calculate document health score"""
    base_score = similarity
    
    # Penalize for risky changes
    risk_adjustment = len(changes) * 0.5
    final_score = max(0, min(100, base_score - risk_adjustment))
    
    if final_score >= 80:
        status = "EXCELLENT"
        color = "#00ff88"
    elif final_score >= 60:
        status = "GOOD"
        color = "#88ff00"
    elif final_score >= 40:
        status = "FAIR"
        color = "#ffaa00"
    else:
        status = "POOR"
        color = "#ff4444"
    
    return {
        "score": round(final_score, 1),
        "status": status,
        "color": color,
        "recommendations": [
            "Review all highlighted changes",
            "Verify financial modifications",
            "Check date-related changes",
            "Ensure all deletions are intentional"
        ]
    }


def generate_smart_recommendations(changes: List[Dict], risk: Dict) -> List[Dict]:
    """Generate smart recommendations based on changes"""
    recommendations = []
    
    if risk["level"] == "HIGH":
        recommendations.append({
            "priority": "URGENT",
            "title": "High Risk Changes Detected",
            "description": f"Risk score: {risk['score']}%. Review all changes before approval.",
            "action": "Request supervisor approval"
        })
    
    financial_changes = [c for c in changes if any(w in c.get('original_content','').lower() for w in ['amount', 'price', '$', '₹'])]
    if financial_changes:
        recommendations.append({
            "priority": "HIGH",
            "title": "Financial Changes Found",
            "description": f"{len(financial_changes)} financial modifications detected. Verify amounts.",
            "action": "Cross-check with finance team"
        })
    
    if len(changes) > 20:
        recommendations.append({
            "priority": "MEDIUM",
            "title": "Many Changes Detected",
            "description": f"{len(changes)} modifications. Consider creating a change summary.",
            "action": "Generate detailed report"
        })
    
    recommendations.append({
        "priority": "INFO",
        "title": "Always Verify",
        "description": "Double-check all modifications before finalizing.",
        "action": "Digital verification recommended"
    })
    
    return recommendations


@app.post("/api/v1/compare")
async def compare_documents(original_file: UploadFile = File(...), modified_file: UploadFile = File(...)):
    """Full-featured document comparison with AI analysis"""
    
    orig_path = TEMP_DIR / f"orig_{uuid.uuid4()}"
    mod_path = TEMP_DIR / f"mod_{uuid.uuid4()}"
    
    try:
        # Save and read files
        orig_path.write_bytes(original_file.file.read())
        mod_path.write_bytes(modified_file.file.read())
        
        original_text = orig_path.read_text(encoding="utf-8", errors="ignore")
        modified_text = mod_path.read_text(encoding="utf-8", errors="ignore")
        
        # Extract lines
        orig_lines = [l.strip() for l in original_text.split("\n") if l.strip()]
        mod_lines = [l.strip() for l in modified_text.split("\n") if l.strip()]
        
        # Analyze changes with AI
        changes = []
        word_level_changes = []
        character_changes = 0
        
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
                
                # AI Analysis
                change_category = analyze_change_type(orig_line + mod_line)
                ai_explanation = generate_ai_explanation(change_category, orig_line, mod_line)
                
                changes.append({
                    "change_id": i + 1,
                    "type": change_type,
                    "category": change_category,
                    "original_content": orig_line[:200] if orig_line else "(empty)",
                    "modified_content": mod_line[:200] if mod_line else "(empty)",
                    "line_number": i + 1,
                    "ai_explanation": ai_explanation,
                    "severity": "HIGH" if change_category in ["financial", "date_change"] else "LOW"
                })
                
                # Word-level analysis
                if orig_line and mod_line:
                    orig_words = set(orig_line.lower().split())
                    mod_words = set(mod_line.lower().split())
                    removed_words = orig_words - mod_words
                    added_words = mod_words - orig_words
                    if removed_words or added_words:
                        word_level_changes.append({
                            "line": i + 1,
                            "removed": list(removed_words)[:5],
                            "added": list(added_words)[:5]
                        })
                
                # Character diff
                if orig_line and mod_line:
                    character_changes += abs(len(orig_line) - len(mod_line))
        
        # Calculate metrics
        matching = sum(1 for i in range(min(len(orig_lines), len(mod_lines))) if orig_lines[i] == mod_lines[i])
        total = max(len(orig_lines), len(mod_lines)) or 1
        similarity = round((matching / total) * 100, 2)
        
        # Generate insights
        risk_analysis = calculate_risk_score(changes)
        fraud_detection = detect_fraud_indicators(changes)
        health_score = generate_health_score(changes, similarity)
        recommendations = generate_smart_recommendations(changes, risk_analysis)
        
        # Document statistics
        stats = {
            "original_words": len(original_text.split()),
            "modified_words": len(modified_text.split()),
            "original_chars": len(original_text),
            "modified_chars": len(modified_text),
            "original_lines": len(orig_lines),
            "modified_lines": len(mod_lines),
            "word_level_changes": len(word_level_changes),
            "character_changes": character_changes
        }
        
        return {
            "status": "success",
            "comparison_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "files": {
                "original": original_file.filename,
                "modified": modified_file.filename
            },
            "similarity": similarity,
            "statistics": stats,
            "total_changes": len(changes),
            "insertions": len([c for c in changes if c["type"] == "insertion"]),
            "deletions": len([c for c in changes if c["type"] == "deletion"]),
            "modifications": len([c for c in changes if c["type"] == "modified"]),
            "changes": changes[:30],
            "word_level_analysis": word_level_changes[:10],
            "risk_analysis": risk_analysis,
            "fraud_detection": {
                "total_alerts": len(fraud_alerts),
                "alerts": fraud_alerts
            },
            "health_score": health_score,
            "recommendations": recommendations
        }
    
    finally:
        if orig_path.exists():
            orig_path.unlink()
        if mod_path.exists():
            mod_path.unlink()


@app.post("/api/v1/export/pdf")
async def export_pdf_report(comparison_data: dict):
    """Export comparison as PDF (placeholder)"""
    return {
        "status": "export_ready",
        "format": "PDF",
        "download_url": "/api/v1/download/report.pdf"
    }


@app.post("/api/v1/export/excel")
async def export_excel_report(comparison_data: dict):
    """Export comparison as Excel (placeholder)"""
    return {
        "status": "export_ready",
        "format": "Excel",
        "download_url": "/api/v1/download/report.xlsx"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
