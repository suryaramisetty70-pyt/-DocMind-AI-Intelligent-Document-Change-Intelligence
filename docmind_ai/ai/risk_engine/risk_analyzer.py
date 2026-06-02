"""
DocMind AI - Risk Analysis Engine
Comprehensive risk detection and assessment for document changes
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import re
from datetime import datetime


class RiskCategory(Enum):
    """Categories of risk"""
    FINANCIAL = "financial"
    LEGAL = "legal"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    REPUTATIONAL = "reputational"
    STRATEGIC = "strategic"


class RiskLevel(Enum):
    """Risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class RiskIndicator:
    """Individual risk indicator"""
    name: str
    category: RiskCategory
    score: float
    description: str
    evidence: List[str]
    mitigation: Optional[str] = None


@dataclass
class RiskAnalysisResult:
    """Complete risk analysis result"""
    overall_risk_score: float
    risk_level: RiskLevel
    financial_risk: float
    legal_risk: float
    compliance_risk: float
    operational_risk: float
    indicators: List[RiskIndicator]
    risk_factors: List[str]
    recommendations: List[str]
    compliance_checks: Dict[str, Any]
    processing_time: float


class FinancialRiskAnalyzer:
    """Analyze financial risks in document changes"""
    
    def __init__(self):
        self.amount_patterns = [
            r'\$\s*[\d,]+\.?\d*',
            r'USD\s*[\d,]+\.?\d*',
            r'EUR\s*[\d,]+\.?\d*',
            r'GBP\s*[\d,]+\.?\d*',
            r'INR\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:dollars?|euros?|pounds?|rupees?)',
            r'[\d,]+\.?\d*\s*(?:percent|%)'
        ]
        
        self.financial_keywords = [
            "payment", "invoice", "fee", "cost", "price", "rate", "budget", "expense",
            "revenue", "profit", "loss", "credit", "debit", "tax", "interest",
            "penalty", "fine", "compensation", "indemnity", "liability"
        ]
    
    def analyze(self, changes: List[Any], original_text: str, modified_text: str) -> Dict[str, Any]:
        """Analyze financial risks"""
        risks = []
        
        # Extract amounts from both documents
        orig_amounts = self._extract_amounts(original_text)
        mod_amounts = self._extract_amounts(modified_text)
        
        # Detect amount manipulation
        amount_changes = self._detect_amount_changes(changes)
        if amount_changes:
            risks.append(RiskIndicator(
                name="Amount Manipulation Detected",
                category=RiskCategory.FINANCIAL,
                score=0.9,
                description=f"Found {len(amount_changes)} potential amount changes",
                evidence=[str(c) for c in amount_changes[:3]]
            ))
        
        # Check for percentage changes
        pct_changes = self._detect_percentage_changes(changes)
        if pct_changes:
            risks.append(RiskIndicator(
                name="Percentage Rate Changes",
                category=RiskCategory.FINANCIAL,
                score=0.85,
                description=f"Found {len(pct_changes)} percentage/rate modifications",
                evidence=[str(c) for c in pct_changes[:3]]
            ))
        
        # Financial keyword analysis
        fin_risk = self._analyze_financial_keywords(changes)
        if fin_risk > 0.7:
            risks.append(RiskIndicator(
                name="High Financial Content Change",
                category=RiskCategory.FINANCIAL,
                score=fin_risk,
                description="Significant changes to financial terms",
                evidence=[]
            ))
        
        # Calculate financial risk score
        financial_score = 0.0
        if risks:
            financial_score = max(r.score for r in risks)
            for r in risks:
                financial_score += r.score * 0.2
        
        return {
            "score": min(financial_score, 1.0),
            "indicators": risks,
            "amount_changes_count": len(amount_changes),
            "percentage_changes_count": len(pct_changes)
        }
    
    def _extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """Extract monetary amounts from text"""
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amounts.append({
                    "text": match.group(),
                    "position": match.start(),
                    "amount": self._parse_amount(match.group())
                })
        
        return amounts
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', amount_str)
        try:
            return float(cleaned)
        except:
            return 0.0
    
    def _detect_amount_changes(self, changes: List[Any]) -> List[Any]:
        """Detect changes involving monetary amounts"""
        amount_changes = []
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            
            has_orig_amount = bool(self._extract_amounts(change.original_content or ""))
            has_mod_amount = bool(self._extract_amounts(change.modified_content or ""))
            
            if (has_orig_amount or has_mod_amount):
                amount_changes.append(change)
        
        return amount_changes
    
    def _detect_percentage_changes(self, changes: List[Any]) -> List[Any]:
        """Detect changes involving percentages"""
        pct_changes = []
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            
            if re.search(r'\d+\s*%', content):
                pct_changes.append(change)
        
        return pct_changes
    
    def _analyze_financial_keywords(self, changes: List[Any]) -> float:
        """Analyze presence of financial keywords in changes"""
        fin_count = 0
        total = len(changes)
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            content_lower = content.lower()
            
            if any(kw in content_lower for kw in self.financial_keywords):
                fin_count += 1
        
        return fin_count / total if total > 0 else 0.0


