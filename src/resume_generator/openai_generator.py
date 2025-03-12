import os
import json
import logging
from typing import Dict, List, Any

import openai
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('OpenAIGenerator')

class OpenAIResumeGenerator:
    """Class to generate tailored resumes using OpenAI API"""
    
    def __init__(self, config_path='config.json', resume_data_path=None):
        # Load config
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Load API key
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY not set in .env file")
        
        # Load resume data
        self.resume_data_path = resume_data_path or os.getenv('RESUME_DATA_PATH', 'assets/resume_data.json')
        with open(self.resume_data_path, 'r') as f:
            self.resume_data = json.load(f)
        
        # OpenAI config
        self.model = self.config["openai"]["model"]
        self.temperature = self.config["openai"]["temperature"]
        self.max_tokens = self.config["openai"]["max_tokens"]
        
        logger.info("OpenAI Resume Generator initialized")
    
    def _generate_skills_section(self, job_description):
        """Generate a tailored skills section based on the job description"""
        try:
            all_skills = []
            for category, skills in self.resume_data["skills"].items():
                all_skills.extend(skills)
            
            prompt = f"""
            Job Description:
            {job_description}
            
            My Skills:
            {', '.join(all_skills)}
            
            Based on the job description, select and order the most relevant skills from my skill set.
            Focus on exact keyword matches that would be picked up by ATS systems.
            List them in order of relevance to the job description.
            Return ONLY the list of skills, comma-separated, with no other text.
            """
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            skills = response.choices[0].message.content.strip()
            logger.info("Generated tailored skills section")
            return skills
            
        except Exception as e:
            logger.error(f"Error generating skills section: {str(e)}")
            # Fallback to original skills
            return ", ".join([skill for category, skills in self.resume_data["skills"].items() for skill in skills])
    
    def _generate_experience_bullets(self, job_description, experience_item):
        """Generate tailored experience bullet points for a specific role"""
        try:
            original_bullets = experience_item["description"]
            
            prompt = f"""
            Job Description:
            {job_description}
            
            My Experience at {experience_item['company']} as {experience_item['title']}:
            {' '.join(original_bullets)}
            
            Rewrite my experience bullet points to better match this job description.
            Focus on using keywords from the job description and quantifiable achievements.
            Maintain the same general information but emphasize the most relevant experience.
            Return EXACTLY 4 bullet points, and make each one a separate line. 
            Start each bullet point with an action verb.
            Be concise but specific, and include metrics where available.
            """
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            bullets = response.choices[0].message.content.strip().split('\n')
            # Clean up bullets if needed (remove bullet markers if present)
            cleaned_bullets = [bullet.strip().lstrip('•-*').strip() for bullet in bullets if bullet.strip()]
            
            logger.info(f"Generated tailored experience bullets for {experience_item['title']} at {experience_item['company']}")
            return cleaned_bullets
            
        except Exception as e:
            logger.error(f"Error generating experience bullets: {str(e)}")
            # Fallback to original bullets
            return experience_item["description"]
    
    def _generate_summary(self, job_description):
        """Generate a tailored professional summary"""
        try:
            original_summary = self.resume_data["summary"]
            
            prompt = f"""
            Job Description:
            {job_description}
            
            My Original Professional Summary:
            {original_summary}
            
            Rewrite my professional summary to better match this job description.
            Use relevant keywords that would be picked up by ATS systems.
            Keep it to 2-3 sentences maximum and focus on my most relevant skills and experience.
            Be professional but conversational in tone.
            Return ONLY the new summary with no other text.
            """
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info("Generated tailored professional summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback to original summary
            return self.resume_data["summary"]
    
    def generate_tailored_resume(self, job_description, job_title, company):
        """Generate a complete tailored resume for a job"""
        try:
            # Get tailored components
            tailored_summary = self._generate_summary(job_description)
            tailored_skills = self._generate_skills_section(job_description)
            
            # Process experience
            tailored_experience = []
            for exp in self.resume_data["experience"]:
                tailored_bullets = self._generate_experience_bullets(job_description, exp)
                tailored_exp = exp.copy()
                tailored_exp["description"] = tailored_bullets
                tailored_experience.append(tailored_exp)
            
            # Create complete tailored resume data
            tailored_resume = {
                "personal_info": self.resume_data["personal_info"],
                "summary": tailored_summary,
                "skills": tailored_skills.split(", "),
                "experience": tailored_experience,
                "education": self.resume_data["education"],
                "projects": self.resume_data["projects"],
                "certifications": self.resume_data.get("certifications", [])
            }
            
            # Add metadata about the job
            tailored_resume["metadata"] = {
                "job_title": job_title,
                "company": company,
                "tailored": True,
                "generation_date": datetime.now().isoformat()
            }
            
            logger.info(f"Generated complete tailored resume for {job_title} at {company}")
            return tailored_resume
            
        except Exception as e:
            logger.error(f"Error generating tailored resume: {str(e)}")
            # Return the original resume data as fallback
            self.resume_data["metadata"] = {
                "job_title": job_title,
                "company": company,
                "tailored": False
            }
            return self.resume_data

# Add necessary import that was missed
from datetime import datetime 