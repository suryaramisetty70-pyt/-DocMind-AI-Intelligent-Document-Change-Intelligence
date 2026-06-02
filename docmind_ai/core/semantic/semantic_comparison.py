"""
DocMind AI - Semantic Comparison Engine
AI-powered document comparison using Sentence Transformers
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import re


@dataclass
class SemanticChange:
    """A semantically significant change"""
    change_id: str
    original_text: str
    modified_text: str
    semantic_similarity: float
    meaning_preserved: bool
    meaning_altered: bool
    paraphrased: bool
    rephrased_similarity: float
    content_preserved: float
    significance_score: float
    explanation: str
    category: str


@dataclass
class SemanticComparisonResult:
    """Complete semantic comparison result"""
    overall_semantic_similarity: float
    meaning_preserved_changes: List[SemanticChange]
    meaning_altered_changes: List[SemanticChange]
    paraphrased_content: List[SemanticChange]
    statistics: Dict[str, Any]
    embeddings_computed: bool = False
    processing_time: float = 0.0
    model_name: str = ""


class SemanticExtractor:
    """Extract semantic units for comparison"""
    
    def __init__(self):
        self.sentence_splitter = re.compile(r'(?<=[.!?])\s+')
        self.paragraph_splitter = re.compile(r'\n\s*\n')
    
    def extract_sentences(self, text: str) -> List[Tuple[str, int]]:
        """Extract sentences with positions"""
        sentences = []
        for idx, sentence in enumerate(self.sentence_splitter.split(text)):
            if sentence.strip():
                sentences.append((sentence.strip(), idx))
        return sentences
    
    def extract_paragraphs(self, text: str) -> List[Tuple[str, int]]:
        """Extract paragraphs with positions"""
        paragraphs = []
        parts = self.paragraph_splitter.split(text)
        for idx, para in enumerate(parts):
            if para.strip():
                paragraphs.append((para.strip(), idx))
        return paragraphs
    
    def extract_semantic_chunks(self, text: str, chunk_size: int = 512) -> List[str]:
        """Extract semantic chunks for embedding"""
        sentences = self.extract_sentences(text)
        chunks = []
        current_chunk = ""
        
        for sentence, _ in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


class SentenceTransformerEmbedder:
    """Handle sentence transformer embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Lazy load the model"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
    
    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Encode texts to embeddings"""
        self._load_model()
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        return embeddings
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two texts"""
        embeddings = self.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    
    def compute_similarities(self, texts1: List[str], texts2: List[str]) -> List[float]:
        """Compute similarities between two sets of texts"""
        embeddings1 = self.encode(texts1)
        embeddings2 = self.encode(texts2)
        
        similarities = []
        for emb1 in embeddings1:
            sims = cosine_similarity([emb1], embeddings2)[0]
            similarities.append(float(np.max(sims)))
        
        return similarities


class ParaphraseDetector:
    """Detect paraphrased content"""
    
    def __init__(self, embedder: SentenceTransformerEmbedder):
        self.embedder = embedder
        self.threshold = 0.75
        self.high_similarity_threshold = 0.90
    
    def detect_paraphrase(self, original: str, modified: str) -> Tuple[bool, float, str]:
        """Detect if content is paraphrased"""
        similarity = self.embedder.compute_similarity(original, modified)
        
        is_paraphrase = False
        explanation = ""
        
        if similarity >= self.high_similarity_threshold:
            is_paraphrase = False  # Nearly identical, not paraphrased
            explanation = "Content is nearly identical"
        elif similarity >= self.threshold:
            is_paraphrase = True
            explanation = f"Content appears paraphrased (similarity: {similarity:.2%})"
        else:
            explanation = f"Content is semantically different (similarity: {similarity:.2%})"
        
        return is_paraphrase, similarity, explanation
    
    def find_paraphrased_pairs(self, originals: List[str], modifieds: List[str]) -> List[Dict[str, Any]]:
        """Find all paraphrased pairs between two sets of texts"""
        results = []
        
        for orig_idx, original in enumerate(originals):
            best_match = None
            best_similarity = 0
            
            for mod_idx, modified in enumerate(modifieds):
                similarity = self.embedder.compute_similarity(original, modified)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = {
                        "original_index": orig_idx,
                        "modified_index": mod_idx,
                        "original_text": original,
                        "modified_text": modified,
                        "similarity": similarity
                    }
            
            if best_match and best_match["similarity"] >= self.threshold:
                results.append(best_match)
        
        return results


