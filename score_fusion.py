"""
Score fusion module to combine keyword and semantic scores.
"""

from typing import List, Dict
from config import KEYWORD_WEIGHT, SEMANTIC_WEIGHT


class ScoreFusion:
    """Combine keyword and semantic scores into final score."""
    
    def __init__(self):
        self.keyword_weight = KEYWORD_WEIGHT
        self.semantic_weight = SEMANTIC_WEIGHT
        
        # Validate weights sum to 1
        total = self.keyword_weight + self.semantic_weight
        if abs(total - 1.0) > 0.01:
            print(f"Warning: Weights sum to {total}, normalizing...")
            self.keyword_weight = self.keyword_weight / total
            self.semantic_weight = self.semantic_weight / total
    
    def fuse_scores(
        self,
        keyword_score: float,
        semantic_score: float
    ) -> float:
        """
        Fuse keyword and semantic scores.
        
        Args:
            keyword_score: Keyword matching score (0-100)
            semantic_score: Semantic matching score (0-100)
            
        Returns:
            Final fused score (0-100)
        """
        # Ensure scores are in valid range
        keyword_score = max(0, min(100, keyword_score))
        semantic_score = max(0, min(100, semantic_score))
        
        # Apply weighted formula
        final_score = (
            self.keyword_weight * keyword_score +
            self.semantic_weight * semantic_score
        )
        
        return round(final_score, 2)
    
    def normalize_scores(self, candidates: List[Dict]) -> List[Dict]:
        """
        Normalize scores across all candidates to ensure meaningful spread.
        
        Args:
            candidates: List of candidate dictionaries with scores
            
        Returns:
            List with normalized scores
        """
        if not candidates:
            return candidates
        
        # Extract keyword and semantic scores
        keyword_scores = [c["keyword_score"] for c in candidates]
        semantic_scores = [c["semantic_score"] for c in candidates]
        
        # Min-max normalization for keyword scores
        min_kw = min(keyword_scores)
        max_kw = max(keyword_scores)
        
        if max_kw - min_kw > 0:
            for c in candidates:
                c["keyword_score_normalized"] = (
                    (c["keyword_score"] - min_kw) / (max_kw - min_kw) * 100
                )
        else:
            for c in candidates:
                c["keyword_score_normalized"] = c["keyword_score"]
        
        # Min-max normalization for semantic scores
        min_sem = min(semantic_scores)
        max_sem = max(semantic_scores)
        
        if max_sem - min_sem > 0:
            for c in candidates:
                c["semantic_score_normalized"] = (
                    (c["semantic_score"] - min_sem) / (max_sem - min_sem) * 100
                )
        else:
            for c in candidates:
                c["semantic_score_normalized"] = c["semantic_score"]
        
        # Recalculate final scores with normalized values
        for c in candidates:
            c["final_score"] = self.fuse_scores(
                c["keyword_score_normalized"],
                c["semantic_score_normalized"]
            )
        
        return candidates
    
    def get_score_breakdown(self, candidate: Dict) -> Dict:
        """
        Get detailed score breakdown for a candidate.
        
        Args:
            candidate: Candidate dictionary
            
        Returns:
            Score breakdown dictionary
        """
        return {
            "keyword_score": candidate.get("keyword_score", 0),
            "keyword_score_normalized": candidate.get("keyword_score_normalized", 0),
            "semantic_score": candidate.get("semantic_score", 0),
            "semantic_score_normalized": candidate.get("semantic_score_normalized", 0),
            "final_score": candidate.get("final_score", 0),
            "keyword_weight": self.keyword_weight,
            "semantic_weight": self.semantic_weight,
            "formula": f"final = {self.keyword_weight} * keyword + {self.semantic_weight} * semantic"
        }
