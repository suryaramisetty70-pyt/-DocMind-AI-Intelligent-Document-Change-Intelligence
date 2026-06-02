"""
DocMind AI - Fraud Detection Engine
Advanced fraud and manipulation detection for document changes
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import re
import difflib
from collections import Counter


class FraudType(Enum):
    """Types of fraud indicators"""
    AMOUNT_MANIPULATION = "amount_manipulation"
    DATE_MANIPULATION = "date_manipulation"
    HIDDEN_TEXT = "hidden_text"
    HIDDEN_ROWS = "hidden_rows"
    SIGNATURE_REMOVAL = "signature_removal"
    STAMP_REMOVAL = "stamp_removal"
    CLONE_DETECTION = "clone_detection"
    WHITEWATERING = "whitewashing"
    CONTENT_SWAPPING = "content_swapping"
    BACKDATING = "backdating"


class FraudSeverity(Enum):
    """Severity of fraud indicators"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SUSPICIOUS = "suspicious"


@dataclass
class FraudIndicator:
    """Individual fraud indicator"""
    fraud_type: FraudType
    severity: FraudSeverity
    confidence: float
    location: Dict[str, Any]
    original_value: Optional[str] = None
    modified_value: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    description: str = ""
    recommendation: str = ""


@dataclass
class FraudDetectionResult:
    """Complete fraud detection result"""
    fraud_score: float
    fraud_level: FraudSeverity
    indicators: List[FraudIndicator]
    critical_findings: List[FraudIndicator]
    summary: str
    recommendations: List[str]
    processing_time: float


class AmountManipulationDetector:
    """Detect amount/financial value manipulation"""
    
    def __init__(self):
        self.amount_patterns = [
            r'\$\s*[\d,]+\.?\d*',
            r'USD\s*[\d,]+\.?\d*',
            r'EUR\s*[\d,]+\.?\d*',
            r'GBP\s*[\d,]+\.?\d*',
            r'INR\s*[\d,]+\.?\d*',
            r'₹\s*[\d,]+\.?\d*',
            r'[\d,]+\.?\d*\s*(?:dollars?|euros?|pounds?|rupees?)',
            r'[\d,]+\.?\d*\s*(?:percent|%)',
            r'\b\d+\.\d{2}\b'
        ]
        
        self.suspicious_patterns = [
            r'\b0{3,}\d+',  # Leading zeros (e.g., 000100)
            r'\b1\.00\b',   # Round numbers used suspiciously
            r'\b9{3,}\b',   # Repetitive 9s
            r'\.\d{3,}',    # Excessive decimal places
        ]
    
    def detect(self, changes: List[Any]) -> List[FraudIndicator]:
        """Detect amount manipulation in changes"""
        indicators = []
        
        for change in changes:
            orig_amounts = self._extract_amounts(change.original_content or "")
            mod_amounts = self._extract_amounts(change.modified_content or "")
            
            # Check for amount changes
            for orig in orig_amounts:
                for mod in mod_amounts:
                    if orig["amount"] != mod["amount"] and abs(orig["amount"] - mod["amount"]) > 0:
                        severity = self._assess_severity(orig["amount"], mod["amount"])
                        
                        indicators.append(FraudIndicator(
                            fraud_type=FraudType.AMOUNT_MANIPULATION,
                            severity=severity,
                            confidence=0.85,
                            location={"page": change.location.page, "line": change.location.line_start},
                            original_value=orig["text"],
                            modified_value=mod["text"],
                            evidence=[
                                f"Original amount: {orig['text']}",
                                f"Modified amount: {mod['text']}",
                                f"Change: {((mod['amount'] - orig['amount']) / orig['amount'] * 100):.1f}%" if orig['amount'] != 0 else "N/A"
                            ],
                            description=f"Amount changed from {orig['text']} to {mod['text']}",
                            recommendation="Verify this financial change is authorized"
                        ))
            
            # Check for suspicious patterns in modified content
            if change.modified_content:
                for pattern in self.suspicious_patterns:
                    matches = re.findall(pattern, change.modified_content)
                    if matches:
                        indicators.append(FraudIndicator(
                            fraud_type=FraudType.AMOUNT_MANIPULATION,
                            severity=FraudSeverity.MEDIUM,
                            confidence=0.6,
                            location={"page": change.location.page, "line": change.location.line_start},
                            modified_value=", ".join(matches),
                            evidence=[f"Suspicious pattern found: {matches}"],
                            description="Suspicious number pattern detected",
                            recommendation="Review this suspicious pattern"
                        ))
        
        return indicators
    
    def _extract_amounts(self, text: str) -> List[Dict[str, Any]]:
        """Extract all amounts from text"""
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
        cleaned = re.sub(r'[^\d.]', '', amount_str)
        try:
            return float(cleaned)
        except:
            return 0.0
    
    def _assess_severity(self, orig: float, mod: float) -> FraudSeverity:
        """Assess severity of amount change"""
        if orig == 0:
            return FraudSeverity.HIGH if mod > 0 else FraudSeverity.LOW
        
        change_pct = abs(mod - orig) / orig
        
        if change_pct > 0.5:  # > 50% change
            return FraudSeverity.CRITICAL
        elif change_pct > 0.2:  # > 20% change
            return FraudSeverity.HIGH
        elif change_pct > 0.1:  # > 10% change
            return FraudSeverity.MEDIUM
        else:
            return FraudSeverity.LOW


