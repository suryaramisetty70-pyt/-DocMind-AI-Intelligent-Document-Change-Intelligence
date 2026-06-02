"""
DocMind AI - Executive Summary Generator
AI-powered document comparison summary generation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class ExecutiveSummary:
    """Executive summary of document comparison"""
    title: str
    generated_at: datetime
    overview: str
    key_changes: List[Dict[str, Any]]
    critical_findings: List[str]
    recommendations: List[str]
    statistics: Dict[str, Any]
    risk_summary: Dict[str, Any]
    fraud_summary: Dict[str, Any]
    compliance_summary: Dict[str, Any]
    next_steps: List[str]
    attachments: List[str] = field(default_factory=list)


class ExecutiveSummaryGenerator:
    """Generate executive summaries for document comparisons"""
    
    def __init__(self):
        self.templates = {
            "overview": "Document comparison between {doc1} and {doc2} reveals {change_summary}.",
            "key_changes": "The comparison identified {count} significant changes including {top_categories}.",
            "critical": "Critical findings require immediate attention: {findings}",
            "recommendations": "Based on the analysis, the following actions are recommended: {actions}"
        }
    
    def generate(
        self,
        comparison_result: Any,
        semantic_result: Any,
        risk_result: Any,
        fraud_result: Any,
        similarity_result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExecutiveSummary:
        """Generate comprehensive executive summary"""
        
        # Extract key information
        total_changes = len(comparison_result.changes) if comparison_result else 0
        critical_count = self._count_by_severity(comparison_result, "critical")
        high_count = self._count_by_severity(comparison_result, "significant")
        
        # Generate overview
        overview = self._generate_overview(
            metadata or {},
            total_changes,
            similarity_result.overall_similarity if similarity_result else 0
        )
        
        # Generate key changes
        key_changes = self._extract_key_changes(comparison_result, limit=10)
        
        # Generate critical findings
        critical_findings = self._generate_critical_findings(
            comparison_result,
            risk_result,
            fraud_result
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            comparison_result,
            risk_result,
            fraud_result
        )
        
        # Generate statistics
        statistics = self._compile_statistics(
            comparison_result,
            semantic_result,
            similarity_result
        )
        
        # Generate risk summary
        risk_summary = self._generate_risk_summary(risk_result)
        
        # Generate fraud summary
        fraud_summary = self._generate_fraud_summary(fraud_result)
        
        # Generate compliance summary
        compliance_summary = self._generate_compliance_summary(risk_result)
        
        # Generate next steps
        next_steps = self._generate_next_steps(
            critical_findings,
            risk_result,
            fraud_result
        )
        
        return ExecutiveSummary(
            title=f"Document Comparison Report - {metadata.get('document_name', 'Comparison')}",
            generated_at=datetime.now(),
            overview=overview,
            key_changes=key_changes,
            critical_findings=critical_findings,
            recommendations=recommendations,
            statistics=statistics,
            risk_summary=risk_summary,
            fraud_summary=fraud_summary,
            compliance_summary=compliance_summary,
            next_steps=next_steps
        )
    
    def _generate_overview(self, metadata: Dict, total_changes: int, similarity: float) -> str:
        """Generate overview section"""
        similarity_pct = int(similarity * 100)
        
        if similarity >= 0.95:
            similarity_desc = "nearly identical documents"
        elif similarity >= 0.80:
            similarity_desc = "minor differences"
        elif similarity >= 0.60:
            similarity_desc = "moderate changes"
        else:
            similarity_desc = "significant modifications"
        
        return (
            f"Analysis of {metadata.get('document_name', 'documents')} reveals {similarity_desc} "
            f"with {total_changes} total changes identified. "
            f"Document similarity is {similarity_pct}%. "
            f"This comparison was performed on {metadata.get('timestamp', datetime.now().strftime('%Y-%m-%d'))}."
        )
    
    def _extract_key_changes(self, comparison_result: Any, limit: int = 10) -> List[Dict[str, Any]]:
        """Extract most significant changes"""
        if not comparison_result or not comparison_result.changes:
            return []
        
        # Sort by severity
        severity_order = {"critical": 0, "significant": 1, "moderate": 2, "minor": 3}
        sorted_changes = sorted(
            comparison_result.changes,
            key=lambda c: severity_order.get(c.severity.value, 4)
        )
        
        key_changes = []
        for change in sorted_changes[:limit]:
            key_changes.append({
                "type": change.change_type.value,
                "severity": change.severity.value,
                "category": change.category.value,
                "original": self._truncate(change.original_content, 100),
                "modified": self._truncate(change.modified_content, 100),
                "location": {
                    "page": change.location.page,
                    "section": change.location.section
                }
            })
        
        return key_changes
    
    def _generate_critical_findings(
        self,
        comparison_result: Any,
        risk_result: Any,
        fraud_result: Any
    ) -> List[str]:
        """Generate critical findings"""
        findings = []
        
        # From comparison
        if comparison_result and comparison_result.changes:
            critical = [c for c in comparison_result.changes if c.severity.value == "critical"]
            if critical:
                findings.append(f"{len(critical)} critical changes detected requiring immediate review")
        
        # From risk analysis
        if risk_result and hasattr(risk_result, 'indicators'):
            high_risk = [i for i in risk_result.indicators if i.score >= 0.8]
            if high_risk:
                findings.append(f"{len(high_risk)} high-risk indicators identified in risk analysis")
        
        # From fraud detection
        if fraud_result and fraud_result.indicators:
            critical_fraud = [i for i in fraud_result.indicators if i.severity.value == "critical"]
            if critical_fraud:
                findings.append(f"{len(critical_fraud)} critical fraud indicators detected")
        
        # Similarity-based findings
        if comparison_result:
            if comparison_result.overall_similarity < 0.5:
                findings.append("Documents are significantly different - thorough review recommended")
        
        return findings[:5]  # Limit to 5 findings
    
    def _generate_recommendations(
        self,
        comparison_result: Any,
        risk_result: Any,
        fraud_result: Any
    ) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        # Based on fraud detection
        if fraud_result and fraud_result.fraud_score > 0.5:
            recommendations.append("Conduct thorough fraud investigation before proceeding")
            recommendations.append("Verify all critical changes with original stakeholders")
        
        # Based on risk analysis
        if risk_result and risk_result.risk_level.value in ["critical", "high"]:
            recommendations.append("Escalate to executive leadership for review")
            recommendations.append("Schedule urgent review meeting with legal and compliance teams")
        
        # Based on comparison
        if comparison_result:
            critical_count = self._count_by_severity(comparison_result, "critical")
            if critical_count > 0:
                recommendations.append(f"Review all {critical_count} critical changes immediately")
        
        # Default recommendations
        if not recommendations:
            recommendations.append("Proceed with standard approval process")
            recommendations.append("Document review completed - no critical issues found")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _compile_statistics(
        self,
        comparison_result: Any,
        semantic_result: Any,
        similarity_result: Any
    ) -> Dict[str, Any]:
        """Compile comparison statistics"""
        stats = {
            "comparison": {},
            "semantic": {},
            "similarity": {}
        }
        
        if comparison_result and comparison_result.statistics:
            stats["comparison"] = {
                "total_changes": comparison_result.statistics.get("total_changes", 0),
                "insertions": comparison_result.statistics.get("insertions", 0),
                "deletions": comparison_result.statistics.get("deletions", 0),
                "modifications": comparison_result.statistics.get("modifications", 0),
                "by_severity": comparison_result.statistics.get("by_severity", {}),
                "by_category": comparison_result.statistics.get("by_category", {})
            }
        
        if semantic_result and hasattr(semantic_result, 'statistics'):
            stats["semantic"] = {
                "overall_similarity": semantic_result.overall_semantic_similarity,
                "meaning_preserved": semantic_result.statistics.get("meaning_preserved_count", 0),
                "meaning_altered": semantic_result.statistics.get("meaning_altered_count", 0),
                "paraphrased": semantic_result.statistics.get("paraphrased_count", 0)
            }
        
        if similarity_result:
            stats["similarity"] = {
                "overall": similarity_result.overall_similarity,
                "semantic": similarity_result.semantic_similarity,
                "structural": similarity_result.structural_similarity,
                "lexical": similarity_result.lexical_similarity
            }
        
        return stats
    
    def _generate_risk_summary(self, risk_result: Any) -> Dict[str, Any]:
        """Generate risk summary"""
        if not risk_result:
            return {"overall_risk": 0, "level": "unknown", "summary": "No risk analysis performed"}
        
        return {
            "overall_risk": risk_result.overall_risk_score,
            "level": risk_result.risk_level.value if hasattr(risk_result, 'risk_level') else "unknown",
            "financial_risk": risk_result.financial_risk if hasattr(risk_result, 'financial_risk') else 0,
            "legal_risk": risk_result.legal_risk if hasattr(risk_result, 'legal_risk') else 0,
            "compliance_risk": risk_result.compliance_risk if hasattr(risk_result, 'compliance_risk') else 0,
            "operational_risk": risk_result.operational_risk if hasattr(risk_result, 'operational_risk') else 0,
            "risk_factors": risk_result.risk_factors[:5] if hasattr(risk_result, 'risk_factors') else []
        }
    
    def _generate_fraud_summary(self, fraud_result: Any) -> Dict[str, Any]:
        """Generate fraud detection summary"""
        if not fraud_result:
            return {"fraud_score": 0, "level": "clean", "summary": "No fraud indicators detected"}
        
        return {
            "fraud_score": fraud_result.fraud_score,
            "level": fraud_result.fraud_level.value if hasattr(fraud_result, 'fraud_level') else "unknown",
            "total_indicators": len(fraud_result.indicators),
            "critical_findings": len(fraud_result.critical_findings) if hasattr(fraud_result, 'critical_findings') else 0,
            "fraud_types": [i.fraud_type.value for i in fraud_result.indicators[:5]] if hasattr(fraud_result, 'indicators') else []
        }
    
    def _generate_compliance_summary(self, risk_result: Any) -> Dict[str, Any]:
        """Generate compliance summary"""
        if not risk_result or not hasattr(risk_result, 'compliance_checks'):
            return {"checks_passed": True, "missing_clauses": [], "frameworks_affected": []}
        
        return {
            "checks_passed": risk_result.compliance_checks.get("clause_check_passed", True),
            "missing_mandatory_clauses": risk_result.compliance_checks.get("missing_mandatory_clauses", []),
            "gdpr_applicable": risk_result.compliance_checks.get("gdpr_applicable", False),
            "hipaa_applicable": risk_result.compliance_checks.get("hipaa_applicable", False)
        }
    
    def _generate_next_steps(
        self,
        critical_findings: List[str],
        risk_result: Any,
        fraud_result: Any
    ) -> List[str]:
        """Generate next steps"""
        steps = []
        
        if fraud_result and fraud_result.fraud_score > 0.5:
            steps.append("1. Conduct fraud investigation (Priority: URGENT)")
        
        if risk_result and risk_result.risk_level.value in ["critical", "high"]:
            steps.append("2. Schedule executive review meeting")
            steps.append("3. Engage legal and compliance teams")
        
        if critical_findings:
            steps.append("4. Review all critical findings in detail")
        
        steps.append("5. Update stakeholders with analysis results")
        steps.append("6. Document decision rationale for changes")
        
        return steps
    
    def _count_by_severity(self, comparison_result: Any, severity: str) -> int:
        """Count changes by severity"""
        if not comparison_result or not comparison_result.changes:
            return 0
        
        stats = comparison_result.statistics.get("by_severity", {})
        return stats.get(severity, 0)
    
    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    def to_json(self, summary: ExecutiveSummary) -> str:
        """Convert summary to JSON"""
        return json.dumps({
            "title": summary.title,
            "generated_at": summary.generated_at.isoformat(),
            "overview": summary.overview,
            "key_changes": summary.key_changes,
            "critical_findings": summary.critical_findings,
            "recommendations": summary.recommendations,
            "statistics": summary.statistics,
            "risk_summary": summary.risk_summary,
            "fraud_summary": summary.fraud_summary,
            "compliance_summary": summary.compliance_summary,
            "next_steps": summary.next_steps,
            "attachments": summary.attachments
        }, indent=2)
    
    def to_markdown(self, summary: ExecutiveSummary) -> str:
        """Convert summary to Markdown"""
        md = f"""# {summary.title}

**Generated:** {summary.generated_at.strftime('%Y-%m-%d %H:%M:%S')}

## Overview

{summary.overview}

## Key Statistics

- Total Changes: {summary.statistics.get('comparison', {}).get('total_changes', 0)}
- Similarity: {int(summary.statistics.get('similarity', {}).get('overall', 0) * 100)}%
- Overall Risk: {summary.risk_summary.get('overall_risk', 0):.1%}

## Critical Findings

"""
        for finding in summary.critical_findings:
            md += f"- {finding}\n"
        
        md += "\n## Key Changes\n\n"
        for idx, change in enumerate(summary.key_changes[:5], 1):
            md += f"{idx}. **[{change['severity'].upper()}]** {change['type']}: {change['original']} → {change['modified']}\n"
        
        md += "\n## Recommendations\n\n"
        for rec in summary.recommendations:
            md += f"- {rec}\n"
        
        md += "\n## Next Steps\n\n"
        for step in summary.next_steps:
            md += f"- {step}\n"
        
        return md