class LegalRiskAnalyzer:
    """Analyze legal risks in document changes"""
    
    def __init__(self):
        self.legal_keywords = [
            "liability", "indemnify", "warranty", "termination", "breach",
            "covenant", "clause", "jurisdiction", "governing law", "arbitration",
            "dispute resolution", "litigation", "injunction", "damages",
            "penalty", "remedy", "force majeure", "confidentiality",
            "non-compete", "non-solicitation", "intellectual property",
            "patent", "trademark", "copyright", "license", "assignment"
        ]
        
        self.critical_terms = [
            "unlimited liability", "waive", "forefeit", "sole discretion",
            "terminate immediately", "without notice", "indemnify and hold harmless"
        ]
    
    def analyze(self, changes: List[Any], original_text: str, modified_text: str) -> Dict[str, Any]:
        """Analyze legal risks"""
        risks = []
        
        # Legal term changes
        legal_changes = self._detect_legal_changes(changes)
        if legal_changes:
            risks.append(RiskIndicator(
                name="Legal Term Modifications",
                category=RiskCategory.LEGAL,
                score=0.8,
                description=f"Found {len(legal_changes)} changes to legal terms",
                evidence=self._extract_legal_evidence(legal_changes)
            ))
        
        # Critical term analysis
        critical_changes = self._detect_critical_term_changes(changes)
        if critical_changes:
            risks.append(RiskIndicator(
                name="Critical Legal Terms Changed",
                category=RiskCategory.LEGAL,
                score=0.95,
                description="Changes to critical legal terms detected - HIGH RISK",
                evidence=[c.original_content[:100] + "..." for c in critical_changes[:3]]
            ))
        
        # Liability clause changes
        liability_changes = self._detect_liability_changes(changes)
        if liability_changes:
            risks.append(RiskIndicator(
                name="Liability Clause Modifications",
                category=RiskCategory.LEGAL,
                score=0.9,
                description="Changes to liability clauses detected",
                evidence=self._extract_legal_evidence(liability_changes)
            ))
        
        # Calculate legal risk score
        legal_score = 0.0
        if risks:
            legal_score = max(r.score for r in risks)
        
        return {
            "score": min(legal_score, 1.0),
            "indicators": risks,
            "legal_changes_count": len(legal_changes),
            "critical_terms_count": len(critical_changes),
            "liability_changes_count": len(liability_changes)
        }
    
    def _detect_legal_changes(self, changes: List[Any]) -> List[Any]:
        """Detect changes involving legal terms"""
        legal_changes = []
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            content_lower = content.lower()
            
            if any(kw in content_lower for kw in self.legal_keywords):
                legal_changes.append(change)
        
        return legal_changes
    
    def _detect_critical_term_changes(self, changes: List[Any]) -> List[Any]:
        """Detect changes to critical legal terms"""
        critical_changes = []
        
        for change in changes:
            orig_lower = (change.original_content or "").lower()
            mod_lower = (change.modified_content or "").lower()
            
            for term in self.critical_terms:
                if term in orig_lower or term in mod_lower:
                    critical_changes.append(change)
                    break
        
        return critical_changes
    
    def _detect_liability_changes(self, changes: List[Any]) -> List[Any]:
        """Detect changes to liability-related clauses"""
        liability_keywords = ["liability", "liable", "indemnify", "indemnification", "hold harmless"]
        
        liability_changes = []
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            
            if any(kw in content.lower() for kw in liability_keywords):
                liability_changes.append(change)
        
        return liability_changes
    
    def _extract_legal_evidence(self, changes: List[Any]) -> List[str]:
        """Extract evidence from legal changes"""
        evidence = []
        for change in changes[:3]:
            text = (change.original_content or change.modified_content or "")[:100]
            evidence.append(text + "..." if len(text) == 100 else text)
        return evidence