class DateManipulationDetector:
    """Detect date manipulation in documents"""
    
    def __init__(self):
        self.date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}/\d{1,2}/\d{2}',  # MM/DD/YY
            r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD
            r'\d{1,2}-\d{1,2}-\d{4}',  # DD-MM-YYYY
            r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}'
        ]
        
        self.suspicious_date_patterns = [
            r'01/01/\d{4}',   # Always January 1st
            r'12/31/\d{4}',   # Always December 31st
            r'01/\d{1,2}/\d{4}',  # Always January
            r'12/\d{1,2}/\d{4}'   # Always December
        ]
    
    def detect(self, changes: List[Any]) -> List[FraudIndicator]:
        """Detect date manipulation in changes"""
        indicators = []
        
        for change in changes:
            orig_dates = self._extract_dates(change.original_content or "")
            mod_dates = self._extract_dates(change.modified_content or "")
            
            # Check for date changes
            for orig in orig_dates:
                for mod in mod_dates:
                    if orig["date_str"] != mod["date_str"]:
                        indicators.append(FraudIndicator(
                            fraud_type=FraudType.DATE_MANIPULATION,
                            severity=FraudSeverity.HIGH,
                            confidence=0.8,
                            location={"page": change.location.page, "line": change.location.line_start},
                            original_value=orig["date_str"],
                            modified_value=mod["date_str"],
                            evidence=[f"Date changed from {orig['date_str']} to {mod['date_str']}"],
                            description=f"Date modification detected",
                            recommendation="Verify this date change is legitimate"
                        ))
            
            # Check for suspicious date patterns in modified content
            if change.modified_content:
                for pattern in self.suspicious_date_patterns:
                    if re.search(pattern, change.modified_content, re.IGNORECASE):
                        indicators.append(FraudIndicator(
                            fraud_type=FraudType.BACKDATING,
                            severity=FraudSeverity.MEDIUM,
                            confidence=0.5,
                            location={"page": change.location.page, "line": change.location.line_start},
                            modified_value=re.search(pattern, change.modified_content, re.IGNORECASE).group(),
                            evidence=["Suspicious date pattern detected"],
                            description="Potentially artificial date pattern",
                            recommendation="Review date legitimacy"
                        ))
        
        return indicators
    
    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """Extract all dates from text"""
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dates.append({
                    "date_str": match.group(),
                    "position": match.start()
                })
        
        return dates


