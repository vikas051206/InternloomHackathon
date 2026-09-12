"""
Ranking and output generation module.
"""

from typing import List, Dict
import json
from datetime import datetime


class RankingEngine:
    """Generate ranked list of candidates."""
    
    def __init__(self):
        pass
    
    def rank_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """
        Sort candidates by final score in descending order.
        
        Args:
            candidates: List of candidate dictionaries with scores
            
        Returns:
            Ranked list of candidates
        """
        # Sort by final score descending
        ranked = sorted(candidates, key=lambda x: x.get("final_score", 0), reverse=True)
        
        # Assign ranks
        for i, candidate in enumerate(ranked, 1):
            candidate["rank"] = i
        
        return ranked
    
    def generate_output(
        self,
        jd_summary: Dict,
        ranked_candidates: List[Dict],
        top_3_explanations: List[Dict]
    ) -> Dict:
        """
        Generate final output JSON.
        
        Args:
            jd_summary: Extracted JD information
            ranked_candidates: List of ranked candidates
            top_3_explanations: Explanations for top 3
            
        Returns:
            Complete output dictionary
        """
        # Prepare rankings list
        rankings = []
        for candidate in ranked_candidates:
            rankings.append({
                "rank": candidate["rank"],
                "name": candidate["name"],
                "final_score": candidate["final_score"],
                "keyword_score": round(candidate.get("keyword_score_normalized", candidate.get("keyword_score", 0)), 2),
                "semantic_score": round(candidate.get("semantic_score_normalized", candidate.get("semantic_score", 0)), 2),
                "years_of_experience": candidate.get("years_of_experience", 0)
            })
        
        # Prepare output
        output = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_candidates": len(ranked_candidates),
                "jd_role": jd_summary.get("role_title", "Unknown")
            },
            "jd_summary": {
                "role_title": jd_summary.get("role_title", "Unknown"),
                "required_skills": jd_summary.get("required_skills", []),
                "nice_to_have_skills": jd_summary.get("nice_to_have_skills", []),
                "experience_level": jd_summary.get("experience_level", "Not Specified"),
                "responsibilities_count": len(jd_summary.get("responsibilities", []))
            },
            "rankings": rankings,
            "top_3_explanations": top_3_explanations
        }
        
        return output
    
    def save_output(self, output: Dict, output_path: str) -> None:
        """
        Save output to JSON file.
        
        Args:
            output: Output dictionary
            output_path: Path to save JSON file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Output saved to {output_path}")
    
    def print_summary(self, output: Dict) -> None:
        """
        Print a human-readable summary of rankings.
        
        Args:
            output: Output dictionary
        """
        print("\n" + "="*80)
        print("SMART SHORTLISTING ENGINE - RANKING RESULTS")
        print("="*80)
        print(f"\nRole: {output['jd_summary']['role_title']}")
        print(f"Experience Level: {output['jd_summary']['experience_level']}")
        print(f"Total Candidates: {output['metadata']['total_candidates']}")
        print(f"\nRequired Skills: {', '.join(output['jd_summary']['required_skills'][:5])}")
        if len(output['jd_summary']['required_skills']) > 5:
            print(f"  ... and {len(output['jd_summary']['required_skills']) - 5} more")
        
        print("\n" + "-"*80)
        print("RANKINGS")
        print("-"*80)
        print(f"{'Rank':<6} {'Name':<30} {'Final Score':<12} {'Keyword':<10} {'Semantic':<10}")
        print("-"*80)
        
        for candidate in output["rankings"]:
            print(
                f"{candidate['rank']:<6} "
                f"{candidate['name'][:28]:<30} "
                f"{candidate['final_score']:<12.1f} "
                f"{candidate['keyword_score']:<10.1f} "
                f"{candidate['semantic_score']:<10.1f}"
            )
        
        print("\n" + "-"*80)
        print("TOP 3 EXPLANATIONS")
        print("-"*80)
        
        for i, expl in enumerate(output["top_3_explanations"], 1):
            print(f"\n#{i} - {expl['name']} (Score: {expl.get('final_score', 'N/A')})")
            print(f"  Matched Skills: {', '.join(expl['matched_skills'])}")
            print(f"  Missing Skills: {', '.join(expl['missing_skills'])}")
            print(f"  Summary: {expl['summary']}")
        
        print("\n" + "="*80)
