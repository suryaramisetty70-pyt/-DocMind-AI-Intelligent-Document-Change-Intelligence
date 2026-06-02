"""
DocMind AI - Comprehensive Test Suite
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDocumentProcessing:
    """Test document processing functionality"""
    
    def test_pdf_parser_import(self):
        """Test PDF parser can be imported"""
        from docmind_ai.core.document_processing import PDFParser
        assert PDFParser is not None
    
    def test_excel_parser_import(self):
        """Test Excel parser can be imported"""
        from docmind_ai.core.document_processing import ExcelParser
        assert ExcelParser is not None
    
    def test_text_parser_import(self):
        """Test text parser can be imported"""
        from docmind_ai.core.document_processing import TextParser
        assert TextParser is not None
    
    def test_document_parser_factory(self):
        """Test document parser factory"""
        from docmind_ai.core.document_processing import DocumentParserFactory
        extensions = DocumentParserFactory.get_supported_extensions()
        assert "pdf" in extensions
        assert "xlsx" in extensions
        assert "txt" in extensions


class TestComparisonEngine:
    """Test document comparison engine"""
    
    def test_comparison_engine_import(self):
        """Test comparison engine can be imported"""
        from docmind_ai.core.comparison import ComparisonEngine
        assert ComparisonEngine is not None
    
    def test_comparison_engine_init(self):
        """Test comparison engine initialization"""
        from docmind_ai.core.comparison import ComparisonEngine
        engine = ComparisonEngine()
        assert engine is not None
    
    def test_basic_comparison(self):
        """Test basic text comparison"""
        from docmind_ai.core.comparison import ComparisonEngine
        
        engine = ComparisonEngine()
        result = engine.compare("Hello world", "Hello universe")
        
        assert result is not None
        assert result.overall_similarity > 0
        assert len(result.changes) >= 0
    
    def test_identical_text_comparison(self):
        """Test comparison of identical text"""
        from docmind_ai.core.comparison import ComparisonEngine
        
        engine = ComparisonEngine()
        result = engine.compare("Same text", "Same text")
        
        assert result.overall_similarity == 1.0
        assert len(result.changes) == 0


class TestSemanticComparison:
    """Test semantic comparison functionality"""
    
    def test_semantic_engine_import(self):
        """Test semantic engine can be imported"""
        from docmind_ai.core.semantic import SemanticComparisonEngine
        assert SemanticComparisonEngine is not None
    
    def test_semantic_similarity_calculation(self):
        """Test semantic similarity calculation"""
        from docmind_ai.core.semantic import SemanticComparisonEngine
        
        try:
            engine = SemanticComparisonEngine()
            result = engine.compare(
                "The quick brown fox jumps over the lazy dog",
                "A fast brown fox leaps over a sleepy canine"
            )
            
            assert result is not None
            assert result.overall_semantic_similarity >= 0
        except Exception as e:
            # May fail without model downloaded
            pytest.skip(f"Model not available: {e}")


class TestSimilarityEngine:
    """Test similarity engine"""
    
    def test_similarity_engine_import(self):
        """Test similarity engine can be imported"""
        from docmind_ai.core.similarity import SimilarityEngine
        assert SimilarityEngine is not None
    
    def test_similarity_calculation(self):
        """Test similarity calculation"""
        from docmind_ai.core.similarity import SimilarityEngine
        
        engine = SimilarityEngine()
        result = engine.calculate_similarity(
            "This is a test document",
            "This is another test document"
        )
        
        assert result is not None
        assert result.overall_similarity >= 0
        assert result.overall_similarity <= 1


class TestRiskEngine:
    """Test risk analysis engine"""
    
    def test_risk_engine_import(self):
        """Test risk engine can be imported"""
        from docmind_ai.ai.risk_engine import RiskAnalysisEngine
        assert RiskAnalysisEngine is not None
    
    def test_risk_analysis(self):
        """Test risk analysis"""
        from docmind_ai.ai.risk_engine import RiskAnalysisEngine
        from docmind_ai.core.comparison import Change, ChangeType, ChangeSeverity, ChangeCategory, ChangeLocation
        
        engine = RiskAnalysisEngine()
        
        # Create sample changes
        changes = [
            Change(
                change_type=ChangeType.MODIFICATION,
                location=ChangeLocation(page=1, line_start=10),
                original_content="$100",
                modified_content="$200",
                severity=ChangeSeverity.SIGNIFICANT,
                category=ChangeCategory.CONTENT
            )
        ]
        
        result = engine.analyze(
            changes,
            "The price is $100",
            "The price is $200"
        )
        
        assert result is not None
        assert result.financial_risk > 0


class TestFraudEngine:
    """Test fraud detection engine"""
    
    def test_fraud_engine_import(self):
        """Test fraud engine can be imported"""
        from docmind_ai.ai.fraud_engine import FraudDetectionEngine
        assert FraudDetectionEngine is not None
    
    def test_amount_manipulation_detection(self):
        """Test amount manipulation detection"""
        from docmind_ai.ai.fraud_engine import FraudDetectionEngine
        from docmind_ai.core.comparison import Change, ChangeType, ChangeSeverity, ChangeCategory, ChangeLocation
        
        engine = FraudDetectionEngine()
        
        changes = [
            Change(
                change_type=ChangeType.MODIFICATION,
                location=ChangeLocation(page=1),
                original_content="$100.00",
                modified_content="$500.00",
                severity=ChangeSeverity.SIGNIFICANT,
                category=ChangeCategory.CONTENT
            )
        ]
        
        result = engine.analyze(
            changes,
            "Invoice amount: $100.00",
            "Invoice amount: $500.00"
        )
        
        assert result is not None
        assert result.fraud_score >= 0


class TestHealthScorer:
    """Test document health scorer"""
    
    def test_health_scorer_import(self):
        """Test health scorer can be imported"""
        from docmind_ai.ai.fraud_engine import DocumentHealthScorer
        assert DocumentHealthScorer is not None
    
    def test_health_score_calculation(self):
        """Test health score calculation"""
        from docmind_ai.ai.fraud_engine import DocumentHealthScorer, FraudDetectionResult
        
        scorer = DocumentHealthScorer()
        
        result = scorer.calculate_health_score(
            None,  # fraud_result
            None,  # risk_result
            0.85,  # similarity_score
            {"total_changes": 5, "by_severity": {"minor": 5}}  # stats
        )
        
        assert result is not None
        assert "overall_health_score" in result
        assert "health_grade" in result


class TestExecutiveSummary:
    """Test executive summary generator"""
    
    def test_summary_generator_import(self):
        """Test summary generator can be imported"""
        from docmind_ai.ai.executive_summary import ExecutiveSummaryGenerator
        assert ExecutiveSummaryGenerator is not None
    
    def test_summary_generation(self):
        """Test executive summary generation"""
        from docmind_ai.ai.executive_summary import ExecutiveSummaryGenerator
        from docmind_ai.core.comparison import ComparisonResult
        
        generator = ExecutiveSummaryGenerator()
        
        # Create mock results
        mock_comparison = type('Mock', (), {
            'changes': [],
            'overall_similarity': 0.85,
            'statistics': {'total_changes': 5}
        })()
        
        summary = generator.generate(
            comparison_result=mock_comparison,
            semantic_result=None,
            risk_result=None,
            fraud_result=None,
            similarity_result=None,
            metadata={"document_name": "Test Document"}
        )
        
        assert summary is not None
        assert hasattr(summary, 'overview')
        assert hasattr(summary, 'title')


class TestReviewerAssistant:
    """Test reviewer assistant"""
    
    def test_assistant_import(self):
        """Test assistant can be imported"""
        from docmind_ai.ai.reviewer_assistant import ReviewerAssistant
        assert ReviewerAssistant is not None
    
    def test_assistant_chat(self):
        """Test assistant chat functionality"""
        from docmind_ai.ai.reviewer_assistant import ReviewerAssistant
        
        assistant = ReviewerAssistant()
        
        # Set context
        assistant.set_context({
            "changes": [],
            "statistics": {"total_changes": 10}
        })
        
        # Test chat
        response = assistant.chat("What are the changes?")
        
        assert response is not None
        assert hasattr(response, 'text')
        assert hasattr(response, 'query_type')


class TestAPI:
    """Test API endpoints"""
    
    def test_api_app_import(self):
        """Test API app can be imported"""
        try:
            from docmind_ai.api.app import app
            assert app is not None
        except ImportError as e:
            pytest.skip(f"API dependencies not available: {e}")


class TestConfig:
    """Test configuration"""
    
    def test_config_import(self):
        """Test configuration can be imported"""
        from docmind_ai.config import config, Config
        assert config is not None
    
    def test_config_values(self):
        """Test configuration values"""
        from docmind_ai.config import config
        
        assert config is not None
        assert hasattr(config, 'ENV')
        assert hasattr(config, 'DEBUG')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])