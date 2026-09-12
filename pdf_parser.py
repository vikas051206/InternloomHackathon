"""
PDF parsing module for extracting text from JD and resume PDFs.
Handles messy formatting gracefully.
"""

import pdfplumber
import fitz  # PyMuPDF
import re
from typing import Dict, List, Optional
from config import RESUME_SECTIONS


class PDFParser:
    """Parse PDFs and extract structured information."""
    
    def __init__(self):
        self.section_patterns = self._build_section_patterns()
    
    def _build_section_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for section headers."""
        patterns = {}
        for section, headers in RESUME_SECTIONS.items():
            patterns[section] = [
                re.compile(rf"^{re.escape(h)}\s*[:\-]?$", re.IGNORECASE)
                for h in headers
            ]
        return patterns
    
    def parse_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using pdfplumber (primary) with PyMuPDF fallback.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text as string
        """
        try:
            # Try pdfplumber first
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                if text.strip():
                    return text
        except Exception as e:
            print(f"pdfplumber failed for {pdf_path}: {e}")
        
        # Fallback to PyMuPDF
        try:
            doc = fitz.open(pdf_path)
            text = "\n".join([page.get_text() for page in doc])
            doc.close()
            return text
        except Exception as e:
            print(f"PyMuPDF also failed for {pdf_path}: {e}")
            return ""
    
    def extract_jd_info(self, jd_text: str) -> Dict:
        """
        Extract structured information from job description.
        
        Args:
            jd_text: Raw text from JD PDF
            
        Returns:
            Dictionary with role, skills, responsibilities, etc.
        """
        lines = [line.strip() for line in jd_text.split("\n") if line.strip()]
        
        # Extract role title (usually first non-empty line or after "Role"/"Position")
        role_title = self._extract_role_title(lines)
        
        # Extract skills section
        required_skills, nice_to_have = self._extract_jd_skills(jd_text)
        
        # Extract responsibilities
        responsibilities = self._extract_responsibilities(jd_text)
        
        # Extract experience level
        experience_level = self._extract_experience_level(jd_text)
        
        return {
            "role_title": role_title,
            "required_skills": required_skills,
            "nice_to_have_skills": nice_to_have,
            "responsibilities": responsibilities,
            "experience_level": experience_level,
            "raw_text": jd_text
        }
    
    def _extract_role_title(self, lines: List[str]) -> str:
        """Extract role title from JD lines."""
        role_keywords = ["role", "position", "job title", "title"]
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in role_keywords):
                if i + 1 < len(lines):
                    return lines[i + 1]
        # Fallback: return first line if it looks like a title
        if lines and len(lines[0]) < 100:
            return lines[0]
        return "Unknown Role"
    
    def _extract_jd_skills(self, jd_text: str) -> tuple[List[str], List[str]]:
        """Extract required and nice-to-have skills from JD."""
        required = []
        nice_to_have = []
        
        # Look for skills section
        skills_section_match = re.search(
            r"(?:skills|technologies|requirements|qualifications)[:\s]*((?:.|\n)*?)(?:\n\n|\n[A-Z])",
            jd_text,
            re.IGNORECASE
        )
        
        if skills_section_match:
            skills_text = skills_section_match.group(1)
            # Split by common delimiters
            skills = re.split(r"[,\n•\-\*]", skills_text)
            skills = [s.strip() for s in skills if s.strip() and len(s) > 2]
            
            # Separate required vs nice-to-have based on keywords
            nice_keywords = ["plus", "bonus", "preferred", "nice to have", "advantageous"]
            for skill in skills:
                if any(kw in skill.lower() for kw in nice_keywords):
                    nice_to_have.append(skill)
                else:
                    required.append(skill)
        
        return required, nice_to_have
    
    def _extract_responsibilities(self, jd_text: str) -> List[str]:
        """Extract responsibilities from JD."""
        responsibilities = []
        
        # Look for responsibilities section
        resp_section_match = re.search(
            r"(?:responsibilities|duties|what you'll do|role)[:\s]*((?:.|\n)*?)(?:\n\n|\n[A-Z])",
            jd_text,
            re.IGNORECASE
        )
        
        if resp_section_match:
            resp_text = resp_section_match.group(1)
            # Split by bullet points or numbered lists
            items = re.split(r"[\n•\-\*]\d*\.?\s*", resp_text)
            responsibilities = [r.strip() for r in items if r.strip() and len(r) > 10]
        
        return responsibilities
    
    def _extract_experience_level(self, jd_text: str) -> str:
        """Extract experience level from JD."""
        # Look for years of experience
        exp_match = re.search(r"(\d+)\+?\s*years?\s*(?:of\s*)?experience", jd_text, re.IGNORECASE)
        if exp_match:
            years = int(exp_match.group(1))
            if years < 2:
                return "Entry Level"
            elif years < 5:
                return "Mid Level"
            elif years < 8:
                return "Senior Level"
            else:
                return "Lead/Principal"
        
        # Look for level keywords
        level_keywords = ["intern", "junior", "mid", "senior", "lead", "principal", "director"]
        for level in level_keywords:
            if level in jd_text.lower():
                return level.title() + " Level"
        
        return "Not Specified"
    
    def extract_resume_info(self, resume_text: str) -> Dict:
        """
        Extract structured information from resume.
        
        Args:
            resume_text: Raw text from resume PDF
            
        Returns:
            Dictionary with name, skills, experience, etc.
        """
        lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
        
        # Extract candidate name (usually first line)
        name = self._extract_name(lines, resume_text)
        
        # Extract skills
        skills = self._extract_resume_skills(resume_text)
        
        # Extract experience/projects
        experience = self._extract_experience(resume_text)
        projects = self._extract_projects(resume_text)
        
        # Extract education
        education = self._extract_education(resume_text)
        
        # Estimate years of experience
        years_exp = self._estimate_experience(experience, resume_text)
        
        return {
            "name": name,
            "skills": skills,
            "experience": experience,
            "projects": projects,
            "education": education,
            "years_of_experience": years_exp,
            "raw_text": resume_text
        }
    
    def _extract_name(self, lines: List[str], full_text: str) -> str:
        """Extract candidate name from resume."""
        if not lines:
            return "Unknown"
        
        # First line is often the name
        first_line = lines[0]
        # Check if it looks like a name (no numbers, reasonable length)
        if re.match(r"^[A-Za-z\s\-\.]+$", first_line) and len(first_line) < 50:
            return first_line
        
        # Try to find email and extract name from it
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_text)
        if email_match:
            email = email_match.group(0)
            name_part = email.split("@")[0]
            # Convert to title case
            name = " ".join(word.capitalize() for word in name_part.split("."))
            if len(name) < 50:
                return name
        
        return "Unknown Candidate"
    
    def _extract_resume_skills(self, resume_text: str) -> List[str]:
        """Extract skills from resume."""
        skills = []
        
        # Look for skills section
        for pattern_list in self.section_patterns["skills"]:
            for pattern in pattern_list:
                match = re.search(
                    rf"{pattern.pattern}[:\s]*((?:.|\n)*?)(?:\n\n|\n[A-Z]{{3,}})",
                    resume_text,
                    re.IGNORECASE
                )
                if match:
                    skills_text = match.group(1)
                    # Split by common delimiters
                    items = re.split(r"[,\n•\-\*]", skills_text)
                    skills.extend([s.strip() for s in items if s.strip() and len(s) > 2])
                    break
        
        # If no skills section found, try to find skill-like words throughout
        if not skills:
            # Common tech keywords
            tech_keywords = [
                "python", "java", "javascript", "react", "node", "angular", "vue",
                "sql", "mongodb", "postgresql", "aws", "docker", "kubernetes",
                "git", "agile", "scrum", "machine learning", "ai", "data science"
            ]
            for keyword in tech_keywords:
                if keyword.lower() in resume_text.lower():
                    skills.append(keyword)
        
        return list(set(skills))  # Remove duplicates
    
    def _extract_experience(self, resume_text: str) -> List[str]:
        """Extract work experience descriptions."""
        experience = []
        
        for pattern_list in self.section_patterns["experience"]:
            for pattern in pattern_list:
                match = re.search(
                    rf"{pattern.pattern}[:\s]*((?:.|\n)*?)(?:\n\n|\n[A-Z]{{3,}})",
                    resume_text,
                    re.IGNORECASE
                )
                if match:
                    exp_text = match.group(1)
                    # Split by bullet points
                    items = re.split(r"[\n•\-\*]\d*\.?\s*", exp_text)
                    experience.extend([e.strip() for e in items if e.strip() and len(e) > 15])
                    break
        
        return experience
    
    def _extract_projects(self, resume_text: str) -> List[str]:
        """Extract project descriptions."""
        projects = []
        
        for pattern_list in self.section_patterns["projects"]:
            for pattern in pattern_list:
                match = re.search(
                    rf"{pattern.pattern}[:\s]*((?:.|\n)*?)(?:\n\n|\n[A-Z]{{3,}})",
                    resume_text,
                    re.IGNORECASE
                )
                if match:
                    proj_text = match.group(1)
                    # Split by bullet points
                    items = re.split(r"[\n•\-\*]\d*\.?\s*", proj_text)
                    projects.extend([p.strip() for p in items if p.strip() and len(p) > 15])
                    break
        
        return projects
    
    def _extract_education(self, resume_text: str) -> List[str]:
        """Extract education information."""
        education = []
        
        for pattern_list in self.section_patterns["education"]:
            for pattern in pattern_list:
                match = re.search(
                    rf"{pattern.pattern}[:\s]*((?:.|\n)*?)(?:\n\n|\n[A-Z]{{3,}})",
                    resume_text,
                    re.IGNORECASE
                )
                if match:
                    edu_text = match.group(1)
                    # Split by newlines
                    items = edu_text.split("\n")
                    education.extend([e.strip() for e in items if e.strip() and len(e) > 10])
                    break
        
        return education
    
    def _estimate_experience(self, experience: List[str], full_text: str) -> int:
        """Estimate years of experience."""
        # Try to find explicit years mentioned
        exp_match = re.search(r"(\d+)\+?\s*years?\s*(?:of\s*)?experience", full_text, re.IGNORECASE)
        if exp_match:
            return int(exp_match.group(1))
        
        # Estimate from number of experience entries
        if experience:
            # Rough estimate: each job ~2-3 years
            return min(len(experience) * 2, 15)
        
        return 0
