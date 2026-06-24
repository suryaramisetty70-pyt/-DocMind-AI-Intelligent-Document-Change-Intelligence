"""AI Engine for semantic comparison and analysis."""
from typing import Dict, Any, List, Tuple
import numpy as np
try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None


class AIEngine:
    """Engine for AI-powered semantic analysis."""
    
    _model = None
    
    @classmethod
    def get_model(cls):
        """Get or initialize the sentence transformer model."""
        if cls._model is None:
            try:
                cls._model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Model loading failed: {e}")
                cls._model = "unavailable"
        return cls._model if cls._model != "unavailable" else None

    @staticmethod
    def compare_semantically(text1: str, text2: str) -> Dict[str, Any]:
        """
        Compare two texts semantically using sentence transformers.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Semantic comparison results
        """
        model = AIEngine.get_model()
        
        if model is None:
            return {
                "error": "AI model not available",
                "fallback": True,
                "similarity_score": 0.0
            }
        
        try:
            # Encode texts
            embeddings1 = model.encode(text1, convert_to_tensor=True)
            embeddings2 = model.encode(text2, convert_to_tensor=True)
            
            # Calculate cosine similarity
            cosine_sim = util.cos_sim(embeddings1, embeddings2).item()
            
            # Split into sentences for detailed analysis
            import re
            sentences1 = re.split(r'[.!?]+', text1)
            sentences2 = re.split(r'[.!?]+', text2)
            
            sentences1 = [s.strip() for s in sentences1 if s.strip()]
            sentences2 = [s.strip() for s in sentences2 if s.strip()]
            
            # Compare sentences
            sentence_similarities = []
            for s1 in sentences1[:10]:  # Limit to first 10 for performance
                if not s1:
                    continue
                best_match = 0
                best_match_text = ""
                for s2 in sentences2[:10]:
                    if not s2:
                        continue
                    emb1 = model.encode(s1, convert_to_tensor=True)
                    emb2 = model.encode(s2, convert_to_tensor=True)
                    sim = util.cos_sim(emb1, emb2).item()
                    if sim > best_match:
                        best_match = sim
                        best_match_text = s2
                sentence_similarities.append({
                    "text": s1[:100],
                    "best_match": best_match_text[:100] if best_match_text else "",
                    "similarity": best_match
                })
            
            return {
                "type": "semantic",
                "similarity_score": float(cosine_sim),
                "similarity_percentage": round(cosine_sim * 100, 2),
                "sentence_comparisons": sentence_similarities,
                "is_semantically_similar": cosine_sim > 0.7,
                "paraphrase_detected": 0.5 < cosine_sim < 0.9
            }
        except Exception as e:
            return {
                "error": str(e),
                "fallback": True,
                "similarity_score": 0.0
            }

    @staticmethod
    def summarize_changes(comparison_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of changes.
        
        Args:
            comparison_result: Result from comparison engine
        
        Returns:
            Summary string
        """
        summary_parts = []
        
        score = comparison_result.get("similarity_score", 0)
        score_pct = round(score * 100, 1)
        
        summary_parts.append(f"Overall similarity: {score_pct}%")
        
        additions = comparison_result.get("total_additions", 0)
        deletions = comparison_result.get("total_deletions", 0)
        
        if additions > 0:
            summary_parts.append(f"Added: {additions} items")
        if deletions > 0:
            summary_parts.append(f"Deleted: {deletions} items")
        
        if "modifications" in comparison_result:
            mods = len(comparison_result["modifications"])
            if mods > 0:
                summary_parts.append(f"Modified: {mods} items")
        
        return ". ".join(summary_parts)

    @staticmethod
    def classify_importance(text_chunk: str) -> str:
        """
        Classify the importance of a text chunk.
        
        Args:
            text_chunk: Text to classify
        
        Returns:
            Importance level: 'critical', 'high', 'medium', or 'low'
        """
        critical_keywords = [
            "payment", "salary", "contract", "agreement", "legal", "confidential",
            "ssn", "social security", "bank", "account number", "password"
        ]
        
        high_keywords = [
            "deadline", "important", "urgent", "required", "mandatory",
            "policy", "rule", "regulation", "must", "shall"
        ]
        
        medium_keywords = [
            "should", "recommend", "suggest", "consider", "may", "might"
        ]
        
        text_lower = text_chunk.lower()
        
        for keyword in critical_keywords:
            if keyword in text_lower:
                return "critical"
        
        for keyword in high_keywords:
            if keyword in text_lower:
                return "high"
        
        for keyword in medium_keywords:
            if keyword in text_lower:
                return "medium"
        
        return "low"

    @staticmethod
    def detect_semantic_changes(text1: str, text2: str) -> List[Dict[str, Any]]:
        """
        Detect semantically similar but differently worded content.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            List of detected semantic changes
        """
        model = AIEngine.get_model()
        
        if model is None:
            return []
        
        import re
        sentences1 = [s.strip() for s in re.split(r'[.!?]+', text1) if s.strip()]
        sentences2 = [s.strip() for s in re.split(r'[.!?]+', text2) if s.strip()]
        
        changes = []
        
        for s1 in sentences1:
            if not s1 or len(s1) < 10:
                continue
            
            emb1 = model.encode(s1, convert_to_tensor=True)
            best_match = 0
            best_match_text = ""
            best_match_idx = -1
            
            for i, s2 in enumerate(sentences2):
                if not s2 or len(s2) < 10:
                    continue
                emb2 = model.encode(s2, convert_to_tensor=True)
                sim = util.cos_sim(emb1, emb2).item()
                if sim > best_match:
                    best_match = sim
                    best_match_text = s2
                    best_match_idx = i
            
            # If there's a good semantic match but different text
            if 0.5 < best_match < 0.95 and best_match_text:
                changes.append({
                    "original": s1,
                    "modified": best_match_text,
                    "similarity": best_match,
                    "is_paraphrase": True
                })
        
        return changes[:20]  # Limit results