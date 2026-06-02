"""
DocMind AI - Fraud Engine Module
"""

from .fraud_detector import (
    FraudDetectionEngine,
    FraudDetectionResult,
    FraudType,
    FraudSeverity,
    FraudIndicator,
    AmountManipulationDetector,
    DateManipulationDetector,
    HiddenTextDetector,
    HiddenRowsDetector,
    SignatureRemovalDetector,
    StampRemovalDetector,
    DocumentHealthScorer
)

__all__ = [
    "FraudDetectionEngine",
    "FraudDetectionResult",
    "FraudType",
    "FraudSeverity",
    "FraudIndicator",
    "AmountManipulationDetector",
    "DateManipulationDetector",
    "HiddenTextDetector",
    "HiddenRowsDetector",
    "SignatureRemovalDetector",
    "StampRemovalDetector",
    "DocumentHealthScorer"
]