class HiddenTextDetector:
    """Detect hidden text in documents"""
    
    def __init__(self):
        self.hidden_techniques = [
            (r'<span[^>]*style=["\']color:\s*white[^"\']*["\']', "White text on white background"),
            (r'<span[^>]*style=["\']color:\s*#fff[^"\']*["\']', "White text (#fff)"),
            (r'<font[^>]*color=["\']white["\']', "Font color white"),
            (r'style=["\'][^"\']*visibility:\s*hidden[^"\']*["\']', "Hidden via CSS"),
            (r'style=["\'][^"\']*display:\s*none[^"\']*["\']', "Display none"),
            (r'font-size:\s*0pt', "Zero font size"),
            (r'font-size:\s*0px', "Zero font size (px)"),
        ]
    
    def detect_html(self, text: str) -> List[FraudIndicator]:
        """Detect hidden text in HTML content"""
        indicators = []
        
        for pattern, technique in self.hidden_techniques:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                indicators.append(FraudIndicator(
                    fraud_type=FraudType.HIDDEN_TEXT,
                    severity=FraudSeverity.HIGH,
                    confidence=0.9,
                    location={"type": "html"},
                    evidence=[f"Technique: {technique}", f"Matches: {len(matches)}"],
                    description=f"Hidden text detected using: {technique}",
                    recommendation="Investigate hidden text content"
                ))
        
        return indicators
    
    def detect_visual_indicators(self, text: str) -> List[FraudIndicator]:
        """Detect visual indicators of hidden text"""
        indicators = []
        
        # Check for extremely small fonts
        small_font_pattern = r'font-size:\s*1pt|font-size:\s*2pt'
        if re.search(small_font_pattern, text, re.IGNORECASE):
            indicators.append(FraudIndicator(
                fraud_type=FraudType.HIDDEN_TEXT,
                severity=FraudSeverity.MEDIUM,
                confidence=0.7,
                location={"type": "formatting"},
                evidence=["Very small font size detected (1-2pt)"],
                description="Micro-sized text may be hidden",
                recommendation="Check for hidden content with small font"
            ))
        
        # Check for text matching background color
        white_text_pattern = r'(?:white|#fff|#ffffff)'
        if re.search(white_text_pattern, text, re.IGNORECASE):
            # This is a heuristic, not definitive
            indicators.append(FraudIndicator(
                fraud_type=FraudType.WHITEWATERING,
                severity=FraudSeverity.LOW,
                confidence=0.4,
                location={"type": "color"},
                evidence=["White color formatting found"],
                description="Potential white-on-white text",
                recommendation="Verify text visibility"
            ))
        
        return indicators


class HiddenRowsDetector:
    """Detect hidden rows in Excel/spreadsheet documents"""
    
    def detect_excel_structure(self, original_tables: List[Dict], modified_tables: List[Dict]) -> List[FraudIndicator]:
        """Detect hidden rows between table versions"""
        indicators = []
        
        for idx, (orig_table, mod_table) in enumerate(zip(original_tables, modified_tables)):
            orig_row_count = len(orig_table.get("data", []))
            mod_row_count = len(mod_table.get("data", []))
            
            if mod_row_count < orig_row_count:
                missing_rows = orig_row_count - mod_row_count
                percentage_lost = (missing_rows / orig_row_count) * 100
                
                indicators.append(FraudIndicator(
                    fraud_type=FraudType.HIDDEN_ROWS,
                    severity=FraudSeverity.CRITICAL if percentage_lost > 10 else FraudSeverity.HIGH,
                    confidence=0.9,
                    location={"table_index": idx + 1, "sheet": orig_table.get("sheet", "Unknown")},
                    evidence=[
                        f"Original rows: {orig_row_count}",
                        f"Current rows: {mod_row_count}",
                        f"Missing rows: {missing_rows}",
                        f"Percentage lost: {percentage_lost:.1f}%"
                    ],
                    description=f"{missing_rows} rows ({percentage_lost:.1f}%) appear to be hidden or removed",
                    recommendation="Check for hidden rows in Excel: Select all rows, right-click, and select 'Unhide'"
                ))
        
        return indicators


