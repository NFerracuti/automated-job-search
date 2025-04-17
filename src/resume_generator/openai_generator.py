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
            
            prompt = f"""You are a resume skills optimizer. Your task is to analyze the job description and optimize the skills section of the resume.

Job Description:
{job_description}

Current Skills:
{'\n\n'.join(skills_by_category)}

Standalone Skills:
{', '.join(standalone_skills)}

Instructions:
1. Keep all existing skills that are relevant to the job
2. Add any missing skills from the job description that are relevant
3. Format the response EXACTLY as shown below, with ONLY the skills section (no explanatory text)
4. Category titles should be bold (using **), but the skills themselves should be regular text
5. Start with "Programming Languages" and end with "Scrum"

Example format:
**Programming Languages**
Javascript, Typescript, Python, YAML, HTML5, CSS

**Git**

**Databases**
SQL, Postgres, MySQL

**Frameworks And Libraries**
React, Next.js, Expo, React Native, Django

**Testing**
Jest, Mocha, Chai, Maestro

**Software**
Sheets, Jira, Asana, Trello, Miro, Figma

**Scrum**

Return ONLY the skills section in this exact format, with no additional text or context."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for more consistent formatting
                max_tokens=self.max_tokens
            )
            
            skills = response.choices[0].message.content.strip()
            
            # Extract only the skills section
            if "Programming Languages" in skills and "Scrum" in skills:
                start_idx = skills.find("Programming Languages")
                end_idx = skills.find("Scrum") + len("Scrum")
                skills_section = skills[start_idx:end_idx]
                
                # Process the skills section line by line
                lines = skills_section.split('\n')
                formatted_lines = []
                current_category = None
                
                for line in lines:
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                        
                    # Remove any existing bold formatting
                    line = line.replace('**', '')
                    
                    # If this line doesn't contain commas, it's a category or standalone skill
                    if ',' not in line:
                        # Check if it's a standalone skill
                        if line.lower() in ['git', 'aws', 'scrum', 'microservices architecture']:
                            if formatted_lines:  # Add spacing before standalone skill
                                formatted_lines.append('')
                            formatted_lines.append(line)
                        else:
                            # It's a category
                            if formatted_lines:  # Add spacing before new category
                                formatted_lines.append('')
                            formatted_lines.append(line)
                    else:
                        # This is a skills line
                        formatted_lines.append(line)
                
                # Remove trailing empty lines
                while formatted_lines and not formatted_lines[-1]:
                    formatted_lines.pop()
                
                skills_section = '\n'.join(formatted_lines)
                logger.info("Generated tailored skills section")
                return skills_section
            
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