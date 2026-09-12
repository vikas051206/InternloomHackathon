"""
Semantic matching module using sentence embeddings.
"""

from typing import List, Dict
import numpy as np
from config import EMBEDDING_MODEL, TOP_K_CHUNKS

try:
    from sentence_transformers import SentenceTransformer
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    print("Warning: sentence-transformers not available. Semantic matching disabled.")


class SemanticMatcher:
    """Match JD and resumes using semantic similarity."""
    
    def __init__(self):
        if SEMANTIC_AVAILABLE:
            print(f"Loading embedding model: {EMBEDDING_MODEL}")
            self.model = SentenceTransformer(EMBEDDING_MODEL)
        else:
            self.model = None
            print("Semantic matching disabled - using keyword-only matching")
    
    def chunk_text(self, text: str, chunk_size: int = 3) -> List[str]:
        """
        Chunk text into sentences or small paragraphs.
        
        Args:
            text: Input text
            chunk_size: Number of sentences per chunk
            
        Returns:
            List of text chunks
        """
        # Split by sentences
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        
        # Group sentences into chunks
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunk = ". ".join(sentences[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def compute_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Compute embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings
        """
        if not texts or not SEMANTIC_AVAILABLE or self.model is None:
            return np.array([])
        
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score
        """
        if vec1.size == 0 or vec2.size == 0:
            return 0.0
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def match_semantic(
        self,
        jd_responsibilities: List[str],
        jd_description: str,
        resume_experience: List[str],
        resume_projects: List[str]
    ) -> Dict:
        """
        Compute semantic similarity between JD and resume.
        
        Args:
            jd_responsibilities: JD responsibility descriptions
            jd_description: Full JD description text
            resume_experience: Resume work experience
            resume_projects: Resume project descriptions
            
        Returns:
            Dictionary with semantic match results
        """
        # Prepare JD chunks
        jd_chunks = []
        if jd_responsibilities:
            jd_chunks.extend(jd_responsibilities)
        
        # Add JD description as chunks if no responsibilities
        if not jd_chunks and jd_description:
            jd_chunks = self.chunk_text(jd_description)
        
        # Prepare resume chunks
        resume_chunks = []
        if resume_experience:
            resume_chunks.extend(resume_experience)
        if resume_projects:
            resume_chunks.extend(resume_projects)
        
        # If no structured sections, chunk the full text
        if not resume_chunks:
            # This would need full resume text, but we only have structured sections
            # For now, return low score
            return {
                "semantic_score": 0.0,
                "top_similarities": [],
                "jd_chunks_used": jd_chunks,
                "resume_chunks_used": []
            }
        
        # Compute embeddings
        jd_embeddings = self.compute_embeddings(jd_chunks)
        resume_embeddings = self.compute_embeddings(resume_chunks)
        
        if jd_embeddings.size == 0 or resume_embeddings.size == 0:
            return {
                "semantic_score": 0.0,
                "top_similarities": [],
                "jd_chunks_used": jd_chunks,
                "resume_chunks_used": resume_chunks
            }
        
        # Compute pairwise similarities
        similarities = []
        for jd_emb in jd_embeddings:
            for resume_emb in resume_embeddings:
                sim = self.cosine_similarity(jd_emb, resume_emb)
                similarities.append(sim)
        
        # Get top-k similarities
        if similarities:
            similarities_sorted = sorted(similarities, reverse=True)
            top_k = similarities_sorted[:TOP_K_CHUNKS]
            avg_top_k = np.mean(top_k) if top_k else 0.0
            
            # Normalize to 0-100 (cosine similarity is -1 to 1, but typically 0 to 1 for similar texts)
            semantic_score = max(0, avg_top_k) * 100
        else:
            semantic_score = 0.0
            top_k = []
        
        return {
            "semantic_score": semantic_score,
            "top_similarities": top_k,
            "jd_chunks_used": jd_chunks,
            "resume_chunks_used": resume_chunks,
            "num_jd_chunks": len(jd_chunks),
            "num_resume_chunks": len(resume_chunks)
        }