class SignatureRemovalDetector:
    """Detect signature removal between document versions"""
    
    def __init__(self):
        self.signature_indicators = [
            r'signature',
            r'signed\s+by',
            r'authorized',
            r'approved\s+by',
            r'witness'
        ]
    
    def detect(self, original_text: str, modified_text: str, original_structure: Dict, modified_structure: Dict) -> List[FraudIndicator]:
        """Detect if signatures were removed"""
        indicators = []
        
        # Check for signature-related text removal
        orig_has_signature = any(re.search(p, original_text, re.IGNORECASE) for p in self.signature_indicators)
        mod_has_signature = any(re.search(p, modified_text, re.IGNORECASE) for p in self.signature_indicators)
        
        if orig_has_signature and not mod_has_signature:
            indicators.append(FraudIndicator(
                fraud_type=FraudType.SIGNATURE_REMOVAL,
                severity=FraudSeverity.CRITICAL,
                confidence=0.95,
                location={"type": "signature_section"},
                evidence=["Signature-related text was removed"],
                description="Signature or authorization appears to have been removed",
                recommendation="Verify signature authenticity and authorization"
            ))
        
        # Check signature region changes
        orig_sigs = original_structure.get("signatures_detected", [])
        mod_sigs = modified_structure.get("signatures_detected", [])
        
        if len(mod_sigs) < len(orig_sigs):
            indicators.append(FraudIndicator(
                fraud_type=FraudType.SIGNATURE_REMOVAL,
                severity=FraudSeverity.CRITICAL,
                confidence=0.9,
                location={"type": "signature_regions"},
                evidence=[
                    f"Original signatures: {len(orig_sigs)}",
                    f"Current signatures: {len(mod_sigs)}",
                    f"Signatures removed: {len(orig_sigs) - len(mod_sigs)}"
                ],
                description=f"{len(orig_sigs) - len(mod_sigs)} signatures appear to have been removed",
                recommendation="Verify signature validity"
            ))
        
        return indicators


class StampRemovalDetector:
    """Detect stamp removal between document versions"""
    
    def detect(self, original_structure: Dict, modified_structure: Dict) -> List[FraudIndicator]:
        """Detect if stamps were removed"""
        indicators = []
        
        orig_stamps = original_structure.get("stamps_detected", [])
        mod_stamps = modified_structure.get("stamps_detected", [])
        
        if len(mod_stamps) < len(orig_stamps):
            indicators.append(FraudIndicator(
                fraud_type=FraudType.STAMP_REMOVAL,
                severity=FraudSeverity.HIGH,
                confidence=0.85,
                location={"type": "stamp_regions"},
                evidence=[
                    f"Original stamps: {len(orig_stamps)}",
                    f"Current stamps: {len(mod_stamps)}",
                    f"Stamps removed: {len(orig_stamps) - len(mod_stamps)}"
                ],
                description=f"{len(orig_stamps) - len(mod_stamps)} stamps appear to have been removed",
                recommendation="Verify stamp authenticity"
            ))
        
        return indicators


class ContentCloneDetector:
    """Detect cloned content that may indicate fraud"""
    
    def detect(self, text: str) -> List[FraudIndicator]:
        """Detect cloned/duplicated content"""
        indicators = []
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 50]
        
        # Find duplicate sentences
        sentence_counts = Counter(sentences)
        
        duplicates = {sent: count for sent, count in sentence_counts.items() if count > 1}
        
        if duplicates:
            indicators.append(FraudIndicator(
                fraud_type=FraudType.CLONE_DETECTION,
                severity=FraudSeverity.MEDIUM,
                confidence=0.75,
                location={"type": "content"},
                evidence=[f"Found {len(duplicates)} duplicated sentences"],
                description=f"Content duplication detected - {sum(duplicates.values())} instances of repeated text",
                recommendation="Review duplicated content for accuracy"
            ))
        
        return indicators


