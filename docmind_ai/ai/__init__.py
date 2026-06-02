"""
DocMind AI - AI Module
"""

from .risk_engine import (
    RiskAnalysisEngine,
    RiskAnalysisResult,
    RiskCategory,
    RiskLevel
)

from .fraud_engine import (
    FraudDetectionEngine,
    FraudDetectionResult,
    FraudType,
    FraudSeverity
)

from .compliance import (
    ComplianceEngine,
    ComplianceReport,
    ComplianceFramework,
    ComplianceStatus
)

from .executive_summary import ExecutiveSummaryGenerator, ExecutiveSummary

from .reviewer_assistant import ReviewerAssistant, AssistantResponse, ChatMessage

from .negotiation import NegotiationAssistant, NegotiationAnalysis, Party

from .voice import VoiceAssistant, VoiceAction, VoiceCommand

from .rag import RAGEngine, RAGResponse, HallucinationDetector, KnowledgeGraphBuilder

from .collaboration import CollaborationEngine, CollabSession, CollabUser, Comment

from .contract_intelligence import ContractIntelligenceEngine, ContractAnalysis, LegalClause, ClauseType

__all__ = [
    # Risk engine
    "RiskAnalysisEngine",
    "RiskAnalysisResult",
    "RiskCategory",
    "RiskLevel",
    
    # Fraud engine
    "FraudDetectionEngine",
    "FraudDetectionResult",
    "FraudType",
    "FraudSeverity",
    
    # Compliance
    "ComplianceEngine",
    "ComplianceReport",
    "ComplianceFramework",
    "ComplianceStatus",
    
    # Executive summary
    "ExecutiveSummaryGenerator",
    "ExecutiveSummary",
    
    # Reviewer assistant
    "ReviewerAssistant",
    "AssistantResponse",
    "ChatMessage",
    
    # Negotiation
    "NegotiationAssistant",
    "NegotiationAnalysis",
    "Party",
    
    # Voice
    "VoiceAssistant",
    "VoiceAction",
    "VoiceCommand",
    
    # RAG
    "RAGEngine",
    "RAGResponse",
    "HallucinationDetector",
    "KnowledgeGraphBuilder",
    
    # Collaboration
    "CollaborationEngine",
    "CollabSession",
    "CollabUser",
    "Comment",
    
    # Contract intelligence
    "ContractIntelligenceEngine",
    "ContractAnalysis",
    "LegalClause",
    "ClauseType"
]