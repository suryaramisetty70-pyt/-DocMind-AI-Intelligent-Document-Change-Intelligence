"""
DocMind AI - Change Intelligence
AI-powered change analysis and explanation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import re


class ChangeCategory(Enum):
    """Categories for document changes"""
    FINANCIAL = "financial"
    LEGAL = "legal"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    RISK = "risk"
    SCHEDULE = "schedule"
    SCOPE = "scope"
    QUALITY = "quality"


class ChangePriority(Enum):
    """Priority levels for changes"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ChangeIntelligence:
    """AI-generated intelligence about a change"""
    change_id: str
    explanation: str
    category: ChangeCategory
    priority: ChangePriority
    impact: str
    risk_level: float
    business_implications: List[str]
    recommendations: List[str]
    related_changes: List[str] = field(default_factory=list)


@dataclass
class ChangeIntelligenceReport:
    """Complete change intelligence report"""
    overall_risk_score: float
    critical_changes: List[ChangeIntelligence]
    high_priority_changes: List[ChangeIntelligence]
    changes_by_category: Dict[str, List[ChangeIntelligence]]
    executive_summary: str
    key_findings: List[str]
    recommendations: List[str]
    processing_time: float


class ChangeExplainer:
    """Explain changes in natural language"""
    
    def __init__(self):
        self.templates = {
            "insertion": "The following content was added: {content}",
            "deletion": "The following content was removed: {content}",
            "modification": "Changed from '{original}' to '{modified}'",
            "movement": "Content was moved from {from_loc} to {to_loc}",
            "formatting": "Formatting was changed: {details}"
        }
    
    def explain(self, change: Any) -> str:
        """Generate natural language explanation"""
        change_type = change.change_type.value
        
        if change_type in self.templates:
            template = self.templates[change_type]
            
            if change_type == "insertion":
                return template.format(content=self._truncate(change.modified_content, 100))
            elif change_type == "deletion":
                return template.format(content=self._truncate(change.original_content, 100))
            elif change_type == "modification":
                return template.format(
                    original=self._truncate(change.original_content, 50),
                    modified=self._truncate(change.modified_content, 50)
                )
            elif change_type == "movement":
                return template.format(
                    from_loc=change.metadata.get("from_position", "unknown"),
                    to_loc=change.metadata.get("to_position", "unknown")
                )
        
        return f"{change_type}: {self._truncate(change.original_content or change.modified_content, 100)}"
    
    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text with ellipsis"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."


class ChangeCategorizer:
    """Categorize changes by business impact"""
    
    def __init__(self):
        self.category_keywords = {
            "financial": ["amount", "price", "cost", "fee", "$", "percentage", "%", "payment", "invoice", "budget", "revenue", "profit", "expense"],
            "legal": ["liability", "indemnify", "warranty", "termination", "clause", "jurisdiction", "governing", "law", "legal", "court"],
            "compliance": ["regulation", "compliance", "requirement", "standard", "certification", "audit", "policy", "GDPR", "HIPAA"],
            "operational": ["process", "procedure", "workflow", "approval", "responsible", "owner", "department"],
            "risk": ["risk", "assumption", "contingency", "mitigation", "escalation", "emergency"],
            "schedule": ["deadline", "date", "time", "duration", "milestone", "delay", "timeline"],
            "scope": ["include", "exclude", "deliverable", "requirement", "specification", "feature"]
        }
        
        self.financial_patterns = [
            r'\$\d+',
            r'\d+%',
            r'currency',
            r'amount',
            r'total',
            r'subtotal'
        ]
        
        self.date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}'
        ]
    
    def categorize(self, change: Any) -> ChangeCategory:
        """Categorize a change based on content"""
        content = (change.original_content or "") + " " + (change.modified_content or "")
        content_lower = content.lower()
        
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            category_scores[category] = score
        
        if max(category_scores.values()) > 0:
            return ChangeCategory(max(category_scores, key=category_scores.get))
        
        return ChangeCategory.OPERATIONAL
    
    def is_financial_change(self, change: Any) -> bool:
        """Check if change is financial"""
        content = (change.original_content or "") + " " + (change.modified_content or "")
        
        for pattern in self.financial_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def is_date_change(self, change: Any) -> bool:
        """Check if change involves date modification"""
        content = (change.original_content or "") + " " + (change.modified_content or "")
        
        for pattern in self.date_patterns:
            if re.search(pattern, content):
                return True
        
        return False


