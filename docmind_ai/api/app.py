"""
DocMind AI - FastAPI Backend Application
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os
from pathlib import Path
import base64
import io

# Import core modules
from docmind_ai.core.document_processing import (
    DocumentParserFactory,
    PDFParser,
    ExcelParser,
    TextParser
)
from docmind_ai.core.ocr import OCRPipeline
from docmind_ai.core.comparison import ComparisonEngine
from docmind_ai.core.semantic import SemanticComparisonEngine
from docmind_ai.core.similarity import SimilarityEngine, ChangeHeatmap
from docmind_ai.core.change_intelligence import ChangeIntelligenceEngine
from docmind_ai.ai.risk_engine import RiskAnalysisEngine
from docmind_ai.ai.fraud_engine import FraudDetectionEngine, DocumentHealthScorer
from docmind_ai.ai.executive_summary import ExecutiveSummaryGenerator
from docmind_ai.ai.reviewer_assistant import ReviewerAssistant

# Initialize FastAPI app
app = FastAPI(
    title="DocMind AI - Intelligent Document Change Intelligence",
    description="Enterprise-grade document comparison and analysis platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
comparison_engine = ComparisonEngine()
semantic_engine = SemanticComparisonEngine()
similarity_engine = SimilarityEngine()
change_intelligence = ChangeIntelligenceEngine()
risk_engine = RiskAnalysisEngine()
fraud_engine = FraudDetectionEngine()
health_scorer = DocumentHealthScorer()
summary_generator = ExecutiveSummaryGenerator()
reviewer_assistant = ReviewerAssistant()

# Storage paths
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Pydantic Models
class ComparisonRequest(BaseModel):
    """Request model for document comparison"""
    original_document_id: Optional[str] = None
    modified_document_id: Optional[str] = None
    language: str = Field(default="en", description="Document language")
    include_semantic: bool = Field(default=True, description="Include semantic analysis")
    include_fraud_detection: bool = Field(default=True, description="Include fraud detection")


class ChangeLocationModel(BaseModel):
    """Change location model"""
    page: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    section: Optional[str] = None


class ChangeModel(BaseModel):
    """Change model"""
    change_id: str
    change_type: str
    location: ChangeLocationModel
    original_content: str
    modified_content: str
    similarity_score: float
    severity: str
    category: str


class ComparisonResponse(BaseModel):
    """Response model for document comparison"""
    comparison_id: str
    overall_similarity: float
    semantic_similarity: float
    total_changes: int
    changes: List[ChangeModel]
    risk_analysis: Optional[Dict[str, Any]] = None
    fraud_detection: Optional[Dict[str, Any]] = None
    health_score: Optional[Dict[str, Any]] = None
    executive_summary: Optional[Dict[str, Any]] = None
    processing_time: float


class ChatRequest(BaseModel):
    """Request model for chat with assistant"""
    message: str
    comparison_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat"""
    response: str
    query_type: str
    confidence: float
    suggested_actions: List[str]


class ReportRequest(BaseModel):
    """Request model for report generation"""
    comparison_id: str
    format: str = Field(default="json", description="Report format: json, pdf, excel")
    include_sections: List[str] = Field(
        default=["overview", "changes", "risk", "fraud", "recommendations"],
        description="Sections to include in report"
    )


class HealthScoreResponse(BaseModel):
    """Response model for health score"""
    overall_health_score: float
    trust_score: float
    risk_score: float
    similarity_score: float
    review_complexity_score: float
    health_grade: str


# Store comparison results in memory (would use database in production)
comparison_results = {}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "DocMind AI API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "documents": "/api/v1/documents",
            "compare": "/api/v1/compare",
            "chat": "/api/v1/chat",
            "report": "/api/v1/report",
            "heatmap": "/api/v1/heatmap"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "comparison_engine": "operational",
            "semantic_engine": "operational",
            "risk_engine": "operational",
            "fraud_engine": "operational"
        }
    }


