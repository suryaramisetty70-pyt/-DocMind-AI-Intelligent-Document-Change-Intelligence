"""
DocMind AI - Similarity Module
"""

from .similarity_engine import (
    SimilarityEngine,
    DocumentSimilarity,
    SimilarityScore,
    LexicalSimilarity,
    StructuralSimilarity,
    CharacterSimilarity,
    WordSimilarity,
    SentenceSimilarity,
    VisualSimilarity,
    ChangeHeatmap,
    SimilarityGrader
)

__all__ = [
    "SimilarityEngine",
    "DocumentSimilarity",
    "SimilarityScore",
    "LexicalSimilarity",
    "StructuralSimilarity",
    "CharacterSimilarity",
    "WordSimilarity",
    "SentenceSimilarity",
    "VisualSimilarity",
    "ChangeHeatmap",
    "SimilarityGrader"
]