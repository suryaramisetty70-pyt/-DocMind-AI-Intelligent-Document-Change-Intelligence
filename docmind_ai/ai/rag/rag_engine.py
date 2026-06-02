"""
DocMind AI - LangChain RAG Integration
Retrieval-Augmented Generation for grounded AI responses
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import os


class EmbeddingModel(Enum):
    """Supported embedding models"""
    OPENAI_ADA = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"
    HUGGINGFACE_MINILM = "all-MiniLM-L6-v2"
    HUGGINGFACE_INSTRUCTOR = "hkunlp/instructor-large"


@dataclass
class DocumentChunk:
    """Chunk of document for embedding"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    vector_index: int = 0


@dataclass
class RetrievalResult:
    """Result from retrieval"""
    chunk: DocumentChunk
    score: float
    source: str
    relevance: str


@dataclass
class RAGResponse:
    """RAG-generated response"""
    answer: str
    sources: List[RetrievalResult]
    confidence: float
    faithfulness_score: float
    citation_used: bool


class DocumentChunker:
    """Chunk documents for embedding"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[DocumentChunk]:
        """Split text into chunks"""
        chunks = []
        metadata = metadata or {}
        
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            chunk = DocumentChunk(
                chunk_id=f"chunk_{chunk_id}",
                content=chunk_text,
                metadata={
                    **metadata,
                    "start_pos": start,
                    "end_pos": end,
                    "total_length": len(text)
                },
                vector_index=chunk_id
            )
            
            chunks.append(chunk)
            chunk_id += 1
            start = end - self.overlap
        
        return chunks
    
    def chunk_by_sentences(self, text: str, metadata: Optional[Dict] = None) -> List[DocumentChunk]:
        """Split text by sentences"""
        import re
        metadata = metadata or {}
        
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        chunks = []
        current_chunk = ""
        chunk_id = 0
        start_pos = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(DocumentChunk(
                        chunk_id=f"chunk_{chunk_id}",
                        content=current_chunk.strip(),
                        metadata={**metadata, "start_pos": start_pos},
                        vector_index=chunk_id
                    ))
                    chunk_id += 1
                    start_pos += len(current_chunk)
                
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                chunk_id=f"chunk_{chunk_id}",
                content=current_chunk.strip(),
                metadata={**metadata, "start_pos": start_pos},
                vector_index=chunk_id
            ))
        
        return chunks


class VectorStore:
    """Vector storage using FAISS"""
    
    def __init__(self, dimension: int = 384, index_type: str = "IVF"):
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.chunks: List[DocumentChunk] = []
    
    def build_index(self, chunks: List[DocumentChunk]) -> None:
        """Build FAISS index from chunks"""
        try:
            import faiss
            import numpy as np
            
            if not chunks:
                return
            
            embeddings = np.array([c.embedding for c in chunks if c.embedding]).astype('float32')
            
            if len(embeddings) == 0:
                return
            
            faiss.normalize_L2(embeddings)
            
            if self.index_type == "Flat":
                self.index = faiss.IndexFlatIP(self.dimension)
            elif self.index_type == "IVF":
                nlist = min(100, len(embeddings))
                quantizer = faiss.IndexFlatIP(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
                self.index.train(embeddings)
            else:
                self.index = faiss.IndexFlatIP(self.dimension)
            
            self.index.add(embeddings)
            self.chunks = [c for c in chunks if c.embedding]
            
        except ImportError:
            self._simple_index(chunks)
    
    def _simple_index(self, chunks: List[DocumentChunk]) -> None:
        """Simple in-memory index fallback"""
        self.chunks = [c for c in chunks if c.embedding]
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[RetrievalResult]:
        """Search for similar chunks"""
        try:
            import faiss
            import numpy as np
            
            if not self.index or not self.chunks:
                return []
            
            query = np.array([query_embedding]).astype('float32')
            faiss.normalize_L2(query)
            
            k = min(top_k, len(self.chunks))
            distances, indices = self.index.search(query, k)
            
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.chunks):
                    results.append(RetrievalResult(
                        chunk=self.chunks[idx],
                        score=float(dist),
                        source="document",
                        relevance="high" if dist > 0.8 else "medium" if dist > 0.6 else "low"
                    ))
            
            return results
            
        except Exception:
            return []
    
    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add new chunks to index"""
        self.chunks.extend(chunks)
        self.build_index(self.chunks)


class EmbeddingGenerator:
    """Generate embeddings for text chunks"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Lazy load the embedding model"""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
            except ImportError:
                pass
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        if self.model is None:
            return [[0.0] * 384 for _ in texts]
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception:
            return [[0.0] * 384 for _ in texts]


