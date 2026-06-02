"""
DocMind AI - Reviewer Assistant
AI-powered conversational interface for document review
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import json


class QueryType(Enum):
    """Types of queries the assistant can handle"""
    CHANGE_EXPLANATION = "change_explanation"
    COMPARISON_SUMMARY = "comparison_summary"
    RISK_EXPLANATION = "risk_explanation"
    COMPLIANCE_QUERY = "compliance_query"
    SIMILARITY_QUERY = "similarity_query"
    STATISTICS_QUERY = "statistics_query"
    RECOMMENDATION_QUERY = "recommendation_query"
    GENERAL = "general"


@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssistantResponse:
    """Structured response from the assistant"""
    text: str
    query_type: QueryType
    confidence: float
    sources: List[str] = field(default_factory=list)
    suggested_actions: List[str] = field(default_factory=list)
    related_queries: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


class QueryClassifier:
    """Classify user queries to determine intent"""
    
    def __init__(self):
        self.query_patterns = {
            QueryType.CHANGE_EXPLANATION: [
                "explain", "what changed", "tell me about", "describe",
                "why was", "what does", "meaning of", "understand"
            ],
            QueryType.COMPARISON_SUMMARY: [
                "compare", "difference", "summary", "overview",
                "what's different", "changes between"
            ],
            QueryType.RISK_EXPLANATION: [
                "risk", "danger", "concern", "problem", "issue",
                "warning", "alert", "fraud", "manipulation"
            ],
            QueryType.COMPLIANCE_QUERY: [
                "compliance", "regulation", "requirement", "clause",
                "policy", "standard", "GDPR", "HIPAA"
            ],
            QueryType.SIMILARITY_QUERY: [
                "similarity", "same", "different", "how related",
                "match", "percent"
            ],
            QueryType.STATISTICS_QUERY: [
                "statistics", "count", "how many", "number of",
                "metrics", "data"
            ],
            QueryType.RECOMMENDATION_QUERY: [
                "recommend", "suggestion", "should", "advise",
                "action", "next steps"
            ]
        }
    
    def classify(self, query: str) -> QueryType:
        """Classify user query"""
        query_lower = query.lower()
        
        scores = {}
        for qtype, patterns in self.query_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            scores[qtype] = score
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return QueryType.GENERAL


class ResponseGenerator:
    """Generate responses for user queries"""
    
    def __init__(self):
        self.templates = {}
    
    def generate_change_explanation(self, query: str, context: Dict[str, Any]) -> str:
        """Generate explanation for specific change"""
        changes = context.get("changes", [])
        
        # Try to find specific change being asked about
        for change in changes:
            if any(word in (change.get("original_content", "") + change.get("modified_content", "")).lower() 
                   for word in query.lower().split()):
                return self._format_change_explanation(change)
        
        # General explanation
        return (
            f"The documents contain {len(changes)} changes in total. "
            f"These include insertions, deletions, modifications, and movements. "
            f"Changes are categorized by type (content, structure, formatting) "
            f"and severity (critical, significant, moderate, minor)."
        )
    
    def _format_change_explanation(self, change: Dict[str, Any]) -> str:
        """Format a single change explanation"""
        change_type = change.get("change_type", "unknown")
        original = change.get("original_content", "")[:100]
        modified = change.get("modified_content", "")[:100]
        severity = change.get("severity", "unknown")
        
        explanation = f"**Change Type:** {change_type}\n"
        explanation += f"**Severity:** {severity.upper()}\n"
        
        if original:
            explanation += f"**Original:** {original}...\n"
        if modified:
            explanation += f"**Modified:** {modified}...\n"
        
        return explanation
    
    def generate_comparison_summary(self, context: Dict[str, Any]) -> str:
        """Generate comparison summary"""
        stats = context.get("statistics", {})
        similarity = context.get("similarity_score", 0)
        
        total = stats.get("total_changes", 0)
        by_type = stats.get("by_type", {})
        by_severity = stats.get("by_severity", {})
        
        summary = f"""## Document Comparison Summary

**Overall Similarity:** {int(similarity * 100)}%

**Total Changes:** {total}

