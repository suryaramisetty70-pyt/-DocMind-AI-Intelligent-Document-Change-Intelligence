"""
DocMind AI - Compliance Engine
Compliance checking and regulatory verification
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
import re


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    ISO_27001 = "iso27001"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    CCPA = "ccpa"
    CUSTOM = "custom"


class ComplianceStatus(Enum):
    """Compliance check status"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class ComplianceCheck:
    """Individual compliance check"""
    check_id: str
    framework: ComplianceFramework
    requirement: str
    description: str
    status: ComplianceStatus
    evidence: List[str] = field(default_factory=list)
    remediation: Optional[str] = None
    severity: str = "medium"


@dataclass
class ComplianceReport:
    """Complete compliance report"""
    overall_status: ComplianceStatus
    checks_passed: int
    checks_failed: int
    checks_warning: int
    framework_scores: Dict[str, float]
    missing_clauses: List[str]
    critical_findings: List[str]
    recommendations: List[str]
    compliance_checks: List[ComplianceCheck]


class GDPRComplianceChecker:
    """GDPR compliance checker"""
    
    def __init__(self):
        self.required_clauses = [
            "data processing",
            "consent",
            "rights of data subject",
            "data protection",
            "breach notification",
            "lawful basis"
        ]
        
        self.key_articles = {
            "5": "Principles of processing",
            "6": "Lawfulness of processing",
            "7": "Conditions for consent",
            "12": "Transparent information",
            "13": "Information provided",
            "15": "Right of access",
            "17": "Right to erasure",
            "20": "Right to data portability",
            "32": "Security of processing"
        }
    
    def check(self, text: str) -> List[ComplianceCheck]:
        """Check GDPR compliance"""
        checks = []
        text_lower = text.lower()
        
        # Check for required clauses
        for clause in self.required_clauses:
            is_present = clause.lower() in text_lower
            
            checks.append(ComplianceCheck(
                check_id=f"gdpr_clause_{clause.replace(' ', '_')}",
                framework=ComplianceFramework.GDPR,
                requirement=f"Include {clause} clause",
                description=f"GDPR requires explicit mention of {clause}",
                status=ComplianceStatus.PASS if is_present else ComplianceStatus.FAIL,
                evidence=[f"{clause}: {'Found' if is_present else 'Missing'}"],
                remediation=f"Add {clause} clause to comply with GDPR" if not is_present else None,
                severity="high" if not is_present else "low"
            ))
        
        # Check for consent language
        consent_patterns = [
            r'i\s+consent',
            r'consent\s+to',
            r'gives?\s+(his|her|their)\s+consent',
            r'by\s+(checking|clicking|ticking)'
        ]
        
        has_consent = any(re.search(p, text_lower) for p in consent_patterns)
        
        checks.append(ComplianceCheck(
            check_id="gdpr_consent_language",
            framework=ComplianceFramework.GDPR,
            requirement="Include consent language",
            description="GDPR requires clear consent language",
            status=ComplianceStatus.PASS if has_consent else ComplianceStatus.WARNING,
            evidence=["Consent language: Found" if has_consent else "Consent language: Not detected"],
            remediation="Add explicit consent language with opt-in mechanism" if not has_consent else None,
            severity="high"
        ))
        
        return checks


