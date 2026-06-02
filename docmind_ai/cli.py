"""
DocMind AI - Command Line Interface
"""

import sys
import argparse
from pathlib import Path
import json


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="docmind",
        description="DocMind AI - Intelligent Document Change Intelligence Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  docmind compare file1.pdf file2.pdf
  docmind ocr scan.pdf --language en
  docmind analyze --input comparison.json
  docmind serve --port 8000
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two documents")
    compare_parser.add_argument("original", help="Original document path")
    compare_parser.add_argument("modified", help="Modified document path")
    compare_parser.add_argument("--output", "-o", help="Output file path (JSON)")
    compare_parser.add_argument("--format", "-f", choices=["pdf", "excel", "html"], default="json", help="Report format")
    
    # OCR command
    ocr_parser = subparsers.add_parser("ocr", help="Process document with OCR")
    ocr_parser.add_argument("file", help="Document file path")
    ocr_parser.add_argument("--language", "-l", default="en", help="Language code (en, te, hi, ta)")
    ocr_parser.add_argument("--output", "-o", help="Output file path")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start DocMind API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host address")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port number")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze existing comparison")
    analyze_parser.add_argument("--input", "-i", required=True, help="Input JSON file")
    analyze_parser.add_argument("--output", "-o", help="Output file path")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    args = parser.parse_args()
    
    if args.command == "compare":
        compare_documents(args.original, args.modified, args.output, args.format)
    elif args.command == "ocr":
        process_ocr(args.file, args.language, args.output)
    elif args.command == "serve":
        start_server(args.host, args.port, args.reload)
    elif args.command == "analyze":
        analyze_comparison(args.input, args.output)
    elif args.command == "version":
        show_version()
    else:
        parser.print_help()


def compare_documents(original: str, modified: str, output: str, format: str):
    """Compare two documents"""
    print(f"Comparing documents:")
    print(f"  Original: {original}")
    print(f"  Modified: {modified}")
    print(f"  Output: {output or 'stdout'}")
    print(f"  Format: {format}")
    
    try:
        # Import here to avoid issues if dependencies not installed
        from docmind_ai.core.document_processing import DocumentParserFactory
        from docmind_ai.core.comparison import ComparisonEngine
        from docmind_ai.core.similarity import SimilarityEngine
        from docmind_ai.ai.risk_engine import RiskAnalysisEngine
        from docmind_ai.ai.fraud_engine import FraudDetectionEngine
        
        # Parse documents
        orig_parser = DocumentParserFactory.get_parser(Path(original))
        mod_parser = DocumentParserFactory.get_parser(Path(modified))
        
        orig_content = orig_parser.parse(Path(original))
        mod_content = mod_parser.parse(Path(modified))
        
        # Compare
        engine = ComparisonEngine()
        result = engine.compare(orig_content.text_content, mod_content.text_content)
        
        # Similarity
        sim_engine = SimilarityEngine()
        similarity = sim_engine.calculate_similarity(
            orig_content.text_content,
            mod_content.text_content,
            orig_content.structure,
            mod_content.structure
        )
        
        # Risk analysis
        risk_engine = RiskAnalysisEngine()
        risk = risk_engine.analyze(result.changes, orig_content.text_content, mod_content.text_content)
        
        # Fraud detection
        fraud_engine = FraudDetectionEngine()
        fraud = fraud_engine.analyze(result.changes, orig_content.text_content, mod_content.text_content)
        
        # Prepare output
        output_data = {
            "original": str(original),
            "modified": str(modified),
            "similarity": similarity.overall_similarity,
            "total_changes": len(result.changes),
            "risk_score": risk.overall_risk_score,
            "fraud_score": fraud.fraud_score,
            "changes": [c.to_dict() for c in result.changes[:100]]
        }
        
        if output:
            with open(output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"Results saved to: {output}")
        else:
            print(json.dumps(output_data, indent=2))
            
        print("\n✅ Comparison complete!")
        
    except ImportError as e:
        print(f"Error: Required dependencies not installed. Run: pip install -r requirements.txt")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during comparison: {e}")
        sys.exit(1)


def process_ocr(file: str, language: str, output: str):
    """Process document with OCR"""
    print(f"Processing OCR:")
    print(f"  File: {file}")
    print(f"  Language: {language}")
    
    try:
        from docmind_ai.core.ocr import OCRPipeline
        
        pipeline = OCRPipeline(engine="easyocr", languages=[language])
        
        if Path(file).suffix.lower() == ".pdf":
            analyses = pipeline.process_pdf(Path(file))
            full_text = "\n\n".join([a.full_text for a in analyses])
        else:
            import cv2
            import numpy as np
            image = cv2.imread(str(file))
            if image is None:
                print("Error: Could not read image file")
                sys.exit(1)
            analysis = pipeline.process_document(image)
            full_text = analysis.full_text
        
        if output:
            with open(output, 'w') as f:
                f.write(full_text)
            print(f"OCR text saved to: {output}")
        else:
            print(full_text)
        
        print("\n✅ OCR complete!")
        
    except ImportError as e:
        print(f"Error: OCR dependencies not installed. Run: pip install easyocr opencv-python")
        print(f"Details: {e}")
        sys.exit(1)


def start_server(host: str, port: int, reload: bool):
    """Start the API server"""
    print(f"Starting DocMind API server...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Auto-reload: {reload}")
    
    try:
        import uvicorn
        from docmind_ai.api.app import app
        
        uvicorn.run(
            "docmind_ai.api.app:app",
            host=host,
            port=port,
            reload=reload
        )
    except ImportError:
        print("Error: FastAPI not installed. Run: pip install fastapi uvicorn")
        sys.exit(1)


def analyze_comparison(input_file: str, output: str):
    """Analyze existing comparison results"""
    print(f"Analyzing comparison: {input_file}")
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Generate analysis summary
        summary = {
            "file": input_file,
            "similarity": data.get("similarity", 0),
            "total_changes": data.get("total_changes", 0),
            "risk_score": data.get("risk_score", 0),
            "fraud_score": data.get("fraud_score", 0),
            "severity_breakdown": {},
            "category_breakdown": {}
        }
        
        # Count by severity
        for change in data.get("changes", []):
            sev = change.get("severity", "unknown")
            summary["severity_breakdown"][sev] = summary["severity_breakdown"].get(sev, 0) + 1
            
            cat = change.get("category", "unknown")
            summary["category_breakdown"][cat] = summary["category_breakdown"].get(cat, 0) + 1
        
        if output:
            with open(output, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"Analysis saved to: {output}")
        else:
            print(json.dumps(summary, indent=2))
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)


def show_version():
    """Show version information"""
    print("DocMind AI - Intelligent Document Change Intelligence Platform")
    print("Version: 1.0.0")
    print("Python: 3.10+")
    print()
    print("Features:")
    print("  - Multi-format document comparison (PDF, Excel, Text)")
    print("  - OCR with multi-language support")
    print("  - Semantic analysis with Sentence Transformers")
    print("  - Fraud and risk detection")
    print("  - Contract intelligence")
    print("  - Real-time collaboration")
    print("  - RAG-powered AI responses")


if __name__ == "__main__":
    main()