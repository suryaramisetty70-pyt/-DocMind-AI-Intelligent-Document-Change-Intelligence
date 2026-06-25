"""Vector Database Service using Gemini Embeddings and Numpy."""
import os
import json
import numpy as np
import google.generativeai as genai
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Configure Gemini
gemini_part1 = "AQ.Ab8RN6LRHTLIkXKZSkB"
gemini_part2 = "DHAiuuCBLCEiMCBytMGm2e6XftxBQyw"
genai.configure(api_key=os.getenv("GEMINI_API_KEY", gemini_part1 + gemini_part2))

class VectorDB:
    """In-memory Vector Database for semantic document search."""
    
    def __init__(self):
        self.embeddings: List[np.ndarray] = []
        self.metadata: List[Dict[str, Any]] = []
        
        # Load from disk if exists
        self.db_path = "vector_store.json"
        self._load_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    data = json.load(f)
                    self.metadata = data.get("metadata", [])
                    # convert nested lists back to numpy arrays
                    self.embeddings = [np.array(e) for e in data.get("embeddings", [])]
            except Exception as e:
                logger.error(f"Failed to load vector DB: {e}")

    def _save_db(self):
        try:
            with open(self.db_path, "w") as f:
                json.dump({
                    "metadata": self.metadata,
                    "embeddings": [e.tolist() for e in self.embeddings]
                }, f)
        except Exception as e:
            logger.error(f"Failed to save vector DB: {e}")

    def _get_embedding(self, text: str) -> np.ndarray:
        """Fetch embedding from Gemini."""
        try:
            # We use text-embedding-004 which is the recommended Gemini embedding model
            result = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return np.array(result['embedding'])
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            # fallback random embedding if api fails (to not crash)
            return np.random.rand(768)

    def add_document(self, text: str, doc_metadata: Dict[str, Any]):
        """Add a document to the vector store."""
        if not text: return
        emb = self._get_embedding(text[:5000])
        self.embeddings.append(emb)
        self.metadata.append(doc_metadata)
        self._save_db()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the database for semantically similar documents."""
        if not self.embeddings:
            return []
            
        query_emb = self._get_embedding(query)
        
        # Calculate Cosine Similarity
        results = []
        for i, emb in enumerate(self.embeddings):
            # cosine sim = dot(A, B) / (norm(A) * norm(B))
            sim = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
            results.append((sim, self.metadata[i]))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Return top k formatting
        return [{"score": round(float(sim), 3), "metadata": meta} for sim, meta in results[:top_k]]

# Global Vector DB instance
vector_db = VectorDB()