class HIPAAComplianceChecker:
    """HIPAA compliance checker"""
    
    def __init__(self):
        self.required_elements = [
            "protected health information",
            " PHI ",
            "health information",
            "medical records",
            "patient data"
        ]
        
        self.safeguard_requirements = {
            "administrative": ["security management", "workforce training", "contingency plan"],
            "physical": ["facility access", "workstation security", "device controls"],
            "technical": ["access control", "audit controls", "integrity controls"]
        }
    
    def check(self, text: str) -> List[ComplianceCheck]:
        """Check HIPAA compliance"""
        checks = []
        text_lower = text.lower()
        
        # Check for PHI language
        has_phi = any(elem.lower() in text_lower for elem in self.required_elements)
        
        checks.append(ComplianceCheck(
            check_id="hipaa_phi_acknowledgment",
            framework=ComplianceFramework.HIPAA,
            requirement="Acknowledge PHI handling",
            description="Document should acknowledge handling of Protected Health Information",
            status=ComplianceStatus.PASS if has_phi else ComplianceStatus.WARNING,
            evidence=["PHI language: Found" if has_phi else "PHI language: Not detected"],
            remediation="Add language about handling Protected Health Information" if not has_phi else None,
            severity="medium"
        ))
        
        # Check for safeguard language
        for category, requirements in self.safeguard_requirements.items():
            for req in requirements:
                is_present = req.lower() in text_lower
                
                checks.append(ComplianceCheck(
                    check_id=f"hipaa_{category}_{req.replace(' ', '_')}",
                    framework=ComplianceFramework.HIPAA,
                    requirement=f"Include {category} safeguard: {req}",
                    description=f"HIPAA requires {req} as part of {category} safeguards",
                    status=ComplianceStatus.PASS if is_present else ComplianceStatus.WARNING,
                    evidence=[f"{req}: {'Found' if is_present else 'Not found'}"],
                    remediation=f"Add {req} requirement" if not is_present else None,
                    severity="medium"
                ))
        
        return checks


class ContractComplianceChecker:
    """General contract compliance checker"""
    
    def __init__(self):
        self.essential_clauses = [
            "termination",
            "governing law",
            "jurisdiction",
            "confidentiality",
            "indemnification",
            "force majeure",
            "notice",
            "amendment",
            "entire agreement",
            "severability",
            "assignment",
            "warranties",
            "limitation of liability"
        ]
        
        self.party_patterns = [
            r'(?:party|parties|provider|client|customer|company|vendor|contractor)',
            r'(?:herein|hereby|hereof)',
            r'(?:shall|will|may|must)'
        ]
    
    def check(self, text: str) -> List[ComplianceCheck]:
        """Check contract compliance"""
        checks = []
        text_lower = text.lower()
        
        # Check for essential clauses
        missing_clauses = []
        for clause in self.essential_clauses:
            is_present = clause.lower() in text_lower
            
            checks.append(ComplianceCheck(
                check_id=f"contract_clause_{clause.replace(' ', '_')}",
                framework=ComplianceFramework.CUSTOM,
                requirement=f"Include {clause} clause",
                description=f"Standard contracts should include {clause} clause",
                status=ComplianceStatus.PASS if is_present else ComplianceStatus.WARNING,
                evidence=[f"{clause}: {'Found' if is_present else 'MISSING'}"],
                remediation=f"Add {clause} clause" if not is_present else None,
                severity="high" if clause in ["termination", "governing law", "confidentiality"] else "medium"
            ))
            
            if not is_present:
                missing_clauses.append(clause)
        
        # Check for standard party language
        has_standard_language = any(re.search(p, text_lower) for p in self.party_patterns)
        
        checks.append(ComplianceCheck(
            check_id="contract_standard_language",
            framework=ComplianceFramework.CUSTOM,
            requirement="Use standard contract language",
            description="Contract should use standard legal language",
            status=ComplianceStatus.PASS if has_standard_language else ComplianceStatus.WARNING,
            evidence=["Standard language: Found" if has_standard_language else "Standard language: Not detected"],
            severity="low"
        ))
        
        return checks, missing_clauses