class ComplianceRiskAnalyzer:
    """Analyze compliance risks in document changes"""
    
    def __init__(self):
        self.compliance_keywords = {
            "GDPR": ["personal data", "data subject", "processing", "consent", "data protection", "privacy"],
            "HIPAA": ["protected health information", "PHI", "medical", "health record", "healthcare"],
            "SOX": ["internal control", "financial reporting", "audit", "disclosure", "compliance officer"],
            "ISO": ["quality", "standard", "certification", "ISO 9001", "ISO 27001"],
            "PCI-DSS": ["payment card", "credit card", "cardholder", "payment gateway"]
        }
        
        self.mandatory_sections = [
            "termination", "governing law", "confidentiality", "indemnification",
            "force majeure", "notice", "amendment", "entire agreement"
        ]
    
    def analyze(self, changes: List[Any], original_text: str, modified_text: str) -> Dict[str, Any]:
        """Analyze compliance risks"""
        risks = []
        
        # Detect removed mandatory clauses
        removed_clauses = self._detect_removed_clauses(changes, original_text, modified_text)
        if removed_clauses:
            risks.append(RiskIndicator(
                name="Mandatory Clauses Removed",
                category=RiskCategory.COMPLIANCE,
                score=0.95,
                description=f"Required clauses may have been removed: {', '.join(removed_clauses)}",
                evidence=removed_clauses
            ))
        
        # Regulatory framework changes
        framework_changes = self._detect_framework_changes(changes)
        if framework_changes:
            risks.append(RiskIndicator(
                name="Regulatory Framework Affected",
                category=RiskCategory.COMPLIANCE,
                score=0.85,
                description=f"Changes may affect {len(framework_changes)} regulatory frameworks",
                evidence=[f["framework"] for f in framework_changes]
            ))
        
        # Compliance language changes
        compliance_changes = self._detect_compliance_language_changes(changes)
        if compliance_changes:
            risks.append(RiskIndicator(
                name="Compliance Language Modified",
                category=RiskCategory.COMPLIANCE,
                score=0.75,
                description="Compliance-related language has been modified",
                evidence=[c.modified_content[:100] + "..." for c in compliance_changes[:3]]
            ))
        
        # Calculate compliance risk score
        compliance_score = 0.0
        if risks:
            compliance_score = max(r.score for r in risks)
        
        return {
            "score": min(compliance_score, 1.0),
            "indicators": risks,
            "removed_clauses": removed_clauses,
            "framework_changes": framework_changes,
            "compliance_changes_count": len(compliance_changes)
        }
    
    def _detect_removed_clauses(self, changes: List[Any], original: str, modified: str) -> List[str]:
        """Detect if mandatory clauses were removed"""
        removed = []
        
        for clause in self.mandatory_sections:
            if clause.lower() in original.lower() and clause.lower() not in modified.lower():
                removed.append(clause)
        
        return removed
    
    def _detect_framework_changes(self, changes: List[Any]) -> List[Dict[str, Any]]:
        """Detect changes affecting regulatory frameworks"""
        framework_changes = []
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            content_lower = content.lower()
            
            for framework, keywords in self.compliance_keywords.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        framework_changes.append({
                            "framework": framework,
                            "keyword": keyword,
                            "change_id": id(change)
                        })
        
        return framework_changes
    
    def _detect_compliance_language_changes(self, changes: List[Any]) -> List[Any]:
        """Detect changes to compliance-related language"""
        compliance_changes = []
        
        compliance_terms = ["shall", "must", "required", "mandatory", "compliance", 
                          "conform", "standard", "regulation", "applicable"]
        
        for change in changes:
            if change.change_type.value == "modification":
                orig_has_compliance = any(t in (change.original_content or "").lower() for t in compliance_terms)
                mod_has_compliance = any(t in (change.modified_content or "").lower() for t in compliance_terms)
                
                if orig_has_compliance != mod_has_compliance:
                    compliance_changes.append(change)
        
        return compliance_changes


