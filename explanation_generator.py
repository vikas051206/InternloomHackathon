"""
Explanation generator for top 3 candidates.
Uses deterministic matching results, not LLM judgment.
"""

from typing import List, Dict
from skill_matcher import SkillMatcher


class ExplanationGenerator:
    """Generate traceable explanations for top candidates."""
    
    def __init__(self):
        self.skill_matcher = SkillMatcher()
    
    def generate_explanation(
        self,
        candidate: Dict,
        skill_match_result: Dict,
        jd_summary: Dict
    ) -> Dict:
        """
        Generate explanation for a single candidate.
        
        Args:
            candidate: Candidate dictionary
            skill_match_result: Skill matching results
            jd_summary: JD information
            
        Returns:
            Explanation dictionary
        """
        # Extract matched and missing skills from deterministic matcher
        matched_skills = [
            m["matched_skill"] for m in skill_match_result.get("matched_required", [])
        ]
        missing_skills = skill_match_result.get("missing_required", [])
        
        # Get evidence snippets for matched skills
        skill_evidence = {}
        for match in skill_match_result.get("matched_required", []):
            evidence = self.skill_matcher.get_skill_evidence(
                match["matched_skill"],
                candidate.get("raw_text", "")
            )
            skill_evidence[match["matched_skill"]] = evidence
        
        # Generate deterministic summary based on scores
        summary = self._generate_deterministic_summary(
            candidate,
            skill_match_result,
            jd_summary
        )
        
        return {
            "name": candidate["name"],
            "final_score": candidate.get("final_score", 0),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "skill_evidence": skill_evidence,
            "required_match_count": skill_match_result.get("required_match_count", 0),
            "total_required": len(jd_summary.get("required_skills", [])),
            "summary": summary
        }
    
    def _generate_deterministic_summary(
        self,
        candidate: Dict,
        skill_match_result: Dict,
        jd_summary: Dict
    ) -> str:
        """
        Generate a summary based on deterministic scores, not LLM.
        
        Args:
            candidate: Candidate dictionary
            skill_match_result: Skill matching results
            jd_summary: JD information
            
        Returns:
            Summary string
        """
        keyword_score = skill_match_result.get("keyword_score", 0)
        semantic_score = candidate.get("semantic_score", 0)
        final_score = candidate.get("final_score", 0)
        
        required_matched = skill_match_result.get("required_match_count", 0)
        total_required = len(jd_summary.get("required_skills", []))
        
        # Build summary based on actual metrics
        if final_score >= 80:
            performance = "excellent match"
        elif final_score >= 60:
            performance = "strong match"
        elif final_score >= 40:
            performance = "moderate match"
        else:
            performance = "limited match"
        
        summary_parts = [
            f"Candidate ranks {candidate.get('rank', 'N/A')} with a {performance}. "
        ]
        
        if total_required > 0:
            match_pct = (required_matched / total_required) * 100
            summary_parts.append(
                f"Matches {required_matched}/{total_required} required skills ({match_pct:.0f}%). "
            )
        
        if keyword_score > semantic_score:
            summary_parts.append(
                f"Stronger on explicit skill matching ({keyword_score:.1f}) "
                f"than semantic fit ({semantic_score:.1f})."
            )
        elif semantic_score > keyword_score:
            summary_parts.append(
                f"Stronger on conceptual fit ({semantic_score:.1f}) "
                f"than explicit skills ({keyword_score:.1f})."
            )
        else:
            summary_parts.append(
                f"Balanced skill and semantic scores ({keyword_score:.1f})."
            )
        
        if skill_match_result.get("missing_required"):
            summary_parts.append(
                f" Missing key skills: {', '.join(skill_match_result['missing_required'][:3])}."
            )
        
        return "".join(summary_parts).strip()
    
    def generate_top_3_explanations(
        self,
        ranked_candidates: List[Dict],
        skill_match_results: List[Dict],
        jd_summary: Dict
    ) -> List[Dict]:
        """
        Generate explanations for top 3 candidates.
        
        Args:
            ranked_candidates: Ranked list of all candidates
            skill_match_results: Skill matching results for all candidates
            jd_summary: JD information
            
        Returns:
            List of explanations for top 3
        """
        top_3 = ranked_candidates[:3]
        explanations = []
        
        for candidate in top_3:
            # Find corresponding skill match result
            skill_result = None
            for i, cand in enumerate(ranked_candidates):
                if cand["name"] == candidate["name"]:
                    skill_result = skill_match_results[i]
                    break
            
            if skill_result:
                explanation = self.generate_explanation(
                    candidate,
                    skill_result,
                    jd_summary
                )
                explanations.append(explanation)
        
        return explanations