### By Type:
"""
        for change_type, count in by_type.items():
            summary += f"- {change_type}: {count}\n"
        
        summary += "\n### By Severity:\n"
        for severity, count in by_severity.items():
            summary += f"- {severity}: {count}\n"
        
        return summary
    
    def generate_risk_explanation(self, risk_result: Any, context: Dict[str, Any]) -> str:
        """Generate risk explanation"""
        if not risk_result:
            return "No risk analysis has been performed on these documents."
        
        explanation = f"""## Risk Analysis Summary

**Overall Risk Score:** {risk_result.overall_risk_score:.1%}

**Risk Level:** {risk_result.risk_level.value.upper() if hasattr(risk_result, 'risk_level') else 'UNKNOWN'}

### Risk Breakdown:
"""
        
        if hasattr(risk_result, 'financial_risk'):
            explanation += f"- **Financial Risk:** {risk_result.financial_risk:.1%}\n"
        if hasattr(risk_result, 'legal_risk'):
            explanation += f"- **Legal Risk:** {risk_result.legal_risk:.1%}\n"
        if hasattr(risk_result, 'compliance_risk'):
            explanation += f"- **Compliance Risk:** {risk_result.compliance_risk:.1%}\n"
        if hasattr(risk_result, 'operational_risk'):
            explanation += f"- **Operational Risk:** {risk_result.operational_risk:.1%}\n"
        
        if hasattr(risk_result, 'risk_factors') and risk_result.risk_factors:
            explanation += "\n### Key Risk Factors:\n"
            for factor in risk_result.risk_factors[:5]:
                explanation += f"- {factor}\n"
        
        if hasattr(risk_result, 'recommendations') and risk_result.recommendations:
            explanation += "\n### Recommendations:\n"
            for rec in risk_result.recommendations[:3]:
                explanation += f"- {rec}\n"
        
        return explanation
    
    def generate_statistics(self, stats: Dict[str, Any]) -> str:
        """Generate statistics response"""
        output = "## Document Statistics\n\n"
        
        comparison = stats.get("comparison", {})
        if comparison:
            output += "**Comparison Statistics:**\n"
            output += f"- Total Changes: {comparison.get('total_changes', 0)}\n"
            output += f"- Insertions: {comparison.get('insertions', 0)}\n"
            output += f"- Deletions: {comparison.get('deletions', 0)}\n"
            output += f"- Modifications: {comparison.get('modifications', 0)}\n"
        
        similarity = stats.get("similarity", {})
        if similarity:
            output += "\n**Similarity Scores:**\n"
            output += f"- Overall: {int(similarity.get('overall', 0) * 100)}%\n"
            output += f"- Semantic: {int(similarity.get('semantic', 0) * 100)}%\n"
            output += f"- Structural: {int(similarity.get('structural', 0) * 100)}%\n"
        
        return output


class ReviewerAssistant:
    """Main reviewer assistant with conversational interface"""
    
    def __init__(self):
        self.classifier = QueryClassifier()
        self.generator = ResponseGenerator()
        self.conversation_history: List[ChatMessage] = []
        self.context: Dict[str, Any] = {}
    
    def set_context(self, context: Dict[str, Any]):
        """Set analysis context for the assistant"""
        self.context = context
    
    def chat(self, user_query: str) -> AssistantResponse:
        """Process user query and generate response"""
        # Classify query
        query_type = self.classifier.classify(user_query)
        
        # Generate response based on type
        if query_type == QueryType.CHANGE_EXPLANATION:
            response_text = self.generator.generate_change_explanation(user_query, self.context)
        elif query_type == QueryType.COMPARISON_SUMMARY:
            response_text = self.generator.generate_comparison_summary(self.context)
        elif query_type == QueryType.RISK_EXPLANATION:
            response_text = self.generator.generate_risk_explanation(
                self.context.get("risk_result"),
                self.context
            )
        elif query_type == QueryType.STATISTICS_QUERY:
            response_text = self.generator.generate_statistics(
                self.context.get("statistics", {})
            )
        else:
            response_text = self._handle_general_query(user_query)
        
        # Add to conversation history
        self.conversation_history.append(ChatMessage(
            role="user",
            content=user_query,
            timestamp=0  # Would be actual timestamp
        ))
        
        self.conversation_history.append(ChatMessage(
            role="assistant",
            content=response_text,
            timestamp=0
        ))
        
        return AssistantResponse(
            text=response_text,
            query_type=query_type,
            confidence=0.9,
            sources=self._get_sources(query_type),
            suggested_actions=self._get_suggested_actions(query_type),
            related_queries=self._get_related_queries(query_type),
            data={"context_used": list(self.context.keys())}
        )
    
    def _handle_general_query(self, query: str) -> str:
        """Handle general queries"""
        query_lower = query.lower()
        
        if "help" in query_lower:
            return self._get_help_text()
        
        if "what can" in query_lower or "capabilities" in query_lower:
            return self._get_capabilities_text()
        
        return "I can help explain changes, analyze risks, summarize comparisons, and answer questions about the documents. Try asking about specific changes, risks, or statistics."
    
    def _get_help_text(self) -> str:
        return """## How to Use the Reviewer Assistant

