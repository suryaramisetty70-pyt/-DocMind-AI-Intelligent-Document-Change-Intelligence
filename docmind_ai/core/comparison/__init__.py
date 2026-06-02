"""
DocMind AI - Comparison Module
"""

from .comparison_engine import (
    ComparisonEngine,
    ComparisonResult,
    Change,
    ChangeType,
    ChangeSeverity,
    ChangeCategory,
    ChangeLocation,
    CharacterLevelDiff,
    WordLevelDiff,
    SentenceLevelDiff,
    ParagraphLevelDiff,
    StructuralDiff,
    TableDiff,
    ChangeAggregator
)

__all__ = [
    "ComparisonEngine",
    "ComparisonResult",
    "Change",
    "ChangeType",
    "ChangeSeverity",
    "ChangeCategory",
    "ChangeLocation",
    "CharacterLevelDiff",
    "WordLevelDiff",
    "SentenceLevelDiff",
    "ParagraphLevelDiff",
    "StructuralDiff",
    "TableDiff",
    "ChangeAggregator"
]