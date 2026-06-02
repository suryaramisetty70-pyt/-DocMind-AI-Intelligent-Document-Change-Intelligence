"""
DocMind AI - Negotiation Assistant
AI-powered analysis of document changes from negotiation perspective
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class Party(Enum):
    """Parties in negotiation"""
    ORIGINAL = "original"
    MODIFIED = "modified"
    NEUTRAL = "neutral"


class PositionType(Enum):
    """Position type in negotiation"""
    AGGRESSIVE = "aggressive"
    MODERATE = "moderate"
    CONCESSIVE = "concessive"
    NEUTRAL = "neutral"


@dataclass
class PartyPosition:
    """Position analysis for a party"""
    party: Party
    position_type: PositionType
    favor_score: float  # -1 to 1, negative = original favored, positive = modified favored
    key_benefits: List[str]
    key_concessions: List[str]
    leverage_points: List[str]


@dataclass
class NegotiationAnalysis:
    """Complete negotiation analysis"""
    overall_assessment: str
    party_positions: List[PartyPosition]
    balance_score: float  # 0 = equal, positive = modified favored
    critical_deal_points: List[Dict[str, Any]]
    recommendations: List[str]
    risk_factors: List[str]
    next_steps: List[str]


class DealPointAnalyzer:
    """Analyze specific deal points in documents"""
    
    def __init__(self):
        self.deal_categories = {
            "price": ["price", "cost", "fee", "rate", "amount", "payment", "$", "USD"],
            "timeline": ["deadline", "date", "time", "duration", "milestone", "delivery"],
            "scope": ["include", "exclude", "scope", "deliverable", "service", "product"],
            "liability": ["liability", "indemnify", "warranty", "limitation", "damages"],
            "termination": ["terminate", "cancel", "end", "close", "exit"],
            "confidentiality": ["confidential", "proprietary", "secret", "NDAs", "disclosure"]
        }
    
    def analyze_deal_points(self, changes: List[Any]) -> List[Dict[str, Any]]:
        """Analyze changes by deal point category"""
        deal_points = []
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            content_lower = content.lower()
            
            # Categorize the change
            category = "other"
            for cat, keywords in self.deal_categories.items():
                if any(kw.lower() in content_lower for kw in keywords):
                    category = cat
                    break
            
            # Determine impact
            impact = self._analyze_impact(change)
            
            deal_points.append({
                "category": category,
                "change_id": id(change),
                "original": change.original_content[:100] if change.original_content else "",
                "modified": change.modified_content[:100] if change.modified_content else "",
                "impact": impact,
                "severity": change.severity.value,
                "position": self._determine_position(change)
            })
        
        return deal_points
    
    def _analyze_impact(self, change: Any) -> str:
        """Analyze impact of a change"""
        if change.change_type.value == "insertion":
            return "addition"
        elif change.change_type.value == "deletion":
            return "removal"
        elif change.change_type.value == "modification":
            # Would need more context to determine increase/decrease
            return "modification"
        return "unknown"
    
    def _determine_position(self, change: Any) -> str:
        """Determine which party benefits"""
        # This is simplified - real implementation would need more context
        if change.category.value in ["financial", "liability", "termination"]:
            return "modified"  # Often modified party benefits
        return "neutral"


class LeverageAnalyzer:
    """Analyze leverage points in negotiation"""
    
    def analyze(self, changes: List[Any], original_text: str, modified_text: str) -> Dict[str, Any]:
        """Analyze leverage points"""
        leverage = {
            "original_party": [],
            "modified_party": [],
            "neutral": []
        }
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            
            # Analyze leverage based on change type and category
            if change.severity.value == "critical":
                if change.category.value == "financial":
                    leverage["modified_party"].append({
                        "leverage_type": "financial",
                        "description": "Critical financial terms modified",
                        "potential_gain": self._estimate_financial_impact(change)
                    })
            
            if change.category.value == "liability":
                leverage["modified_party"].append({
                    "leverage_type": "liability",
                    "description": "Liability terms changed",
                    "risk_reduction": "High"
                })
        
        return leverage
    
    def _estimate_financial_impact(self, change: Any) -> str:
        """Estimate financial impact"""
        # Simplified estimation
        if "$" in change.modified_content or "amount" in change.modified_content.lower():
            return "High"
        return "Medium"


class BalanceScorer:
    """Score the balance of changes between parties"""
    
    def calculate(self, changes: List[Any], deal_points: List[Dict[str, Any]]) -> float:
        """Calculate balance score"""
        # -1 = original heavily favored, 0 = balanced, 1 = modified heavily favored
        
        scores = []
        
        for dp in deal_points:
            severity_weight = {
                "critical": 3,
                "significant": 2,
                "moderate": 1,
                "minor": 0.5
            }.get(dp.get("severity", "minor"), 1)
            
            position = dp.get("position", "neutral")
            position_score = {
                "original": -1,
                "modified": 1,
                "neutral": 0
            }.get(position, 0)
            
            scores.append(position_score * severity_weight)
        
        if scores:
            return sum(scores) / len(scores)
        
        return 0.0


class NegotiationAssistant:
    """Main negotiation assistant"""
    
    def __init__(self):
        self.deal_analyzer = DealPointAnalyzer()
        self.leverage_analyzer = LeverageAnalyzer()
        self.balance_scorer = BalanceScorer()
    
    def analyze(
        self,
        changes: List[Any],
        original_text: str,
        modified_text: str,
        party_labels: Optional[Dict[str, str]] = None
    ) -> NegotiationAnalysis:
        """Perform comprehensive negotiation analysis"""
        
        # Analyze deal points
        deal_points = self.deal_analyzer.analyze_deal_points(changes)
        
        # Analyze leverage
        leverage = self.leverage_analyzer.analyze(changes, original_text, modified_text)
        
        # Calculate balance
        balance_score = self.balance_scorer.calculate(changes, deal_points)
        
        # Determine party positions
        party_positions = self._determine_party_positions(balance_score, leverage, party_labels)
        
        # Identify critical deal points
        critical_deal_points = self._identify_critical_deal_points(deal_points)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(balance_score, deal_points)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(changes, balance_score)
        
        # Generate next steps
        next_steps = self._generate_next_steps(balance_score, critical_deal_points)
        
        # Overall assessment
        overall_assessment = self._generate_assessment(balance_score, party_positions)
        
        return NegotiationAnalysis(
            overall_assessment=overall_assessment,
            party_positions=party_positions,
            balance_score=balance_score,
            critical_deal_points=critical_deal_points,
            recommendations=recommendations,
            risk_factors=risk_factors,
            next_steps=next_steps
        )
    
    def _determine_party_positions(
        self,
        balance_score: float,
        leverage: Dict[str, Any],
        party_labels: Optional[Dict[str, str]]
    ) -> List[PartyPosition]:
        """Determine positions for each party"""
        positions = []
        
        # Original party position
        orig_leverage = leverage.get("original_party", [])
        orig_score = balance_score * -1  # Invert for original party
        
        positions.append(PartyPosition(
            party=Party.ORIGINAL,
            position_type=self._score_to_position(orig_score),
            favor_score=orig_score,
            key_benefits=["Current terms maintained"] if orig_score > 0 else [],
            key_concessions=["Terms changed"] if orig_score < 0 else [],
            leverage_points=[l["description"] for l in orig_leverage]
        ))
        
        # Modified party position
        mod_leverage = leverage.get("modified_party", [])
        
        positions.append(PartyPosition(
            party=Party.MODIFIED,
            position_type=self._score_to_position(balance_score),
            favor_score=balance_score,
            key_benefits=[l["description"] for l in mod_leverage],
            key_concessions=[],
            leverage_points=[l["description"] for l in mod_leverage]
        ))
        
        return positions
    
    def _score_to_position(self, score: float) -> PositionType:
        """Convert score to position type"""
        if score < -0.3:
            return PositionType.AGGRESSIVE
        elif score < 0:
            return PositionType.CONCESSIVE
        elif score == 0:
            return PositionType.NEUTRAL
        elif score < 0.3:
            return PositionType.MODERATE
        else:
            return PositionType.AGGRESSIVE
    
    def _identify_critical_deal_points(self, deal_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify critical deal points"""
        critical = []
        
        for dp in deal_points:
            if dp.get("severity") == "critical":
                critical.append({
                    "category": dp.get("category"),
                    "description": f"{dp.get('impact').title()} in {dp.get('category')}",
                    "original": dp.get("original"),
                    "modified": dp.get("modified")
                })
        
        return critical[:5]  # Top 5
    
    def _generate_recommendations(self, balance_score: float, deal_points: List[Dict[str, Any]]) -> List[str]:
        """Generate negotiation recommendations"""
        recommendations = []
        
        if balance_score > 0.3:
            recommendations.append("Modified version heavily favors one party - review terms carefully")
            recommendations.append("Consider requesting additional concessions")
        
        if balance_score < -0.3:
            recommendations.append("Original terms significantly altered - verify all changes")
            recommendations.append("May need to renegotiate critical points")
        
        # Category-specific recommendations
        categories = [dp.get("category") for dp in deal_points]
        
        if "price" in categories:
            recommendations.append("Review all financial terms carefully")
        
        if "liability" in categories:
            recommendations.append("Liability changes require legal review")
        
        if not recommendations:
            recommendations.append("Changes appear balanced - proceed with standard review")
        
        return list(set(recommendations))[:5]  # Top 5 unique
    
    def _identify_risk_factors(self, changes: List[Any], balance_score: float) -> List[str]:
        """Identify risk factors"""
        risks = []
        
        # Unbalanced changes
        if abs(balance_score) > 0.5:
            risks.append("Highly unbalanced changes - potential negotiation issue")
        
        # Critical changes
        critical_count = sum(1 for c in changes if c.severity.value == "critical")
        if critical_count > 3:
            risks.append(f"Multiple critical changes ({critical_count}) - requires careful review")
        
        # Financial changes
        financial_count = sum(1 for c in changes if c.category.value == "financial")
        if financial_count > 0:
            risks.append(f"{financial_count} financial terms modified - verify amounts")
        
        return risks[:5]
    
    def _generate_next_steps(self, balance_score: float, critical_points: List[Dict]) -> List[str]:
        """Generate next steps for negotiation"""
        steps = []
        
        if abs(balance_score) > 0.3:
            steps.append("Schedule negotiation session to discuss unbalanced terms")
        
        if critical_points:
            steps.append("Prioritize review of critical deal points")
        
        steps.append("Prepare counter-proposals for unfavorable changes")
        steps.append("Document all concerns for records")
        
        return steps[:4]
    
    def _generate_assessment(self, balance_score: float, positions: List[PartyPosition]) -> str:
        """Generate overall negotiation assessment"""
        if abs(balance_score) < 0.2:
            return "Changes appear balanced between parties. Standard review process recommended."
        
        favored_party = "modified" if balance_score > 0 else "original"
        
        return (
            f"Analysis indicates the {favored_party} version benefits one party "
            f"with a balance score of {balance_score:.2f}. "
            f"Review of critical points and potential renegotiation may be needed."
        )