class ContentSwappingDetector:
    """Detect content swapping between sections"""
    
    def detect(self, changes: List[Any]) -> List[FraudIndicator]:
        """Detect content that appears to be swapped"""
        indicators = []
        
        # Look for movement changes with unusual patterns
        for change in changes:
            if change.change_type.value == "movement":
                content_length = len(change.original_content)
                
                # Very long content movements are suspicious
                if content_length > 500:
                    indicators.append(FraudIndicator(
                        fraud_type=FraudType.CONTENT_SWAPPING,
                        severity=FraudSeverity.MEDIUM,
                        confidence=0.6,
                        location={"page": change.location.page, "section": change.location.section},
                        evidence=[f"Large content section moved: {content_length} characters"],
                        description="Large content section was moved",
                        recommendation="Verify moved content is appropriate in new location"
                    ))
        
        return indicators


class FraudDetectionEngine:
    """Main fraud detection engine coordinating all detectors"""
    
    def __init__(self):
        self.amount_detector = AmountManipulationDetector()
        self.date_detector = DateManipulationDetector()
        self.hidden_text_detector = HiddenTextDetector()
        self.hidden_rows_detector = HiddenRowsDetector()
        self.signature_detector = SignatureRemovalDetector()
        self.stamp_detector = StampRemovalDetector()
        self.clone_detector = ContentCloneDetector()
        self.swapping_detector = ContentSwappingDetector()
    
    def analyze(
        self,
        changes: List[Any],
        original_text: str,
        modified_text: str,
        original_structure: Optional[Dict] = None,
        modified_structure: Optional[Dict] = None,
        original_tables: Optional[List[Dict]] = None,
        modified_tables: Optional[List[Dict]] = None
    ) -> FraudDetectionResult:
        """Perform comprehensive fraud detection"""
        import time
        start_time = time.time()
        
        all_indicators = []
        
        # Amount manipulation
        all_indicators.extend(self.amount_detector.detect(changes))
        
        # Date manipulation
        all_indicators.extend(self.date_detector.detect(changes))
        
        # Hidden text
        all_indicators.extend(self.hidden_text_detector.detect_html(modified_text))
        all_indicators.extend(self.hidden_text_detector.detect_visual_indicators(modified_text))
        
        # Hidden rows
        if original_tables and modified_tables:
            all_indicators.extend(self.hidden_rows_detector.detect_excel_structure(original_tables, modified_tables))
        
        # Signature removal
        if original_structure and modified_structure:
            all_indicators.extend(self.signature_detector.detect(
                original_text, modified_text, original_structure or {}, modified_structure or {}
            ))
            all_indicators.extend(self.stamp_detector.detect(original_structure or {}, modified_structure or {}))
        
        # Content cloning
        all_indicators.extend(self.clone_detector.detect(modified_text))
        
        # Content swapping
        all_indicators.extend(self.swapping_detector.detect(changes))
        
        # Calculate overall fraud score
        if all_indicators:
            severity_scores = {
                FraudSeverity.CRITICAL: 1.0,
                FraudSeverity.HIGH: 0.75,
                FraudSeverity.MEDIUM: 0.5,
                FraudSeverity.LOW: 0.25,
                FraudSeverity.SUSPICIOUS: 0.1
            }
            
            fraud_score = max(
                severity_scores.get(i.severity, 0) * i.confidence
                for i in all_indicators
            )
            
            # Boost score for multiple indicators
            if len(all_indicators) > 3:
                fraud_score = min(fraud_score * 1.2, 1.0)
        else:
            fraud_score = 0.0
        
        # Determine fraud level
        fraud_level = self._determine_fraud_level(fraud_score)
        
        # Get critical findings
        critical_findings = [i for i in all_indicators if i.severity == FraudSeverity.CRITICAL]
        
        # Generate summary
        summary = self._generate_summary(all_indicators, fraud_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_indicators, fraud_level)
        
        return FraudDetectionResult(
            fraud_score=fraud_score,
            fraud_level=fraud_level,
            indicators=all_indicators,
            critical_findings=critical_findings,
            summary=summary,
            recommendations=recommendations,
            processing_time=time.time() - start_time
        )
    
    def _determine_fraud_level(self, score: float) -> FraudSeverity:
        """Determine fraud level from score"""
        if score >= 0.9:
            return FraudSeverity.CRITICAL
        elif score >= 0.7:
            return FraudSeverity.HIGH
        elif score >= 0.5:
            return FraudSeverity.MEDIUM
        elif score >= 0.2:
            return FraudSeverity.LOW
        else:
            return FraudSeverity.SUSPICIOUS
    
    def _generate_summary(self, indicators: List[FraudIndicator], score: float) -> str:
        """Generate fraud detection summary"""
        if not indicators:
            return "No fraud indicators detected. Document appears clean."
        
        count_by_type = Counter(i.fraud_type for i in indicators)
        
        summary_parts = [
            f"Fraud Analysis Complete",
            f"Overall Score: {score:.1%}",
            f"Total Indicators: {len(indicators)}",
        ]
        
        if count_by_type:
            top_types = count_by_type.most_common(3)
            summary_parts.append("Top Concerns:")
            for fraud_type, count in top_types:
                summary_parts.append(f"  - {fraud_type.value}: {count}")
        
        return "\n".join(summary_parts)
    
    def _generate_recommendations(self, indicators: List[FraudIndicator], level: FraudSeverity) -> List[str]:
        """Generate fraud detection recommendations"""
        recommendations = []
        
        if level in [FraudSeverity.CRITICAL, FraudSeverity.HIGH]:
            recommendations.append("URGENT: Investigate detected fraud indicators immediately")
            recommendations.append("Do not proceed with document until review is complete")
        
        for indicator in indicators:
            if indicator.severity in [FraudSeverity.CRITICAL, FraudSeverity.HIGH]:
                recommendations.append(f"Review: {indicator.description}")
        
        if not recommendations:
            recommendations.append("Standard verification process applies")
        
        return list(set(recommendations))  # Remove duplicates