class ChangePrioritizer:
    """Prioritize changes by business impact"""
    
    def __init__(self):
        self.severity_weights = {
            "critical": 5,
            "significant": 4,
            "moderate": 3,
            "minor": 2,
            "info": 1
        }
        
        self.category_weights = {
            ChangeCategory.FINANCIAL: 1.5,
            ChangeCategory.LEGAL: 1.4,
            ChangeCategory.COMPLIANCE: 1.4,
            ChangeCategory.RISK: 1.3,
            ChangeCategory.SCHEDULE: 1.1,
            ChangeCategory.SCOPE: 1.0,
            ChangeCategory.OPERATIONAL: 0.9,
            ChangeCategory.QUALITY: 0.8
        }
    
    def prioritize(self, changes: List[Any], context: Optional[Dict[str, Any]] = None) -> List[ChangeIntelligence]:
        """Prioritize changes and generate intelligence"""
        results = []
        
        for idx, change in enumerate(changes):
            # Calculate priority score
            severity_score = self.severity_weights.get(change.severity.value, 2)
            category_weight = self.category_weights.get(change.category, 1.0)
            
            # Check for financial/date manipulation
            categorizer = ChangeCategorizer()
            
            priority_score = severity_score * category_weight
            
            if categorizer.is_financial_change(change):
                priority_score *= 1.5
                category = ChangeCategory.FINANCIAL
            elif categorizer.is_date_change(change):
                priority_score *= 1.2
                category = ChangeCategory.SCHEDULE
            else:
                category = categorizer.categorize(change)
            
            # Determine priority level
            if priority_score >= 8:
                priority = ChangePriority.CRITICAL
            elif priority_score >= 6:
                priority = ChangePriority.HIGH
            elif priority_score >= 4:
                priority = ChangePriority.MEDIUM
            elif priority_score >= 2:
                priority = ChangePriority.LOW
            else:
                priority = ChangePriority.INFO
            
            # Generate explanation
            explainer = ChangeExplainer()
            explanation = explainer.explain(change)
            
            # Generate business implications
            implications = self._generate_implications(change, category)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(change, category, priority)
            
            results.append(ChangeIntelligence(
                change_id=f"change_{idx}",
                explanation=explanation,
                category=category,
                priority=priority,
                impact=self._assess_impact(change, category),
                risk_level=min(priority_score / 10, 1.0),
                business_implications=implications,
                recommendations=recommendations
            ))
        
        # Sort by priority
        results.sort(key=lambda x: (
            self._priority_order(x.priority),
            -x.risk_level
        ), reverse=True)
        
        return results
    
    def _priority_order(self, priority: ChangePriority) -> int:
        """Convert priority to numeric order"""
        order = {
            ChangePriority.CRITICAL: 5,
            ChangePriority.HIGH: 4,
            ChangePriority.MEDIUM: 3,
            ChangePriority.LOW: 2,
            ChangePriority.INFO: 1
        }
        return order.get(priority, 0)
    
    def _assess_impact(self, change: Any, category: ChangeCategory) -> str:
        """Assess impact of change"""
        severity = change.severity.value
        
        impact_templates = {
            ChangeCategory.FINANCIAL: {
                "critical": "Major financial impact expected - requires immediate review",
                "high": "Significant financial implications",
                "medium": "Moderate financial impact",
                "low": "Minor financial consideration"
            },
            ChangeCategory.LEGAL: {
                "critical": "May affect legal rights or obligations - legal review required",
                "high": "Significant legal implications",
                "medium": "Legal considerations apply",
                "low": "Limited legal impact"
            },
            ChangeCategory.COMPLIANCE: {
                "critical": "May affect regulatory compliance - compliance team review required",
                "high": "Compliance implications",
                "medium": "May require compliance check",
                "low": "Minimal compliance impact"
            }
        }
        
        category_impacts = impact_templates.get(category, {
            "critical": "High impact change",
            "high": "Notable change",
            "medium": "Moderate impact",
            "low": "Low impact"
        })
        
        return category_impacts.get(severity, "Impact varies")
    
    def _generate_implications(self, change: Any, category: ChangeCategory) -> List[str]:
        """Generate business implications"""
        implications = []
        
        if category == ChangeCategory.FINANCIAL:
            if "increase" in (change.modified_content or "").lower():
                implications.append("May increase costs or expenses")
            if "decrease" in (change.modified_content or "").lower():
                implications.append("May reduce costs or revenue")
        
        if category == ChangeCategory.LEGAL:
            implications.append("Should be reviewed by legal team")
            implications.append("May affect contract terms")
        
        if category == ChangeCategory.COMPLIANCE:
            implications.append("Compliance review recommended")
            implications.append("May affect regulatory requirements")
        
        return implications if implications else ["Standard review required"]
    
    def _generate_recommendations(self, change: Any, category: ChangeCategory, priority: ChangePriority) -> List[str]:
        """Generate recommendations for change"""
        recommendations = []
        
        if priority in [ChangePriority.CRITICAL, ChangePriority.HIGH]:
            recommendations.append("Immediate review required")
            recommendations.append("Escalate to appropriate stakeholders")
        
        if category == ChangeCategory.FINANCIAL:
            recommendations.append("Verify financial calculations")
            recommendations.append("Consult finance team")
        
        if category == ChangeCategory.LEGAL:
            recommendations.append("Legal review required")
            recommendations.append("Ensure proper documentation")
        
        if category == ChangeCategory.COMPLIANCE:
            recommendations.append("Compliance check needed")
            recommendations.append("Update compliance documentation")
        
        if not recommendations:
            recommendations.append("Standard approval process applies")
        
        return recommendations