@app.post("/api/v1/documents/upload")
async def upload_documents(
    original: UploadFile = File(...),
    modified: UploadFile = File(...)
):
    """Upload two documents for comparison"""
    try:
        # Save uploaded files
        original_path = UPLOAD_DIR / f"{uuid.uuid4()}_{original.filename}"
        modified_path = UPLOAD_DIR / f"{uuid.uuid4()}_{modified.filename}"
        
        with open(original_path, "wb") as f:
            f.write(await original.read())
        
        with open(modified_path, "wb") as f:
            f.write(await modified.read())
        
        # Get parser for file types
        original_parser = DocumentParserFactory.get_parser(original_path)
        modified_parser = DocumentParserFactory.get_parser(modified_path)
        
        # Parse documents
        original_content = original_parser.parse(original_path)
        modified_content = modified_parser.parse(modified_path)
        
        return {
            "status": "success",
            "original_document": {
                "id": str(original_path.stem),
                "filename": original.filename,
                "path": str(original_path),
                "size": original_content.metadata.file_size,
                "pages": original_content.metadata.page_count
            },
            "modified_document": {
                "id": str(modified_path.stem),
                "filename": modified.filename,
                "path": str(modified_path),
                "size": modified_content.metadata.file_size,
                "pages": modified_content.metadata.page_count
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/compare")
async def compare_documents(
    original_file: UploadFile = File(...),
    modified_file: UploadFile = File(...),
    language: str = "en",
    include_semantic: bool = True,
    include_fraud_detection: bool = True
):
    """Compare two documents and generate comprehensive analysis"""
    try:
        import time
        start_time = time.time()
        
        # Save uploaded files
        original_path = UPLOAD_DIR / f"{uuid.uuid4()}_{original_file.filename}"
        modified_path = UPLOAD_DIR / f"{uuid.uuid4()}_{modified_file.filename}"
        
        with open(original_path, "wb") as f:
            f.write(await original_file.read())
        
        with open(modified_path, "wb") as f:
            f.write(await modified_file.read())
        
        # Parse documents
        original_parser = DocumentParserFactory.get_parser(original_path)
        modified_parser = DocumentParserFactory.get_parser(modified_path)
        
        original_content = original_parser.parse(original_path)
        modified_content = modified_parser.parse(modified_path)
        
        # Run comparison
        comparison_result = comparison_engine.compare_structured(
            {
                "text_content": original_content.text_content,
                "structure": original_content.structure,
                "tables": original_content.tables
            },
            {
                "text_content": modified_content.text_content,
                "structure": modified_content.structure,
                "tables": modified_content.tables
            }
        )
        
        # Semantic comparison
        semantic_result = None
        if include_semantic:
            semantic_result = semantic_engine.compare(
                original_content.text_content,
                modified_content.text_content
            )
        
        # Similarity calculation
        similarity_result = similarity_engine.calculate_similarity(
            original_content.text_content,
            modified_content.text_content,
            original_content.structure,
            modified_content.structure
        )
        
        # Risk analysis
        risk_result = risk_engine.analyze(
            comparison_result.changes,
            original_content.text_content,
            modified_content.text_content
        )
        
        # Fraud detection
        fraud_result = None
        health_result = None
        if include_fraud_detection:
            fraud_result = fraud_engine.analyze(
                comparison_result.changes,
                original_content.text_content,
                modified_content.text_content,
                original_content.structure,
                modified_content.structure,
                original_content.tables,
                modified_content.tables
            )
            
            # Health score
            health_result = health_scorer.calculate_health_score(
                fraud_result,
                risk_result,
                similarity_result.overall_similarity,
                comparison_result.statistics
            )
        
        # Generate executive summary
        summary_result = summary_generator.generate(
            comparison_result,
            semantic_result,
            risk_result,
            fraud_result,
            similarity_result,
            {
                "document_name": original_file.filename,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        
        # Set context for reviewer assistant
        reviewer_assistant.set_context({
            "changes": [c.to_dict() for c in comparison_result.changes],
            "statistics": comparison_result.statistics,
            "risk_result": risk_result,
            "fraud_result": fraud_result,
            "similarity_score": similarity_result.overall_similarity
        })
        
        # Store results
        comparison_id = str(uuid.uuid4())
        comparison_results[comparison_id] = {
            "comparison_result": comparison_result,
            "semantic_result": semantic_result,
            "risk_result": risk_result,
            "fraud_result": fraud_result,
            "health_result": health_result,
            "summary_result": summary_result
        }
        
        total_time = time.time() - start_time
        
        # Build response
        changes = []
        for idx, change in enumerate(comparison_result.changes):
            changes.append(ChangeModel(
                change_id=f"change_{idx}",
                change_type=change.change_type.value,
                location=ChangeLocationModel(
                    page=change.location.page,
                    line_start=change.location.line_start,
                    line_end=change.location.line_end,
                    section=change.location.section
                ),
                original_content=change.original_content,
                modified_content=change.modified_content,
                similarity_score=change.similarity_score,
                severity=change.severity.value,
                category=change.category.value
            ))
        
        return ComparisonResponse(
            comparison_id=comparison_id,
            overall_similarity=comparison_result.overall_similarity,
            semantic_similarity=semantic_result.overall_semantic_similarity if semantic_result else 0,
            total_changes=len(comparison_result.changes),
            changes=changes,
            risk_analysis={
                "overall_risk_score": risk_result.overall_risk_score,
                "risk_level": risk_result.risk_level.value,
                "financial_risk": risk_result.financial_risk,
                "legal_risk": risk_result.legal_risk,
                "compliance_risk": risk_result.compliance_risk,
                "operational_risk": risk_result.operational_risk,
                "risk_factors": risk_result.risk_factors,
                "recommendations": risk_result.recommendations
            } if risk_result else None,
            fraud_detection={
                "fraud_score": fraud_result.fraud_score if fraud_result else 0,
                "fraud_level": fraud_result.fraud_level.value if fraud_result else "unknown",
                "indicators_count": len(fraud_result.indicators) if fraud_result else 0,
                "critical_findings_count": len(fraud_result.critical_findings) if fraud_result else 0
            } if fraud_result else None,
            health_score={
                "overall_health_score": health_result.get("overall_health_score", 0) if health_result else 0,
                "trust_score": health_result.get("trust_score", 0) if health_result else 0,
                "risk_score": health_result.get("risk_score", 0) if health_result else 0,
                "similarity_score": health_result.get("similarity_score", 0) if health_result else 0,
                "health_grade": health_result.get("health_grade", "N/A") if health_result else "N/A"
            } if health_result else None,
            executive_summary={
                "overview": summary_result.overview,
                "critical_findings": summary_result.critical_findings,
                "recommendations": summary_result.recommendations,
                "statistics": summary_result.statistics
            } if summary_result else None,
            processing_time=total_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat")
async def chat_with_assistant(request: ChatRequest):
    """Chat with the reviewer assistant"""
    try:
        response = reviewer_assistant.chat(request.message)
        
        return ChatResponse(
            response=response.text,
            query_type=response.query_type.value,
            confidence=response.confidence,
            suggested_actions=response.suggested_actions
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/comparison/{comparison_id}")
async def get_comparison(comparison_id: str):
    """Get stored comparison results"""
    if comparison_id not in comparison_results:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    return comparison_results[comparison_id]


@app.get("/api/v1/heatmap/{comparison_id}")
async def get_change_heatmap(comparison_id: str):
    """Get change heatmap for a comparison"""
    if comparison_id not in comparison_results:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    result = comparison_results[comparison_id]
    comparison_result = result["comparison_result"]
    
    heatmap = ChangeHeatmap()
    
    total_pages = max(
        (change.location.page or 1) 
        for change in comparison_result.changes
    ) if comparison_result.changes else 1
    
    page_density = heatmap.generate_page_heatmap(
        comparison_result.changes,
        total_pages
    )
    
    hotspots = heatmap.get_hotspots(page_density, threshold=0.5)
    
    return {
        "page_density": page_density,
        "hotspots": hotspots,
        "total_pages": total_pages,
        "change_distribution": {
            "high": sum(1 for d in page_density.values() if d >= 0.7),
            "medium": sum(1 for d in page_density.values() if 0.3 <= d < 0.7),
            "low": sum(1 for d in page_density.values() if d < 0.3)
        }
    }


@app.get("/api/v1/summary/{comparison_id}")
async def get_executive_summary(comparison_id: str):
    """Get executive summary for a comparison"""
    if comparison_id not in comparison_results:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    result = comparison_results[comparison_id]
    summary_result = result["summary_result"]
    
    return summary_generator.to_dict(summary_result)


@app.post("/api/v1/report")
async def generate_report(request: ReportRequest):
    """Generate a report for a comparison"""
    if request.comparison_id not in comparison_results:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    result = comparison_results[request.comparison_id]
    
    # Generate report based on format
    if request.format == "json":
        return {
            "comparison_id": request.comparison_id,
            "format": "json",
            "sections": request.include_sections,
            "data": {
                "overview": result.get("summary_result").overview if result.get("summary_result") else "",
                "changes": [c.to_dict() for c in result.get("comparison_result", {}).changes or []],
                "risk": result.get("risk_result"),
                "fraud": result.get("fraud_result"),
                "statistics": result.get("comparison_result", {}).statistics if result.get("comparison_result") else {}
            }
        }
    
    return {"message": "Other formats not yet implemented"}


# OCR Endpoint
@app.post("/api/v1/ocr/process")
async def process_ocr(
    file: UploadFile = File(...),
    language: str = "en"
):
    """Process document with OCR"""
    try:
        import numpy as np
        import cv2
        
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Process based on file type
        if file_path.suffix.lower() == ".pdf":
            ocr_pipeline = OCRPipeline(engine="easyocr", languages=[language])
            analyses = ocr_pipeline.process_pdf(file_path)
            
            full_text = "\n\n".join([a.full_text for a in analyses])
            
            return {
                "status": "success",
                "file_type": "pdf",
                "pages_processed": len(analyses),
                "full_text": full_text,
                "overall_confidence": sum(a.overall_confidence for a in analyses) / len(analyses) if analyses else 0,
                "detections": {
                    "signatures": sum(len(a.layout.signature_regions) for a in analyses),
                    "stamps": sum(len(a.layout.stamp_regions) for a in analyses),
                    "tables": sum(len(a.layout.table_regions) for a in analyses)
                }
            }
        else:
            # Process as image
            image = cv2.imread(str(file_path))
            if image is None:
                raise HTTPException(status_code=400, detail="Could not read image file")
            
            ocr_pipeline = OCRPipeline(engine="easyocr", languages=[language])
            analysis = ocr_pipeline.process_document(image)
            
            return {
                "status": "success",
                "file_type": "image",
                "full_text": analysis.full_text,
                "confidence": analysis.overall_confidence,
                "processing_time": analysis.processing_time
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)