class ComplianceEngine:
    """Main compliance engine coordinating all checkers"""
    
    def __init__(self):
        self.gdpr_checker = GDPRComplianceChecker()
        self.hipaa_checker = HIPAAComplianceChecker()
        self.contract_checker = ContractComplianceChecker()
    
    def check_compliance(
        self,
        original_text: str,
        modified_text: str,
        frameworks: List[ComplianceFramework] = None
    ) -> ComplianceReport:
        """Check compliance across specified frameworks"""
        if frameworks is None:
            frameworks = [ComplianceFramework.CUSTOM]
        
        all_checks = []
        framework_scores = {}
        
        for framework in frameworks:
            if framework == ComplianceFramework.GDPR:
                checks = self.gdpr_checker.check(modified_text)
                all_checks.extend(checks)
                
                passed = sum(1 for c in checks if c.status == ComplianceStatus.PASS)
                framework_scores["GDPR"] = passed / len(checks) if checks else 0
            
            elif framework == ComplianceFramework.HIPAA:
                checks = self.hipaa_checker.check(modified_text)
                all_checks.extend(checks)
                
                passed = sum(1 for c in checks if c.status == ComplianceStatus.PASS)
                framework_scores["HIPAA"] = passed / len(checks) if checks else 0
            
            elif framework == ComplianceFramework.CUSTOM:
                checks, missing = self.contract_checker.check(modified_text)
                all_checks.extend(checks)
                
                passed = sum(1 for c in checks if c.status == ComplianceStatus.PASS)
                framework_scores["Contract"] = passed / len(checks) if checks else 0
        
        # Detect clause changes
        removed_clauses = self._detect_removed_clauses(original_text, modified_text)
        added_clauses = self._detect_added_clauses(original_text, modified_text)
        
        # Count by status
        passed = sum(1 for c in all_checks if c.status == ComplianceStatus.PASS)
        failed = sum(1 for c in all_checks if c.status == ComplianceStatus.FAIL)
        warning = sum(1 for c in all_checks if c.status == ComplianceStatus.WARNING)
        
        # Determine overall status
        if failed > 0:
            overall_status = ComplianceStatus.FAIL
        elif warning > passed:
            overall_status = ComplianceStatus.WARNING
        else:
            overall_status = ComplianceStatus.PASS
        
        # Generate critical findings
        critical_findings = []
        for check in all_checks:
            if check.status == ComplianceStatus.FAIL and check.severity == "high":
                critical_findings.append(f"Missing {check.requirement}")
        
        if removed_clauses:
            critical_findings.append(f"Required clauses removed: {', '.join(removed_clauses)}")
        
        # Generate recommendations
        recommendations = []
        for check in all_checks:
            if check.remediation and check.status != ComplianceStatus.PASS:
                recommendations.append(check.remediation)
        
        return ComplianceReport(
            overall_status=overall_status,
            checks_passed=passed,
            checks_failed=failed,
            checks_warning=warning,
            framework_scores=framework_scores,
            missing_clauses=removed_clauses,
            critical_findings=critical_findings,
            recommendations=list(set(recommendations)),
            compliance_checks=all_checks
        )
    
    def _detect_removed_clauses(self, original: str, modified: str) -> List[str]:
        """Detect essential clauses that were removed"""
        essential = ["termination", "governing law", "confidentiality", "indemnification"]
        removed = []
        
        orig_lower = original.lower()
        mod_lower = modified.lower()
        
        for clause in essential:
            if clause in orig_lower and clause not in mod_lower:
                removed.append(clause)
        
        return removed
    
    def _detect_added_clauses(self, original: str, modified: str) -> List[str]:
        """Detect new clauses that were added"""
        essential = ["termination", "governing law", "confidentiality", "indemnification"]
        added = []
        
        orig_lower = original.lower()
        mod_lower = modified.lower()
        
        for clause in essential:
            if clause not in orig_lower and clause in mod_lower:
                added.append(clause)
        
        return added


class ComplianceDashboard:
    """Generate compliance dashboard data"""
    
    def generate_dashboard(self, report: ComplianceReport) -> Dict[str, Any]:
        """Generate dashboard visualization data"""
        return {
            "overall_status": report.overall_status.value,
            "score": sum(report.framework_scores.values()) / len(report.framework_scores) if report.framework_scores else 0,
            "checks_summary": {
                "passed": report.checks_passed,
                "failed": report.checks_failed,
                "warning": report.checks_warning,
                "total": report.checks_passed + report.checks_failed + report.checks_warning
            },
            "framework_breakdown": [
                {"name": name, "score": score * 100}
                for name, score in report.framework_scores.items()
            ],
            "critical_issues": report.critical_findings,
            "next_steps": report.recommendations[:5]
        }