class RAGEngine:
    """Main RAG engine for document intelligence"""
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 1000,
        similarity_threshold: float = 0.7
    ):
        self.chunker = DocumentChunker(chunk_size=chunk_size)
        self.embedder = EmbeddingGenerator(model_name=embedding_model)
        self.vector_store = VectorStore()
        self.similarity_threshold = similarity_threshold
        self._context: Dict[str, Any] = {}
    
    def index_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> int:
        """Index a document for retrieval"""
        chunks = self.chunker.chunk_by_sentences(text, metadata)
        
        contents = [c.content for c in chunks]
        embeddings = self.embedder.embed(contents)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        self.vector_store.build_index(chunks)
        
        if doc_id:
            self._context[doc_id] = {
                "text": text,
                "metadata": metadata,
                "chunks": chunks
            }
        
        return len(chunks)
    
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """Retrieve relevant chunks for a query"""
        query_embedding = self.embedder.embed([query])[0]
        
        results = self.vector_store.search(query_embedding, top_k)
        
        return [r for r in results if r.score >= self.similarity_threshold]
    
    def generate_with_context(
        self,
        query: str,
        llm_callback: Optional[Callable] = None,
        system_prompt: Optional[str] = None
    ) -> RAGResponse:
        """Generate response using retrieved context"""
        retrieved = self.retrieve(query, top_k=5)
        
        if not retrieved:
            return RAGResponse(
                answer="I don't have enough context to answer this question.",
                sources=[],
                confidence=0.0,
                faithfulness_score=0.0,
                citation_used=False
            )
        
        context_parts = []
        for result in retrieved:
            context_parts.append(f"[Source {result.chunk.chunk_id}]: {result.chunk.content}")
        
        context = "\n\n".join(context_parts)
        
        if system_prompt is None:
            system_prompt = """You are a document analysis assistant. Use the provided context to answer questions."""
        
        prompt = f"""Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"""
        
        if llm_callback:
            answer = llm_callback(prompt, system_prompt)
        else:
            answer = f"Based on retrieved documents: {retrieved[0].chunk.content[:200]}..."
        
        faithfulness = self._calculate_faithfulness(answer, context)
        
        return RAGResponse(
            answer=answer,
            sources=retrieved,
            confidence=sum(r.score for r in retrieved) / len(retrieved),
            faithfulness_score=faithfulness,
            citation_used=True
        )
    
    def _calculate_faithfulness(self, answer: str, context: str) -> float:
        """Calculate faithfulness score"""
        answer_words = set(answer.lower().split())
        context_words = set(context.lower().split())
        
        overlap = len(answer_words & context_words)
        total = len(answer_words) if answer_words else 1
        
        return overlap / total
    
    def query_document(self, doc_id: str, query: str) -> RAGResponse:
        """Query a specific document"""
        if doc_id not in self._context:
            return RAGResponse(
                answer="Document not found in index.",
                sources=[],
                confidence=0.0,
                faithfulness_score=0.0,
                citation_used=False
            )
        
        return self.generate_with_context(query)
    
    def compare_documents(self, doc1_id: str, doc2_id: str, query: str) -> Dict[str, Any]:
        """Compare information across two documents"""
        results = {}
        
        for doc_id in [doc1_id, doc2_id]:
            if doc_id in self._context:
                response = self.query_document(doc_id, query)
                results[doc_id] = {
                    "answer": response.answer,
                    "confidence": response.confidence
                }
        
        return results


class HallucinationDetector:
    """Detect hallucinations in LLM outputs"""
    
    def __init__(self):
        self.threshold = 0.7
    
    def detect(
        self,
        answer: str,
        sources: List[RetrievalResult],
        original_documents: List[str]
    ) -> Dict[str, Any]:
        """Detect potential hallucinations"""
        findings = []
        
        answer_lower = answer.lower()
        source_contents = " ".join([s.chunk.content.lower() for s in sources])
        
        sentences = answer.split('.')
        for sentence in sentences:
            if len(sentence.strip()) > 20:
                words = set(sentence.lower().split())
                source_words = set(source_contents.split())
                
                novel_words = words - source_words
                if len(novel_words) > len(words) * 0.3:
                    findings.append({
                        "type": "potential_hallucination",
                        "sentence": sentence[:100],
                        "novel_word_ratio": len(novel_words) / len(words),
                        "severity": "high" if len(novel_words) > len(words) * 0.5 else "medium"
                    })
        
        hallucination_score = len(findings) * 0.2
        
        return {
            "has_hallucinations": len(findings) > 0,
            "hallucination_score": min(hallucination_score, 1.0),
            "findings": findings,
            "recommendation": "Review highlighted sections" if findings else "Content appears grounded"
        }


class KnowledgeGraphBuilder:
    """Build knowledge graphs from documents"""
    
    def __init__(self):
        self.graph: Dict[str, List[Dict[str, Any]]] = {"nodes": [], "relationships": []}
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities"""
        import re
        
        entities = []
        
        patterns = {
            "organization": r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+\b',
            "date": r'\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b',
            "money": r'\$\s*[\d,]+(?:\.\d{2})?',
            "person": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            "location": r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                entities.append({
                    "type": entity_type,
                    "value": match,
                    "confidence": 0.8
                })
        
        return entities
    
    def build_graph(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build knowledge graph from text"""
        entities = self.extract_entities(text)
        
        doc_node = {
            "id": metadata.get("doc_id", "unknown"),
            "type": "document",
            "properties": metadata
        }
        
        entity_nodes = []
        relationships = []
        
        for entity in entities:
            node_id = f"{entity['type']}_{entity['value']}"
            entity_nodes.append({
                "id": node_id,
                "type": entity["type"],
                "properties": {
                    "value": entity["value"],
                    "confidence": entity["confidence"]
                }
            })
            
            relationships.append({
                "from": metadata.get("doc_id", "unknown"),
                "to": node_id,
                "type": "contains"
            })
        
        return {
            "nodes": [doc_node] + entity_nodes,
            "relationships": relationships,
            "metadata": metadata
        }
    
    def query_graph(self, entity_type: str = None, entity_value: str = None) -> List[Dict]:
        """Query the knowledge graph"""
        results = []
        
        for node in self.graph.get("nodes", []):
            if entity_type and node.get("type") != entity_type:
                continue
            if entity_value and node.get("properties", {}).get("value") != entity_value:
                continue
            results.append(node)
        
        return results