class MeaningPreservationAnalyzer:
    """Analyze if meaning is preserved in changes"""
    
    def __init__(self, embedder: SentenceTransformerEmbedder):
        self.embedder = embedder
    
    def analyze(self, original: str, modified: str) -> Dict[str, Any]:
        """Analyze meaning preservation"""
        similarity = self.embedder.compute_similarity(original, modified)
        
        # Analyze key entities
        orig_entities = self._extract_entities(original)
        mod_entities = self._extract_entities(modified)
        
        entities_preserved = len(orig_entities & mod_entities) / len(orig_entities) if orig_entities else 1.0
        
        # Analyze key terms
        orig_terms = self._extract_key_terms(original)
        mod_terms = self._extract_key_terms(modified)
        
        terms_preserved = len(orig_terms & mod_terms) / len(orig_terms) if orig_terms else 1.0
        
        # Overall meaning preservation
        meaning_preserved = similarity >= 0.85 and entities_preserved >= 0.8
        
        return {
            "semantic_similarity": similarity,
            "entities_preserved": entities_preserved,
            "terms_preserved": terms_preserved,
            "meaning_preserved": meaning_preserved,
            "meaning_altered": not meaning_preserved and similarity < 0.70,
            "new_entities": mod_entities - orig_entities,
            "removed_entities": orig_entities - mod_entities
        }
    
    def _extract_entities(self, text: str) -> set:
        """Extract key entities (simplified)"""
        # Simple noun phrase extraction
        words = text.split()
        # Return capitalized words as potential entities
        return {w for w in words if w and w[0].isupper() and len(w) > 2}
    
    def _extract_key_terms(self, text: str) -> set:
        """Extract key terms from text"""
        words = text.lower().split()
        # Remove stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                    'should', 'may', 'might', 'must', 'shall', 'can', 'and', 'or', 'but',
                    'if', 'then', 'else', 'when', 'at', 'by', 'for', 'with', 'about',
                    'into', 'through', 'during', 'before', 'after', 'above', 'below'}
        return {w for w in words if w not in stopwords and len(w) > 3}


