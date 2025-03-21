import os
import json
import logging
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('OpenAIGenerator')

class OpenAIResumeGenerator:
    """Class to generate tailored resume content using OpenAI"""
    
    def __init__(self, resume_data_path='assets/resume_data.json'):
        """Initialize the generator with resume data and OpenAI client"""
        load_dotenv()
        
        # Load resume data
        try:
            with open(resume_data_path, 'r') as f:
                self.resume_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading resume data: {str(e)}")
            raise
        
        # Initialize OpenAI client
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OpenAI API key not found in environment variables")
            
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4"  # or "gpt-3.5-turbo" for faster, cheaper results
            self.temperature = 0.7
            self.max_tokens = 1000
            
            logger.info("OpenAI Resume Generator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise
    
    def generate_tailored_resume(self, job_description):
        """Generate a complete tailored resume based on the job description"""
        try:
            tailored_resume = self.resume_data.copy()
            
            # Generate tailored sections
            tailored_resume["summary"] = self._generate_summary(job_description)
            tailored_resume["skills"] = self._generate_skills_section(job_description)
            
            # Tailor experience bullet points
            for i, exp in enumerate(tailored_resume["experience"]):
                tailored_resume["experience"][i]["description"] = self._generate_experience_bullets(job_description, exp)
            
            logger.info("Generated complete tailored resume")
            return tailored_resume
            
        except Exception as e:
            logger.error(f"Error generating tailored resume: {str(e)}")
            return self.resume_data
    
    def _generate_summary(self, job_description):
        """Generate a tailored professional summary"""
        try:
            original_summary = self.resume_data["summary"]
            
            prompt = f"""
            Job Description:
            {job_description}
            
            My Original Professional Summary:
            {original_summary}
            
            As an AI assistant specializing in resume optimization:
            1. Analyze the job description for key requirements, technologies, and desired qualities
            2. Identify overlapping areas between my experience and the job requirements
            3. Rewrite my professional summary to:
               - Emphasize relevant experience in tech (ad-tech, health-tech, entrepreneurship)
               - Highlight matching technical skills and methodologies
               - Maintain my focus on practical solutions and communication
               - Include specific keywords from the job description
               - Keep it to 2-3 impactful sentences
            
            Return ONLY the new summary, optimized for both ATS systems and human readers.
            """
            
            response = self.client.chat.completions.create(
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
            return self.resume_data["summary"]
    
    def _generate_skills_section(self, job_description):
        """Generate a tailored skills section based on the job description"""
        try:
            # Prepare skills by category
            skills_by_category = []
            standalone_skills = []
            
            # Separate standalone skills (Git and Scrum) from categorized skills
            for category, skills in self.resume_data["skills"].items():
                if category.lower() in ['git', 'scrum']:
                    standalone_skills.extend(skills)
                else:
                    category_name = category.replace('_', ' ').title()
                    skills_text = ', '.join(skills)
                    skills_by_category.append(f"{category_name}:\n{skills_text}")
            
            prompt = f"""
            Job Description:
            {job_description}
            
            My Current Skills Structure:
            {'\n\n'.join(skills_by_category)}
            
            Standalone Skills:
            {', '.join(standalone_skills)}
            
            As an AI assistant specializing in resume optimization:
            1. IMPORTANT: DO NOT REMOVE ANY EXISTING SKILLS
            2. Analyze the job description for additional required technical skills that are not in my current skill set
            3. Add only the missing skills that are explicitly mentioned in the job description
            4. Place new skills in their appropriate categories, maintaining the existing structure
            5. Keep Git and Scrum as standalone skills (not in categories)
            
            Return the skills in this EXACT format (including newlines):
            Programming Languages:
            [skills list]
            
            Git
            
            Databases:
            [skills list]
            
            Frameworks, libraries, environments:
            [skills list]
            
            Testing Frameworks:
            [skills list]
            
            Software:
            [skills list]
            
            Scrum
            
            IMPORTANT: 
            - Maintain all existing skills in each category
            - Only add new skills that are explicitly mentioned in the job description
            - Keep the exact category names and format
            - Keep Git and Scrum as standalone entries
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=self.max_tokens
            )
            
            skills = response.choices[0].message.content.strip()
            logger.info("Generated tailored skills section")
            return skills
            
        except Exception as e:
            logger.error(f"Error generating skills section: {str(e)}")
            # Return original skills structure as fallback
            return self._format_original_skills()
    
    def _format_original_skills(self):
        """Format original skills in the desired structure as a fallback"""
        formatted_skills = []
        for category, skills in self.resume_data["skills"].items():
            if category.lower() in ['git', 'scrum']:
                formatted_skills.append(category.title())
            else:
                category_name = category.replace('_', ' ').title()
                skills_text = ', '.join(skills)
                formatted_skills.append(f"{category_name}:\n{skills_text}")
        return '\n\n'.join(formatted_skills)
    
    def _generate_experience_bullets(self, job_description, experience_item):
        """Generate tailored experience bullet points for a specific role"""
        try:
            original_bullets = experience_item["description"]
            technologies = experience_item.get("technologies", [])
            
            prompt = f"""
            Job Description:
            {job_description}
            
            My Experience at {experience_item['company']} as {experience_item['title']}:
            {' '.join(original_bullets)}
            
            Technologies Used: {', '.join(technologies) if technologies else 'Not specified'}
            
            As an AI assistant specializing in resume optimization:
            1. Analyze the job description for:
               - Key responsibilities
               - Required technical skills
               - Desired soft skills
               - Industry-specific keywords
            
            2. Rewrite my experience bullets to:
               - Focus on achievements and impacts
               - Include specific metrics where available
               - Use strong action verbs
               - Incorporate relevant keywords from the job description
               - Highlight technical skills that match the requirements
               - Demonstrate leadership and collaboration abilities
            
            Return EXACTLY 4 bullet points, each on a new line.
            Each bullet should:
            - Start with an action verb
            - Be concise but specific
            - Include metrics where available
            - Incorporate relevant keywords
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            bullets = response.choices[0].message.content.strip().split('\n')
            cleaned_bullets = [bullet.strip().lstrip('•-*').strip() for bullet in bullets if bullet.strip()]
            
            logger.info(f"Generated tailored experience bullets for {experience_item['title']} at {experience_item['company']}")
            return cleaned_bullets
            
        except Exception as e:
            logger.error(f"Error generating experience bullets: {str(e)}")
            return experience_item["description"]

# Add necessary import that was missed
from datetime import datetime 