class ChangeIntelligenceEngine:
    """Main change intelligence engine"""
    
    def __init__(self):
        self.explainer = ChangeExplainer()
        self.categorizer = ChangeCategorizer()
        self.prioritizer = ChangePrioritizer()
    
    def analyze(self, changes: List[Any], context: Optional[Dict[str, Any]] = None) -> ChangeIntelligenceReport:
        """Analyze changes and generate intelligence report"""
        import time
        start_time = time.time()
        
        # Generate intelligence for each change
        intelligences = self.prioritizer.prioritize(changes, context)
        
        # Categorize by priority
        critical = [i for i in intelligences if i.priority == ChangePriority.CRITICAL]
        high = [i for i in intelligences if i.priority == ChangePriority.HIGH]
        
        # Categorize by category
        by_category = {}
        for intelligence in intelligences:
            cat_name = intelligence.category.value
            if cat_name not in by_category:
                by_category[cat_name] = []
            by_category[cat_name].append(intelligence)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(intelligences, critical, high)
        
        # Generate key findings
        key_findings = self._generate_key_findings(intelligences)
        
        # Generate recommendations
        recommendations = self._generate_overall_recommendations(intelligences)
        
        # Calculate overall risk score
        overall_risk = sum(i.risk_level for i in intelligences) / len(intelligences) if intelligences else 0
        
        return ChangeIntelligenceReport(
            overall_risk_score=overall_risk,
            critical_changes=critical,
            high_priority_changes=high,
            changes_by_category=by_category,
            executive_summary=executive_summary,
            key_findings=key_findings,
            recommendations=recommendations,
            processing_time=time.time() - start_time
        )
    
    def _generate_executive_summary(self, intelligences: List[ChangeIntelligence], critical: List, high: List) -> str:
        """Generate executive summary"""
        total = len(intelligences)
        
        if not intelligences:
            return "No significant changes detected between documents."
        
        summary_parts = [
            f"Analyzed {total} document changes.",
        ]
        
        if critical:
            summary_parts.append(f"Found {len(critical)} critical changes requiring immediate attention.")
        
        if high:
            summary_parts.append(f"Identified {len(high)} high-priority changes for review.")
        
        # Top category
        category_counts = {}
        for i in intelligences:
            cat = i.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        if category_counts:
            top_cat = max(category_counts, key=category_counts.get)
            summary_parts.append(f"Most changes relate to {top_cat} aspects of the document.")
        
        return " ".join(summary_parts)
    
    def _generate_key_findings(self, intelligences: List[ChangeIntelligence]) -> List[str]:
        """Generate key findings"""
        findings = []
        
        # Group by category
        category_groups = {}
        for i in intelligences:
            cat = i.category.value
            if cat not in category_groups:
                category_groups[cat] = []
            category_groups[cat].append(i)
        
        # Key findings per category
        for category, items in category_groups.items():
            count = len(items)
            avg_risk = sum(i.risk_level for i in items) / count
            
            if avg_risk > 0.7:
                findings.append(f"High-risk {category} changes detected: {count} changes with average risk score of {avg_risk:.1%}")
            elif count > 5:
                findings.append(f"Multiple {category} changes found: {count} total changes")
        
        # Critical findings
        critical = [i for i in intelligences if i.priority == ChangePriority.CRITICAL]
        if critical:
            findings.append(f"Critical: {len(critical)} changes require immediate review")
        
        return findings[:5]  # Top 5 findings
    
    def _generate_overall_recommendations(self, intelligences: List[ChangeIntelligence]) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        critical = [i for i in intelligences if i.priority == ChangePriority.CRITICAL]
        if critical:
            recommendations.append("URGENT: Review all critical changes before proceeding")
        
        # Category-specific recommendations
        categories = set(i.category for i in intelligences)
        
        if ChangeCategory.FINANCIAL in categories:
            recommendations.append("Conduct thorough financial impact analysis")
        
        if ChangeCategory.LEGAL in categories:
            recommendations.append("Schedule legal team review for contract changes")
        
        if ChangeCategory.COMPLIANCE in categories:
            recommendations.append("Verify compliance status with regulatory requirements")
        
        if len(intelligences) > 20:
            recommendations.append("Consider implementing staged review process due to volume of changes")
        
        return recommendations[:5]  # Top 5 recommendations


class ChangeEvolutionTracker:
    """Track changes across multiple document versions"""
    
    def __init__(self):
        self.versions = []
        self.change_history = []
    
    def add_version(self, version_id: str, content: str, timestamp: str):
        """Add a new document version"""
        self.versions.append({
            "version_id": version_id,
            "content": content,
            "timestamp": timestamp
        })
    
    def track_evolution(self, original_idx: int, modified_idx: int, changes: List[Any]):
        """Track evolution between versions"""
        self.change_history.append({
            "from_version": self.versions[original_idx]["version_id"] if original_idx < len(self.versions) else None,
            "to_version": self.versions[modified_idx]["version_id"] if modified_idx < len(self.versions) else None,
            "change_count": len(changes),
            "changes": [c.to_dict() for c in changes]
        })
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of document evolution"""
        if not self.change_history:
            return {"message": "No evolution data available"}
        
        total_changes = sum(h["change_count"] for h in self.change_history)
        avg_changes = total_changes / len(self.change_history)
        
        return {
            "versions_count": len(self.versions),
            "transitions_count": len(self.change_history),
            "total_changes": total_changes,
            "average_changes_per_version": avg_changes,
            "change_history": self.change_history
        }