class DocumentHealthScorer:
    """Calculate overall document health scores"""
    
    def calculate_health_score(
        self,
        fraud_result: Optional[FraudDetectionResult],
        risk_result: Optional[Any],
        similarity_score: float,
        comparison_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive health scores"""
        
        # Trust score (inverse of fraud)
        if fraud_result:
            trust_score = 1.0 - fraud_result.fraud_score
        else:
            trust_score = 1.0
        
        # Risk score
        if risk_result:
            risk_score = risk_result.overall_risk_score
        else:
            risk_score = 0.0
        
        # Similarity score (from comparison)
        sim_score = similarity_score
        
        # Review complexity (based on number of changes)
        change_count = comparison_stats.get("total_changes", 0)
        if change_count > 50:
            review_complexity = 1.0
        elif change_count > 20:
            review_complexity = 0.75
        elif change_count > 10:
            review_complexity = 0.5
        elif change_count > 5:
            review_complexity = 0.25
        else:
            review_complexity = 0.1
        
        # Overall document health
        overall_health = (
            trust_score * 0.35 +
            (1.0 - risk_score) * 0.25 +
            sim_score * 0.25 +
            (1.0 - review_complexity) * 0.15
        )
        
        return {
            "overall_health_score": overall_health,
            "trust_score": trust_score,
            "risk_score": risk_score,
            "similarity_score": sim_score,
            "review_complexity_score": review_complexity,
            "health_grade": self._get_grade(overall_health),
            "factors": {
                "fraud_indicators": len(fraud_result.indicators) if fraud_result else 0,
                "critical_changes": comparison_stats.get("by_severity", {}).get("critical", 0),
                "total_changes": change_count
            }
        }
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.85:
            return "A"
        elif score >= 0.8:
            return "B+"
        elif score >= 0.75:
            return "B"
        elif score >= 0.7:
            return "C+"
        elif score >= 0.65:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"