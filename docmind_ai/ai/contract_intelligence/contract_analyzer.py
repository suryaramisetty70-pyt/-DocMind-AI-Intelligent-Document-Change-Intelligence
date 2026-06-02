"""
DocMind AI - Contract Intelligence Engine
Specialized legal document analysis and clause extraction
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import re


class ClauseType(Enum):
    """Types of legal clauses"""
    TERMINATION = "termination"
    PAYMENT = "payment"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    CONFIDENTIALITY = "confidentiality"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    NON_COMPETE = "non_compete"
    FORCE_MAJEURE = "force_majeure"
    GOVERNING_LAW = "governing_law"
    DISPUTE_RESOLUTION = "dispute_resolution"
    ASSIGNMENT = "assignment"
    WARRANTIES = "warranties"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    INSURANCE = "insurance"


class ObligationLevel(Enum):
    """Level of obligation in a clause"""
    MANDATORY = "mandatory"
    PERMISSIVE = "permissive"
    PROHIBITORY = "prohibitory"


@dataclass
class LegalClause:
    """Extracted legal clause"""
    clause_id: str
    clause_type: ClauseType
    title: str
    content: str
    page_number: int
    position: int
    obligations: List[str]
    parties_involved: List[str]
    obligations_level: ObligationLevel
    risk_level: float
    confidence: float


@dataclass
class ContractAnalysis:
    """Complete contract analysis result"""
    contract_type: str
    effective_date: Optional[str]
    expiration_date: Optional[str]
    parties: List[str]
    total_clauses: int
    clauses_by_type: Dict[str, int]
    high_risk_clauses: List[LegalClause]
    missing_standard_clauses: List[str]
    compliance_gaps: List[str]
    key_terms_summary: Dict[str, Any]
    risk_score: float


class ClauseExtractor:
    """Extract clauses from legal documents"""
    
    def __init__(self):
        self.clause_patterns = {
            ClauseType.TERMINATION: [r'termination', r'terminat(?:e|ion)'],
            ClauseType.PAYMENT: [r'payment', r'fee', r'invoice'],
            ClauseType.LIABILITY: [r'liability', r'liable'],
            ClauseType.INDEMNIFICATION: [r'indemnif', r'hold harmless'],
            ClauseType.CONFIDENTIALITY: [r'confidential', r'non-disclosure'],
            ClauseType.INTELLECTUAL_PROPERTY: [r'intellectual property', r'copyright', r'patent'],
            ClauseType.NON_COMPETE: [r'non-?compete', r'compete'],
            ClauseType.FORCE_MAJEURE: [r'force majeure'],
            ClauseType.GOVERNING_LAW: [r'governing law', r'applicable law'],
            ClauseType.DISPUTE_RESOLUTION: [r'dispute', r'arbitration', r'mediation']
        }
        
        self.obligation_patterns = {
            "shall": ObligationLevel.MANDATORY,
            "must": ObligationLevel.MANDATORY,
            "will": ObligationLevel.PERMISSIVE,
            "may": ObligationLevel.PERMISSIVE,
            "shall not": ObligationLevel.PROHIBITORY,
            "must not": ObligationLevel.PROHIBITORY
        }
    
    def extract_clauses(self, text: str) -> List[LegalClause]:
        """Extract all clauses from document text"""
        clauses = []
        sections = self._split_into_sections(text)
        
        clause_id = 0
        for idx, section in enumerate(sections):
            clause_type = self._identify_clause_type(section)
            
            if clause_type:
                clause = self._create_clause(
                    f"clause_{clause_id}", clause_type, section, 1, idx
                )
                clauses.append(clause)
                clause_id += 1
        
        return clauses
    
    def _split_into_sections(self, text: str) -> List[str]:
        """Split text into logical sections"""
        import re
        sections = re.split(r'\n\s*\n', text)
        refined = []
        for section in sections:
            if len(section.split()) > 150:
                sentences = re.split(r'(?<=[.!?])\s+', section)
                current = ""
                for sentence in sentences:
                    if len(current.split()) + len(sentence.split()) < 100:
                        current += " " + sentence
                    else:
                        if current.strip():
                            refined.append(current.strip())
                        current = sentence
                if current.strip():
                    refined.append(current.strip())
            elif section.strip():
                refined.append(section.strip())
        return refined
    
    def _identify_clause_type(self, text: str) -> Optional[ClauseType]:
        """Identify the type of clause"""
        text_lower = text.lower()
        for clause_type, patterns in self.clause_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return clause_type
        return None
    
    def _create_clause(self, clause_id: str, clause_type: ClauseType, content: str, page: int, pos: int) -> LegalClause:
        """Create a clause object"""
        obligations = self._extract_obligations(content)
        parties = self._extract_parties(content)
        obl_level = ObligationLevel.PERMISSIVE
        for obl in obligations:
            if obl.type in self.obligation_patterns:
                if self.obligation_patterns[obl.type] == ObligationLevel.MANDATORY:
                    obl_level = ObligationLevel.MANDATORY
        
        risk = self._assess_clause_risk(clause_type, content)
        title = self._extract_clause_title(content, clause_type)
        
        return LegalClause(
            clause_id=clause_id,
            clause_type=clause_type,
            title=title,
            content=content,
            page_number=page,
            position=pos,
            obligations=[o.action for o in obligations],
            parties_involved=parties,
            obligations_level=obl_level,
            risk_level=risk,
            confidence=0.85
        )
    
    def _extract_obligations(self, text: str) -> List:
        """Extract legal obligations"""
        obligations = []
        for pattern, level in self.obligation_patterns.items():
            matches = re.finditer(rf'\b{pattern}\b[^\.]*', text, re.IGNORECASE)
            for match in matches:
                obligation_text = match.group().strip()
                words = obligation_text.split()
                action = " ".join(words[2:]) if len(words) > 2 else obligation_text
                obligations.append(type('Obligation', (), {
                    'type': pattern.lower(),
                    'action': action
                })())
        return obligations
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract party names"""
        patterns = [r'\b(?:Provider|Vendor|Client|Customer|Company)\b', r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b']
        parties = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            parties.extend(matches)
        return list(set(parties))
    
    def _assess_clause_risk(self, clause_type: ClauseType, content: str) -> float:
        """Assess risk level"""
        base_risk = {
            ClauseType.LIABILITY: 0.8,
            ClauseType.INDEMNIFICATION: 0.75,
            ClauseType.TERMINATION: 0.6,
            ClauseType.NON_COMPETE: 0.65,
            ClauseType.CONFIDENTIALITY: 0.5,
            ClauseType.PAYMENT: 0.5
        }
        risk = base_risk.get(clause_type, 0.5)
        for indicator in ["unlimited", "sole discretion"]:
            if indicator in content.lower():
                risk += 0.1
        return min(max(risk, 0), 1)
    
    def _extract_clause_title(self, content: str, clause_type: ClauseType) -> str:
        """Extract or generate clause title"""
        header_match = re.match(r'^\d+\.?\s*([A-Z][^:]+)', content)
        if header_match:
            return header_match.group(1).strip()
        return clause_type.value.replace('_', ' ').title()


class ContractIntelligenceEngine:
    """Main contract intelligence engine"""
    
    def __init__(self):
        self.extractor = ClauseExtractor()
    
    def analyze_contract(self, text: str, metadata: Optional[Dict] = None) -> ContractAnalysis:
        """Perform complete contract analysis"""
        clauses = self.extractor.extract_clauses(text)
        
        clause_types = {c.clause_type for c in clauses}
        standard = [ClauseType.TERMINATION, ClauseType.PAYMENT, ClauseType.LIABILITY]
        missing = [s.value for s in standard if s not in clause_types]
        
        high_risk = [c for c in clauses if c.risk_level >= 0.7]
        
        clauses_by_type = {}
        for clause in clauses:
            type_name = clause.clause_type.value
            clauses_by_type[type_name] = clauses_by_type.get(type_name, 0) + 1
        
        avg_risk = sum(c.risk_level for c in clauses) / len(clauses) if clauses else 0
        
        return ContractAnalysis(
            contract_type=metadata.get("contract_type", "General") if metadata else "General",
            effective_date=None,
            expiration_date=None,
            parties=[],
            total_clauses=len(clauses),
            clauses_by_type=clauses_by_type,
            high_risk_clauses=high_risk,
            missing_standard_clauses=missing,
            compliance_gaps=missing,
            key_terms_summary={},
            risk_score=avg_risk
        )