class SemanticComparisonEngine:
    """Main semantic comparison engine"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedder = SentenceTransformerEmbedder(model_name)
        self.extractor = SemanticExtractor()
        self.paraphrase_detector = ParaphraseDetector(self.embedder)
        self.meaning_analyzer = MeaningPreservationAnalyzer(self.embedder)
        self.threshold = 0.75
        self.paraphrase_threshold = 0.75
        self.meaning_altered_threshold = 0.70
    
    def compare(self, original: str, modified: str) -> SemanticComparisonResult:
        """Perform semantic comparison"""
        import time
        start_time = time.time()
        
        # Extract semantic units
        orig_sentences = self.extractor.extract_sentences(original)
        mod_sentences = self.extractor.extract_sentences(modified)
        
        orig_texts = [s[0] for s in orig_sentences]
        mod_texts = [s[0] for s in mod_sentences]
        
        # Compute embeddings
        embeddings_original = self.embedder.encode(orig_texts)
        embeddings_modified = self.embedder.encode(mod_texts)
        
        # Find matching pairs
        meaning_preserved_changes = []
        meaning_altered_changes = []
        paraphrased_content = []
        
        # Track matched originals to detect additions
        matched_originals = set()
        matched_mods = set()
        
        for i, orig_text in enumerate(orig_texts):
            best_similarity = 0
            best_match_idx = -1
            
            for j, mod_text in enumerate(mod_texts):
                similarity = float(util.cos_sim(embeddings_original[i], embeddings_modified[j])[0][0])
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_idx = j
            
            if best_match_idx >= 0:
                matched_originals.add(i)
                matched_mods.add(best_match_idx)
                
                analysis = self.meaning_analyzer.analyze(orig_text, mod_text)
                
                is_paraphrase, para_sim, para_explanation = self.paraphrase_detector.detect_paraphrase(
                    orig_text, mod_text
                )
                
                semantic_change = SemanticChange(
                    change_id=f"change_{i}_{best_match_idx}",
                    original_text=orig_text,
                    modified_text=mod_text,
                    semantic_similarity=best_similarity,
                    meaning_preserved=analysis["meaning_preserved"],
                    meaning_altered=analysis["meaning_altered"],
                    paraphrased=is_paraphrase,
                    rephrased_similarity=para_sim,
                    content_preserved=best_similarity,
                    significance_score=best_similarity * (1 if analysis["meaning_preserved"] else -1),
                    explanation=para_explanation if is_paraphrase else analysis.get("entities_preserved", 0),
                    category="paraphrase" if is_paraphrase else ("preserved" if analysis["meaning_preserved"] else "altered")
                )
                
                if is_paraphrase:
                    paraphrased_content.append(semantic_change)
                elif analysis["meaning_preserved"]:
                    meaning_preserved_changes.append(semantic_change)
                elif analysis["meaning_altered"]:
                    meaning_altered_changes.append(semantic_change)
        
        # Detect pure additions (new content in modified)
        for j, mod_text in enumerate(mod_texts):
            if j not in matched_mods:
                semantic_change = SemanticChange(
                    change_id=f"addition_{j}",
                    original_text="",
                    modified_text=mod_text,
                    semantic_similarity=0.0,
                    meaning_preserved=False,
                    meaning_altered=True,
                    paraphrased=False,
                    rephrased_similarity=0.0,
                    content_preserved=0.0,
                    significance_score=0.5,
                    explanation="New content added",
                    category="addition"
                )
                meaning_altered_changes.append(semantic_change)
        
        # Calculate overall semantic similarity
        if embeddings_original.shape[0] > 0 and embeddings_modified.shape[0] > 0:
            overall_similarity = float(util.cos_sim(embeddings_original.mean(axis=0, keepdims=True),
                                                   embeddings_modified.mean(axis=0, keepdims=True))[0][0])
        else:
            overall_similarity = 0.0
        
        statistics = {
            "original_sentences": len(orig_texts),
            "modified_sentences": len(mod_texts),
            "meaning_preserved_count": len(meaning_preserved_changes),
            "meaning_altered_count": len(meaning_altered_changes),
            "paraphrased_count": len(paraphrased_content),
            "additions_count": len([c for c in meaning_altered_changes if c.category == "addition"]),
            "embeddings_dim": embeddings_original.shape[1] if len(embeddings_original) > 0 else 0
        }
        
        return SemanticComparisonResult(
            overall_semantic_similarity=overall_similarity,
            meaning_preserved_changes=meaning_preserved_changes,
            meaning_altered_changes=meaning_altered_changes,
            paraphrased_content=paraphrased_content,
            statistics=statistics,
            embeddings_computed=True,
            processing_time=time.time() - start_time,
            model_name=self.model_name
        )
    
    def compare_chunks(self, original: str, modified: str, chunk_size: int = 512) -> SemanticComparisonResult:
        """Compare documents using semantic chunks"""
        orig_chunks = self.extractor.extract_semantic_chunks(original, chunk_size)
        mod_chunks = self.extractor.extract_semantic_chunks(modified, chunk_size)
        
        # Similar comparison logic but with chunks
        return self.compare(" ".join(orig_chunks), " ".join(mod_chunks))
    
    def get_semantic_hash(self, text: str) -> str:
        """Generate semantic hash for document"""
        embeddings = self.embedder.encode([text])
        return str(embeddings[0].sum())[:16]


class ContentReorderingDetector:
    """Detect content that has been reordered"""
    
    def __init__(self, embedder: SentenceTransformerEmbedder):
        self.embedder = embedder
    
    def detect_reordering(self, original: List[str], modified: List[str]) -> List[Dict[str, Any]]:
        """Detect content reordering between documents"""
        reorderings = []
        
        # Compute all pairwise similarities
        orig_embeddings = self.embedder.encode(original)
        mod_embeddings = self.embedder.encode(modified)
        
        similarity_matrix = cosine_similarity(orig_embeddings, mod_embeddings)
        
        # Find optimal matching using Hungarian algorithm style approach
        # (simplified greedy matching for now)
        matched_originals = set()
        matched_mods = set()
        
        # Sort by highest similarity first
        pairs = []
        for i in range(len(original)):
            for j in range(len(modified)):
                pairs.append((i, j, similarity_matrix[i][j]))
        
        pairs.sort(key=lambda x: -x[2])
        
        for orig_idx, mod_idx, similarity in pairs:
            if orig_idx not in matched_originals and mod_idx not in matched_mods:
                if similarity > 0.7:
                    matched_originals.add(orig_idx)
                    matched_mods.add(mod_idx)
                    
                    # Check if position changed significantly
                    if orig_idx != mod_idx:
                        reorderings.append({
                            "original_index": orig_idx,
                            "modified_index": mod_idx,
                            "original_text": original[orig_idx],
                            "modified_text": modified[mod_idx],
                            "similarity": similarity,
                            "from_position": orig_idx,
                            "to_position": mod_idx,
                            "movement_distance": abs(mod_idx - orig_idx)
                        })
        
        return reorderings