class NegotiationReportGenerator:
    """Generate negotiation reports"""
    
    def generate_markdown(self, analysis: NegotiationAnalysis) -> str:
        """Generate Markdown report"""
        md = f"""# Negotiation Analysis Report

## Overall Assessment

{analysis.overall_assessment}

## Balance Score

**Score: {analysis.balance_score:.2f}** ({-1} = Original Favored, {+1} = Modified Favored)

## Party Positions

"""
        for position in analysis.party_positions:
            md += f"""### {position.party.value.title()} Party

- **Position Type:** {position.position_type.value}
- **Favor Score:** {position.favor_score:.2f}
- **Key Benefits:** {', '.join(position.key_benefits) or 'None identified'}
- **Key Concessions:** {', '.join(position.key_concessions) or 'None identified'}
- **Leverage Points:** {', '.join(position.leverage_points) or 'None identified'}

"""
        
        if analysis.critical_deal_points:
            md += "## Critical Deal Points\n\n"
            for i, point in enumerate(analysis.critical_deal_points, 1):
                md += f"{i}. **{point['category'].title()}**: {point['description']}\n"
                md += f"   - Original: {point['original']}\n"
                md += f"   - Modified: {point['modified']}\n\n"
        
        if analysis.recommendations:
            md += "## Recommendations\n\n"
            for rec in analysis.recommendations:
                md += f"- {rec}\n"
        
        if analysis.next_steps:
            md += "\n## Next Steps\n\n"
            for step in analysis.next_steps:
                md += f"- {step}\n"
        
        return md