class OperationalRiskAnalyzer:
    """Analyze operational risks in document changes"""
    
    def __init__(self):
        self.operational_keywords = [
            "process", "procedure", "workflow", "approval", "responsible",
            "department", "personnel", "staff", "resource", "capacity",
            "timeline", "deadline", "milestone", "deliverable"
        ]
    
    def analyze(self, changes: List[Any], original_text: str, modified_text: str) -> Dict[str, Any]:
        """Analyze operational risks"""
        risks = []
        
        # Process change detection
        process_changes = self._detect_process_changes(changes)
        if process_changes:
            risks.append(RiskIndicator(
                name="Process Modifications",
                category=RiskCategory.OPERATIONAL,
                score=0.7,
                description=f"Found {len(process_changes)} operational process changes",
                evidence=[c.modified_content[:100] + "..." for c in process_changes[:3]]
            ))
        
        # Responsibility changes
        responsibility_changes = self._detect_responsibility_changes(changes)
        if responsibility_changes:
            risks.append(RiskIndicator(
                name="Responsibility Changes",
                category=RiskCategory.OPERATIONAL,
                score=0.75,
                description="Changes to roles and responsibilities detected",
                evidence=[c.modified_content[:100] + "..." for c in responsibility_changes[:3]]
            ))
        
        # Calculate operational risk score
        operational_score = 0.0
        if risks:
            operational_score = max(r.score for r in risks)
        
        return {
            "score": min(operational_score, 1.0),
            "indicators": risks,
            "process_changes_count": len(process_changes),
            "responsibility_changes_count": len(responsibility_changes)
        }
    
    def _detect_process_changes(self, changes: List[Any]) -> List[Any]:
        """Detect operational process changes"""
        process_changes = []
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            content_lower = content.lower()
            
            if any(kw in content_lower for kw in ["process", "procedure", "workflow", "approval"]):
                process_changes.append(change)
        
        return process_changes
    
    def _detect_responsibility_changes(self, changes: List[Any]) -> List[Any]:
        """Detect changes to responsibilities"""
        resp_changes = []
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            content_lower = content.lower()
            
            if any(kw in content_lower for kw in ["responsible", "shall", "will", "must", "accountable"]):
                resp_changes.append(change)
        
        return resp_changes


