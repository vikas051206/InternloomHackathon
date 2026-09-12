"""
Skill matching module with normalization and fuzzy matching.
"""

from typing import List, Dict, Tuple
from rapidfuzz import fuzz, process
from config import SKILL_ALIASES, FUZZY_MATCH_THRESHOLD, REQUIRED_SKILL_WEIGHT, NICE_TO_HAVE_SKILL_WEIGHT


class SkillMatcher:
    """Match skills between JD and resumes with normalization."""
    
    def __init__(self):
        self.aliases = SKILL_ALIASES
    
    def normalize_skill(self, skill: str) -> str:
        """
        Normalize a skill name using alias dictionary.
        
        Args:
            skill: Raw skill name
            
        Returns:
            Normalized skill name
        """
        skill_lower = skill.lower().strip()
        return self.aliases.get(skill_lower, skill_lower)
    
    def fuzzy_match_skill(self, skill: str, candidate_skills: List[str]) -> Tuple[str, float]:
        """
        Fuzzy match a skill against candidate skills.
        
        Args:
            skill: Skill to match
            candidate_skills: List of candidate's skills
            
        Returns:
            Tuple of (matched_skill, similarity_score)
        """
        # Normalize the skill
        normalized_skill = self.normalize_skill(skill)
        
        # Normalize all candidate skills
        normalized_candidates = [self.normalize_skill(s) for s in candidate_skills]
        
        # Try exact match first
        if normalized_skill in normalized_candidates:
            idx = normalized_candidates.index(normalized_skill)
            return candidate_skills[idx], 100.0
        
        # Try fuzzy match
        result = process.extractOne(
            normalized_skill,
            normalized_candidates,
            scorer=fuzz.ratio
        )
        
        if result and result[1] >= FUZZY_MATCH_THRESHOLD:
            idx = normalized_candidates.index(result[0])
            return candidate_skills[idx], result[1]
        
        return None, 0.0
    
    def match_skills(
        self,
        jd_required: List[str],
        jd_nice_to_have: List[str],
        resume_skills: List[str]
    ) -> Dict:
        """
        Match JD skills against resume skills.
        
        Args:
            jd_required: Required skills from JD
            jd_nice_to_have: Nice-to-have skills from JD
            resume_skills: Skills extracted from resume
            
        Returns:
            Dictionary with match results and scores
        """
        matched_required = []
        missing_required = []
        matched_nice_to_have = []
        missing_nice_to_have = []
        
        # Match required skills
        for skill in jd_required:
            matched, score = self.fuzzy_match_skill(skill, resume_skills)
            if matched:
                matched_required.append({
                    "jd_skill": skill,
                    "matched_skill": matched,
                    "similarity": score
                })
            else:
                missing_required.append(skill)
        
        # Match nice-to-have skills
        for skill in jd_nice_to_have:
            matched, score = self.fuzzy_match_skill(skill, resume_skills)
            if matched:
                matched_nice_to_have.append({
                    "jd_skill": skill,
                    "matched_skill": matched,
                    "similarity": score
                })
            else:
                missing_nice_to_have.append(skill)
        
        # Calculate keyword score
        required_score = len(matched_required) * REQUIRED_SKILL_WEIGHT
        nice_to_have_score = len(matched_nice_to_have) * NICE_TO_HAVE_SKILL_WEIGHT
        
        # Normalize to 0-100
        max_possible = (len(jd_required) * REQUIRED_SKILL_WEIGHT + 
                       len(jd_nice_to_have) * NICE_TO_HAVE_SKILL_WEIGHT)
        
        if max_possible > 0:
            keyword_score = (required_score + nice_to_have_score) / max_possible * 100
        else:
            keyword_score = 0.0
        
        return {
            "matched_required": matched_required,
            "missing_required": missing_required,
            "matched_nice_to_have": matched_nice_to_have,
            "missing_nice_to_have": missing_nice_to_have,
            "keyword_score": keyword_score,
            "required_match_count": len(matched_required),
            "nice_to_have_match_count": len(matched_nice_to_have)
        }
    
    def get_skill_evidence(self, skill: str, resume_text: str) -> str:
        """
        Find evidence snippet for a skill in resume text.
        
        Args:
            skill: Skill to find evidence for
            resume_text: Full resume text
            
        Returns:
            Context snippet containing the skill
        """
        # Look for the skill in the text
        skill_variants = [skill, skill.lower(), skill.upper(), skill.capitalize()]
        
        for variant in skill_variants:
            if variant in resume_text:
                # Extract surrounding context
                idx = resume_text.find(variant)
                start = max(0, idx - 50)
                end = min(len(resume_text), idx + len(variant) + 50)
                return resume_text[start:end].strip()
        
        return "No direct evidence found"
