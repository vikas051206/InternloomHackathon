"""
Main pipeline orchestrator for the Smart Shortlisting Engine.
"""

import os
from typing import List, Dict
from pdf_parser import PDFParser
from skill_matcher import SkillMatcher
from semantic_matcher import SemanticMatcher
from score_fusion import ScoreFusion
from ranking import RankingEngine
from explanation_generator import ExplanationGenerator
from database import MongoDB


class ShortlistingPipeline:
    """Orchestrate the entire shortlisting pipeline."""
    
    def __init__(self, use_mongodb: bool = True):
        self.pdf_parser = PDFParser()
        self.skill_matcher = SkillMatcher()
        self.semantic_matcher = SemanticMatcher()
        self.score_fusion = ScoreFusion()
        self.ranking_engine = RankingEngine()
        self.explanation_generator = ExplanationGenerator()
        self.db = MongoDB() if use_mongodb else None
    
    def run(
        self,
        jd_path: str,
        resume_folder: str,
        output_path: str = "output.json"
    ) -> Dict:
        """
        Run the complete shortlisting pipeline.
        
        Args:
            jd_path: Path to JD PDF
            resume_folder: Path to folder containing resume PDFs
            output_path: Path to save output JSON
            
        Returns:
            Complete output dictionary
        """
        print("="*80)
        print("SMART SHORTLISTING ENGINE - PIPELINE START")
        print("="*80)
        
        # Stage 1: Data Ingestion
        print("\n[Stage 1] Data Ingestion & Parsing")
        print("-" * 80)
        jd_summary = self._parse_jd(jd_path)
        candidates = self._parse_resumes(resume_folder)
        print(f"Parsed JD: {jd_summary['role_title']}")
        print(f"Parsed {len(candidates)} resumes")
        
        # Stage 2: Keyword Matching
        print("\n[Stage 2] Keyword/Skill Matching")
        print("-" * 80)
        skill_match_results = []
        for candidate in candidates:
            result = self.skill_matcher.match_skills(
                jd_summary["required_skills"],
                jd_summary["nice_to_have_skills"],
                candidate["skills"]
            )
            skill_match_results.append(result)
            candidate["keyword_score"] = result["keyword_score"]
        print(f"Keyword matching complete for {len(candidates)} candidates")
        
        # Stage 3: Semantic Matching
        print("\n[Stage 3] Semantic Matching")
        print("-" * 80)
        for i, candidate in enumerate(candidates):
            result = self.semantic_matcher.match_semantic(
                jd_summary["responsibilities"],
                jd_summary["raw_text"],
                candidate["experience"],
                candidate["projects"]
            )
            candidate["semantic_score"] = result["semantic_score"]
            if (i + 1) % 5 == 0:
                print(f"Processed {i + 1}/{len(candidates)} candidates")
        print("Semantic matching complete")
        
        # Stage 4: Score Fusion
        print("\n[Stage 4] Score Fusion & Normalization")
        print("-" * 80)
        candidates = self.score_fusion.normalize_scores(candidates)
        print(f"Scores normalized using {self.score_fusion.keyword_weight}/{self.score_fusion.semantic_weight} weights")
        
        # Stage 5: Ranking
        print("\n[Stage 5] Ranking")
        print("-" * 80)
        ranked_candidates = self.ranking_engine.rank_candidates(candidates)
        print(f"Ranked {len(ranked_candidates)} candidates")
        
        # Stage 6: Explanation Generation
        print("\n[Stage 6] Explanation Generation (Top 3)")
        print("-" * 80)
        top_3_explanations = self.explanation_generator.generate_top_3_explanations(
            ranked_candidates,
            skill_match_results,
            jd_summary
        )
        print("Generated explanations for top 3 candidates")
        
        # Stage 7: Output Generation
        print("\n[Stage 7] Output Generation")
        print("-" * 80)
        output = self.ranking_engine.generate_output(
            jd_summary,
            ranked_candidates,
            top_3_explanations
        )
        
        # Save output
        self.ranking_engine.save_output(output, output_path)
        
        # Save to MongoDB if enabled
        if self.db:
            mongo_id = self.db.save_shortlisting_result(
                jd_path=jd_path,
                output=output,
                resume_count=len(candidates)
            )
            if mongo_id:
                print(f"Result saved to MongoDB with ID: {mongo_id}")
        
        # Print summary
        self.ranking_engine.print_summary(output)
        
        print("\n" + "="*80)
        print("PIPELINE COMPLETE")
        print("="*80)
        
        return output
    
    def _parse_jd(self, jd_path: str) -> Dict:
        """Parse JD PDF."""
        print(f"Parsing JD: {jd_path}")
        jd_text = self.pdf_parser.parse_pdf(jd_path)
        if not jd_text:
            raise ValueError(f"Failed to parse JD: {jd_path}")
        
        jd_summary = self.pdf_parser.extract_jd_info(jd_text)
        return jd_summary
    
    def _parse_resumes(self, resume_folder: str) -> List[Dict]:
        """Parse all resume PDFs in folder."""
        candidates = []
        
        if not os.path.exists(resume_folder):
            raise ValueError(f"Resume folder not found: {resume_folder}")
        
        resume_files = [
            f for f in os.listdir(resume_folder)
            if f.lower().endswith('.pdf')
        ]
        
        print(f"Found {len(resume_files)} resume PDFs")
        
        for i, resume_file in enumerate(resume_files):
            resume_path = os.path.join(resume_folder, resume_file)
            print(f"  [{i+1}/{len(resume_files)}] Parsing: {resume_file}")
            
            try:
                resume_text = self.pdf_parser.parse_pdf(resume_path)
                if resume_text:
                    candidate = self.pdf_parser.extract_resume_info(resume_text)
                    candidate["resume_file"] = resume_file
                    candidates.append(candidate)
                else:
                    print(f"    Warning: Empty text from {resume_file}")
            except Exception as e:
                print(f"    Error parsing {resume_file}: {e}")
                # Create placeholder candidate to avoid crashing
                candidates.append({
                    "name": f"Unknown ({resume_file})",
                    "skills": [],
                    "experience": [],
                    "projects": [],
                    "education": [],
                    "years_of_experience": 0,
                    "raw_text": "",
                    "resume_file": resume_file
                })
        
        return candidates