class RiskAnalysisEngine:
    """Main risk analysis engine coordinating all risk analyzers"""
    
    def __init__(self):
        self.financial_analyzer = FinancialRiskAnalyzer()
        self.legal_analyzer = LegalRiskAnalyzer()
        self.compliance_analyzer = ComplianceRiskAnalyzer()
        self.operational_analyzer = OperationalRiskAnalyzer()
        
        # Risk scoring weights
        self.weights = {
            RiskCategory.FINANCIAL: 0.30,
            RiskCategory.LEGAL: 0.30,
            RiskCategory.COMPLIANCE: 0.25,
            RiskCategory.OPERATIONAL: 0.15
        }
    
    def analyze(self, changes: List[Any], original_text: str, modified_text: str) -> RiskAnalysisResult:
        """Perform comprehensive risk analysis"""
        import time
        start_time = time.time()
        
        # Run all analyzers
        financial_result = self.financial_analyzer.analyze(changes, original_text, modified_text)
        legal_result = self.legal_analyzer.analyze(changes, original_text, modified_text)
        compliance_result = self.compliance_analyzer.analyze(changes, original_text, modified_text)
        operational_result = self.operational_analyzer.analyze(changes, original_text, modified_text)
        
        # Collect all indicators
        all_indicators = (
            financial_result.get("indicators", []) +
            legal_result.get("indicators", []) +
            compliance_result.get("indicators", []) +
            operational_result.get("indicators", [])
        )
        
        # Calculate overall risk score
        overall_score = (
            financial_result["score"] * self.weights[RiskCategory.FINANCIAL] +
            legal_result["score"] * self.weights[RiskCategory.LEGAL] +
            compliance_result["score"] * self.weights[RiskCategory.COMPLIANCE] +
            operational_result["score"] * self.weights[RiskCategory.OPERATIONAL]
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)
        
        # Generate risk factors
        risk_factors = self._generate_risk_factors(
            financial_result, legal_result, compliance_result, operational_result
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            all_indicators, risk_level
        )
        
        # Compliance checks
        compliance_checks = self._perform_compliance_checks(changes, original_text, modified_text)
        
        return RiskAnalysisResult(
            overall_risk_score=overall_score,
            risk_level=risk_level,
            financial_risk=financial_result["score"],
            legal_risk=legal_result["score"],
            compliance_risk=compliance_result["score"],
            operational_risk=operational_result["score"],
            indicators=all_indicators,
            risk_factors=risk_factors,
            recommendations=recommendations,
            compliance_checks=compliance_checks,
            processing_time=time.time() - start_time
        )
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level from score"""
        if score >= 0.8:
            return RiskLevel.CRITICAL
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.4:
            return RiskLevel.MEDIUM
        elif score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    def _generate_risk_factors(
        self,
        financial: Dict,
        legal: Dict,
        compliance: Dict,
        operational: Dict
    ) -> List[str]:
        """Generate risk factors summary"""
        factors = []
        
        if financial["score"] >= 0.7:
            factors.append("High financial risk - amount/rate changes detected")
        
        if legal["score"] >= 0.7:
            factors.append("High legal risk - critical legal terms modified")
        
        if compliance["score"] >= 0.7:
            factors.append("High compliance risk - mandatory clauses may be missing")
        
        if operational["score"] >= 0.7:
            factors.append("Operational changes may affect processes")
        
        return factors
    
    def _generate_recommendations(self, indicators: List[RiskIndicator], risk_level: RiskLevel) -> List[str]:
        """Generate recommendations based on risk analysis"""
        recommendations = []
        
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            recommendations.append("URGENT: Conduct comprehensive review before proceeding")
            recommendations.append("Escalate to executive leadership")
        
        for indicator in indicators:
            if indicator.category == RiskCategory.FINANCIAL and indicator.score >= 0.8:
                recommendations.append("Verify all financial calculations and amounts")
            
            if indicator.category == RiskCategory.LEGAL and indicator.score >= 0.8:
                recommendations.append("Schedule legal review for contract modifications")
            
            if indicator.category == RiskCategory.COMPLIANCE and indicator.score >= 0.8:
                recommendations.append("Conduct compliance audit to verify regulatory requirements")
        
        if not recommendations:
            recommendations.append("Standard review process applies")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _perform_compliance_checks(
        self,
        changes: List[Any],
        original: str,
        modified: str
    ) -> Dict[str, Any]:
        """Perform specific compliance checks"""
        checks = {}
        
        # Check for missing clauses
        mandatory = ["termination", "governing law", "confidentiality"]
        missing_clauses = []
        
        for clause in mandatory:
            if clause.lower() in original.lower() and clause.lower() not in modified.lower():
                missing_clauses.append(clause)
        
        checks["missing_mandatory_clauses"] = missing_clauses
        checks["clause_check_passed"] = len(missing_clauses) == 0
        
        # Check for regulatory language
        has_gdpr = "gdpr" in original.lower() or "gdpr" in modified.lower()
        has_hipaa = "hipaa" in original.lower() or "hipaa" in modified.lower()
        
        checks["gdpr_applicable"] = has_gdpr
        checks["hipaa_applicable"] = has_hipaa
        
        return checks


class BusinessImpactAnalyzer:
    """Analyze business impact of document changes"""
    
    def analyze(self, changes: List[Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze business impact"""
        impact = {
            "revenue_impact": self._analyze_revenue_impact(changes),
            "cost_impact": self._analyze_cost_impact(changes),
            "contract_impact": self._analyze_contract_impact(changes),
            "policy_impact": self._analyze_policy_impact(changes)
        }
        
        # Calculate overall business impact score
        impact["overall_business_impact"] = (
            impact["revenue_impact"] * 0.35 +
            impact["cost_impact"] * 0.25 +
            impact["contract_impact"] * 0.25 +
            impact["policy_impact"] * 0.15
        )
        
        return impact
    
    def _analyze_revenue_impact(self, changes: List[Any]) -> float:
        """Analyze potential revenue impact"""
        # Simplified analysis
        revenue_keywords = ["revenue", "sales", "income", "profit", "earnings"]
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            if any(kw in content.lower() for kw in revenue_keywords):
                return 0.8  # High impact
        
        return 0.2  # Low impact
    
    def _analyze_cost_impact(self, changes: List[Any]) -> float:
        """Analyze potential cost impact"""
        cost_keywords = ["cost", "expense", "budget", "fee", "charge", "price"]
        
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            if any(kw in content.lower() for kw in cost_keywords):
                return 0.75
        
        return 0.2
    
    def _analyze_contract_impact(self, changes: List[Any]) -> float:
        """Analyze contract-related impact"""
        contract_keywords = ["contract", "agreement", "party", "obligation", "term"]
        
        count = 0
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            if any(kw in content.lower() for kw in contract_keywords):
                count += 1
        
        return min(count / 10, 1.0)  # Scale by number of changes
    
    def _analyze_policy_impact(self, changes: List[Any]) -> float:
        """Analyze policy-related impact"""
        policy_keywords = ["policy", "procedure", "regulation", "standard", "requirement"]
        
        count = 0
        for change in changes:
            content = (change.original_content or "") + (change.modified_content or "")
            if any(kw in content.lower() for kw in policy_keywords):
                count += 1
        
        return min(count / 10, 1.0)