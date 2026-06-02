"""
DocMind AI - Similarity Engine
Multi-dimensional document similarity analysis
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
from collections import Counter
import re


@dataclass
class SimilarityScore:
    """Individual similarity score component"""
    metric_name: str
    score: float
    weight: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentSimilarity:
    """Complete similarity analysis result"""
    overall_similarity: float
    semantic_similarity: float
    structural_similarity: float
    visual_similarity: float
    lexical_similarity: float
    character_similarity: float
    word_similarity: float
    sentence_similarity: float
    component_scores: List[SimilarityScore]
    processing_time: float
    confidence: float


class LexicalSimilarity:
    """Calculate lexical similarity between documents"""
    
    def calculate(self, text1: str, text2: str) -> Dict[str, float]:
        """Calculate various lexical similarity metrics"""
        if not text1 or not text2:
            return {"jaccard": 0.0, "dice": 0.0, "overlap": 0.0, "cosine": 0.0}
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        # Jaccard similarity
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Dice coefficient
        dice = 2 * len(intersection) / (len(words1) + len(words2)) if (words1 or words2) else 0.0
        
        # Overlap coefficient
        overlap = len(intersection) / min(len(words1), len(words2)) if (words1 and words2) else 0.0
        
        # TF-IDF cosine similarity
        try:
            vectorizer = TfidfVectorizer()
            tfidf = vectorizer.fit_transform([text1, text2])
            cosine = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
        except:
            cosine = 0.0
        
        return {
            "jaccard": jaccard,
            "dice": dice,
            "overlap": overlap,
            "cosine": cosine
        }


class StructuralSimilarity:
    """Calculate structural similarity between documents"""
    
    def calculate(self, structure1: Dict[str, Any], structure2: Dict[str, Any]) -> Dict[str, float]:
        """Calculate structural similarity metrics"""
        metrics = {}
        
        # Section similarity
        sections1 = structure1.get("sections", [])
        sections2 = structure2.get("sections", [])
        
        if sections1 and sections2:
            section_titles1 = [s.get("title", "") for s in sections1]
            section_titles2 = [s.get("title", "") for s in sections2]
            
            section_overlap = len(set(section_titles1) & set(section_titles2)) / len(set(section_titles1 + section_titles2))
            metrics["section_similarity"] = section_overlap
            
            # Section order similarity
            order_similarity = self._sequence_similarity(section_titles1, section_titles2)
            metrics["section_order_similarity"] = order_similarity
        else:
            metrics["section_similarity"] = 0.0
            metrics["section_order_similarity"] = 0.0
        
        # Element count similarity
        elements1 = structure1.get("text_blocks", 0) + structure1.get("tables", 0)
        elements2 = structure2.get("text_blocks", 0) + structure2.get("tables", 0)
        metrics["element_count_similarity"] = min(elements1, elements2) / max(elements1, elements2) if max(elements1, elements2) > 0 else 1.0
        
        # Page count similarity
        pages1 = structure1.get("total_pages", 1)
        pages2 = structure2.get("total_pages", 1)
        metrics["page_count_similarity"] = min(pages1, pages2) / max(pages1, pages2) if max(pages1, pages2) > 0 else 1.0
        
        return metrics
    
    def _sequence_similarity(self, seq1: List, seq2: List) -> float:
        """Calculate sequence similarity using LCS approach"""
        if not seq1 or not seq2:
            return 0.0
        
        matcher = SequenceMatcher(None, seq1, seq2)
        return matcher.ratio()


class CharacterSimilarity:
    """Calculate character-level similarity"""
    
    def calculate(self, text1: str, text2: str) -> Dict[str, float]:
        """Calculate character-level similarity metrics"""
        if not text1 or not text2:
            return {"sequence_ratio": 0.0, "longest_common_substring_ratio": 0.0}
        
        # SequenceMatcher ratio
        matcher = SequenceMatcher(None, text1, text2)
        sequence_ratio = matcher.ratio()
        
        # Longest common substring ratio
        lcs_length = self._lcs_length(text1, text2)
        max_len = max(len(text1), len(text2))
        lcs_ratio = lcs_length / max_len if max_len > 0 else 0.0
        
        # Character set overlap
        chars1 = set(text1)
        chars2 = set(text2)
        char_overlap = len(chars1 & chars2) / len(chars1 | chars2) if chars1 | chars2 else 0.0
        
        return {
            "sequence_ratio": sequence_ratio,
            "longest_common_substring_ratio": lcs_ratio,
            "character_set_overlap": char_overlap
        }
    
    def _lcs_length(self, s1: str, s2: str) -> int:
        """Calculate longest common substring length"""
        m, n = len(s1), len(s2)
        
        # Limit for performance
        if m * n > 1000000:
            return 0
        
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]


class WordSimilarity:
    """Calculate word-level similarity"""
    
    def calculate(self, text1: str, text2: str) -> Dict[str, float]:
        """Calculate word-level similarity metrics"""
        if not text1 or not text2:
            return {"sequence_ratio": 0.0, "ngram_overlap": 0.0}
        
        words1 = text1.split()
        words2 = text2.split()
        
        # Word sequence ratio
        matcher = SequenceMatcher(None, words1, words2)
        sequence_ratio = matcher.ratio()
        
        # N-gram overlap (bigrams and trigrams)
        bigrams1 = set(self._get_ngrams(words1, 2))
        bigrams2 = set(self._get_ngrams(words2, 2))
        bigram_overlap = len(bigrams1 & bigrams2) / len(bigrams1 | bigrams2) if bigrams1 | bigrams2 else 0.0
        
        trigrams1 = set(self._get_ngrams(words1, 3))
        trigrams2 = set(self._get_ngrams(words2, 3))
        trigram_overlap = len(trigrams1 & trigrams2) / len(trigrams1 | trigrams2) if trigrams1 | trigrams2 else 0.0
        
        return {
            "sequence_ratio": sequence_ratio,
            "bigram_overlap": bigram_overlap,
            "trigram_overlap": trigram_overlap
        }
    
    def _get_ngrams(self, words: List[str], n: int) -> List[Tuple]:
        """Get n-grams from word list"""
        return [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]


class SentenceSimilarity:
    """Calculate sentence-level similarity"""
    
    def calculate(self, text1: str, text2: str) -> Dict[str, float]:
        """Calculate sentence-level similarity metrics"""
        sentences1 = self._split_sentences(text1)
        sentences2 = self._split_sentences(text2)
        
        if not sentences1 or not sentences2:
            return {"sequence_ratio": 0.0, "content_overlap": 0.0}
        
        # Sentence sequence ratio
        matcher = SequenceMatcher(None, sentences1, sentences2)
        sequence_ratio = matcher.ratio()
        
        # Content overlap (sentence content matching)
        matched = 0
        for s1 in sentences1:
            for s2 in sentences2:
                ratio = SequenceMatcher(None, s1, s2).ratio()
                if ratio > 0.8:
                    matched += 1
                    break
        
        content_overlap = matched / max(len(sentences1), len(sentences2))
        
        return {
            "sequence_ratio": sequence_ratio,
            "content_overlap": content_overlap,
            "original_sentences": len(sentences1),
            "modified_sentences": len(sentences2)
        }
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentence_pattern = re.compile(r'(?<=[.!?])\s+')
        return [s.strip() for s in sentence_pattern.split(text) if s.strip()]


class VisualSimilarity:
    """Calculate visual similarity for document images/rendering"""
    
    def calculate(self, image1: Any, image2: Any) -> Dict[str, float]:
        """Calculate visual similarity between document images"""
        # This would require image comparison
        # Simplified implementation
        return {
            "image_similarity": 0.0,
            "layout_similarity": 0.0
        }


class SimilarityEngine:
    """Main similarity engine coordinating all similarity calculations"""
    
    def __init__(self):
        self.lexical = LexicalSimilarity()
        self.structural = StructuralSimilarity()
        self.character = CharacterSimilarity()
        self.word = WordSimilarity()
        self.sentence = SentenceSimilarity()
        self.visual = VisualSimilarity()
        
        # Weights for different similarity components
        self.weights = {
            "semantic": 0.35,
            "structural": 0.20,
            "lexical": 0.15,
            "character": 0.10,
            "word": 0.10,
            "sentence": 0.10
        }
    
    def calculate_similarity(
        self,
        original_text: str,
        modified_text: str,
        original_structure: Optional[Dict[str, Any]] = None,
        modified_structure: Optional[Dict[str, Any]] = None
    ) -> DocumentSimilarity:
        """Calculate comprehensive similarity between documents"""
        import time
        start_time = time.time()
        
        component_scores = []
        
        # Character-level similarity
        char_metrics = self.character.calculate(original_text, modified_text)
        char_similarity = char_metrics.get("sequence_ratio", 0.0)
        component_scores.append(SimilarityScore(
            metric_name="character_similarity",
            score=char_similarity,
            weight=0.10,
            details=char_metrics
        ))
        
        # Word-level similarity
        word_metrics = self.word.calculate(original_text, modified_text)
        word_similarity = word_metrics.get("sequence_ratio", 0.0)
        component_scores.append(SimilarityScore(
            metric_name="word_similarity",
            score=word_similarity,
            weight=0.10,
            details=word_metrics
        ))
        
        # Sentence-level similarity
        sentence_metrics = self.sentence.calculate(original_text, modified_text)
        sentence_similarity = sentence_metrics.get("sequence_ratio", 0.0)
        component_scores.append(SimilarityScore(
            metric_name="sentence_similarity",
            score=sentence_similarity,
            weight=0.10,
            details=sentence_metrics
        ))
        
        # Lexical similarity
        lexical_metrics = self.lexical.calculate(original_text, modified_text)
        lexical_similarity = lexical_metrics.get("cosine", 0.0)
        component_scores.append(SimilarityScore(
            metric_name="lexical_similarity",
            score=lexical_similarity,
            weight=0.15,
            details=lexical_metrics
        ))
        
        # Structural similarity
        if original_structure and modified_structure:
            struct_metrics = self.structural.calculate(original_structure, modified_structure)
            struct_similarity = (
                struct_metrics.get("section_similarity", 0.0) * 0.5 +
                struct_metrics.get("section_order_similarity", 0.0) * 0.3 +
                struct_metrics.get("element_count_similarity", 0.0) * 0.2
            )
        else:
            struct_similarity = 0.5
            struct_metrics = {}
        component_scores.append(SimilarityScore(
            metric_name="structural_similarity",
            score=struct_similarity,
            weight=0.20,
            details=struct_metrics
        ))
        
        # Semantic similarity (placeholder - would use embeddings)
        semantic_similarity = char_similarity * 0.4 + word_similarity * 0.3 + lexical_similarity * 0.3
        component_scores.append(SimilarityScore(
            metric_name="semantic_similarity",
            score=semantic_similarity,
            weight=0.35,
            details={"estimated": True}
        ))
        
        # Calculate weighted overall similarity
        overall_similarity = sum(s.score * s.weight for s in component_scores)
        
        processing_time = time.time() - start_time
        
        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(component_scores)
        
        return DocumentSimilarity(
            overall_similarity=overall_similarity,
            semantic_similarity=semantic_similarity,
            structural_similarity=struct_similarity,
            visual_similarity=0.0,  # Would need images
            lexical_similarity=lexical_similarity,
            character_similarity=char_similarity,
            word_similarity=word_similarity,
            sentence_similarity=sentence_similarity,
            component_scores=component_scores,
            processing_time=processing_time,
            confidence=confidence
        )
    
    def _calculate_confidence(self, scores: List[SimilarityScore]) -> float:
        """Calculate confidence in similarity score"""
        if not scores:
            return 0.0
        
        # Higher confidence if scores are consistent
        score_values = [s.score for s in scores]
        variance = np.var(score_values)
        
        # Low variance = high confidence
        confidence = max(0.5, 1.0 - variance)
        
        return confidence
    
    def compare_multiple_documents(self, documents: List[str]) -> List[List[float]]:
        """Compare multiple documents pairwise"""
        n = len(documents)
        similarity_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i+1, n):
                similarity = self.calculate_similarity(documents[i], documents[j])
                similarity_matrix[i][j] = similarity.overall_similarity
                similarity_matrix[j][i] = similarity.overall_similarity
        
        return similarity_matrix


class ChangeHeatmap:
    """Generate change heatmap for document comparison"""
    
    def __init__(self):
        self.page_changes = {}
        self.section_changes = {}
    
    def generate_page_heatmap(self, changes: List[Any], total_pages: int) -> Dict[int, float]:
        """Generate change density heatmap per page"""
        page_density = {i: 0.0 for i in range(1, total_pages + 1)}
        
        for change in changes:
            page = change.location.page if change.location.page else 1
            if page in page_density:
                # Higher weight for more significant changes
                weight = 1.0
                if hasattr(change, 'severity'):
                    if change.severity.value == "critical":
                        weight = 3.0
                    elif change.severity.value == "significant":
                        weight = 2.0
                
                page_density[page] += weight
        
        # Normalize
        max_density = max(page_density.values()) if max(page_density.values()) > 0 else 1
        for page in page_density:
            page_density[page] /= max_density
        
        return page_density
    
    def generate_section_heatmap(self, changes: List[Any], sections: List[str]) -> Dict[str, float]:
        """Generate change density heatmap per section"""
        section_density = {s: 0.0 for s in sections}
        
        for change in changes:
            section = change.location.section if change.location.section else "unknown"
            if section in section_density:
                section_density[section] += 1
        
        # Normalize
        max_density = max(section_density.values()) if max(section_density.values()) > 0 else 1
        for section in section_density:
            section_density[section] /= max_density
        
        return section_density
    
    def get_hotspots(self, page_density: Dict[int, float], threshold: float = 0.7) -> List[int]:
        """Identify hotspot pages with high change density"""
        return [page for page, density in page_density.items() if density >= threshold]


class SimilarityGrader:
    """Grade similarity scores into human-readable categories"""
    
    @staticmethod
    def grade_similarity(score: float) -> Dict[str, Any]:
        """Convert numerical score to grade"""
        if score >= 0.95:
            return {"grade": "A+", "label": "Nearly Identical", "color": "green"}
        elif score >= 0.90:
            return {"grade": "A", "label": "Very Similar", "color": "lightgreen"}
        elif score >= 0.80:
            return {"grade": "B", "label": "Similar", "color": "yellowgreen"}
        elif score >= 0.70:
            return {"grade": "C", "label": "Moderately Similar", "color": "yellow"}
        elif score >= 0.50:
            return {"grade": "D", "label": "Different", "color": "orange"}
        else:
            return {"grade": "F", "label": "Very Different", "color": "red"}