You can ask me:
- **About changes:** "Explain the third change" or "What was modified in section 2?"
- **About risks:** "What are the risk factors?" or "Is there any fraud detected?"
- **About comparison:** "Give me a summary of the changes" or "How similar are these documents?"
- **About statistics:** "How many changes were made?" or "Show me the statistics"
- **About compliance:** "Any compliance issues?" or "Are there missing clauses?"

Just type your question naturally and I'll help you understand the document comparison."""
    
    def _get_capabilities_text(self) -> str:
        return """## Assistant Capabilities

I can help you with:

1. **Change Analysis**
   - Explain specific changes
   - Show change details and context
   - Track change history

2. **Risk Assessment**
   - Identify financial, legal, compliance risks
   - Explain risk factors
   - Suggest mitigations

3. **Fraud Detection**
   - Detect manipulation attempts
   - Identify hidden text/rows
   - Alert to suspicious patterns

4. **Document Comparison**
   - Summary of differences
   - Similarity scores
   - Statistics and metrics

5. **Recommendations**
   - Suggest next steps
   - Priority actions
   - Review guidance

Just ask a question and I'll provide the information you need."""
    
    def _get_sources(self, query_type: QueryType) -> List[str]:
        """Get relevant sources for the query type"""
        sources_map = {
            QueryType.CHANGE_EXPLANATION: ["comparison_engine", "change_intelligence"],
            QueryType.RISK_EXPLANATION: ["risk_engine"],
            QueryType.FRAUD_DETECTION: ["fraud_detector"],
            QueryType.COMPLIANCE_QUERY: ["compliance_engine"],
            QueryType.SIMILARITY_QUERY: ["similarity_engine"]
        }
        return sources_map.get(query_type, ["general"])
    
    def _get_suggested_actions(self, query_type: QueryType) -> List[str]:
        """Get suggested follow-up actions"""
        actions_map = {
            QueryType.CHANGE_EXPLANATION: [
                "View full change details",
                "Export change report",
                "Filter by severity"
            ],
            QueryType.RISK_EXPLANATION: [
                "View risk indicators",
                "Download risk report",
                "Escalate high-risk items"
            ],
            QueryType.GENERAL: [
                "Ask about specific changes",
                "View risk summary",
                "Generate full report"
            ]
        }
        return actions_map.get(query_type, ["Ask another question", "Generate report"])
    
    def _get_related_queries(self, query_type: QueryType) -> List[str]:
        """Get related query suggestions"""
        queries_map = {
            QueryType.CHANGE_EXPLANATION: [
                "What are the critical changes?",
                "Show changes by category",
                "Explain risk implications"
            ],
            QueryType.RISK_EXPLANATION: [
                "What changes caused high risk?",
                "Show fraud indicators",
                "View compliance status"
            ],
            QueryType.GENERAL: [
                "Summarize the comparison",
                "What are the key findings?",
                "Show me the statistics"
            ]
        }
        return queries_map.get(query_type, ["Tell me about the changes", "What risks were found?"])
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history for display"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in self.conversation_history
        ]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []