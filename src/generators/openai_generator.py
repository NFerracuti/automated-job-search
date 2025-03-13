import os
import logging
from openai import OpenAI
import types

class OpenAIResumeGenerator:
    def __init__(self, resume_data):
        self.resume_data = resume_data
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # Update model to GPT-4o
        self.model = "gpt-4o"  # Previously was likely "gpt-3.5-turbo" or "gpt-4"
        self.client = OpenAI(api_key=self.openai_api_key)
        self.logger = logging.getLogger(__name__)
        
    def _get_completion(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model=self.model,  # Using the newer model defined above
                messages=[
                    {"role": "system", "content": "You are a professional resume writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error getting completion: {str(e)}")
            return None

    def _get_skills_prompt(self, job_description, current_skills):
        return f"""You are a professional resume writer helping tailor a resume for a specific job.

Current skills section: {current_skills}

Job Description: {job_description}

Your task is to create a tailored skills section.
IMPORTANT: Always return a list of skills - never leave this empty.
Keep ALL existing skills that are relevant. You may add 2-3 additional relevant skills from the job description if they're genuinely part of the candidate's skillset.

Format as a simple comma-separated list.
Be extremely concise - use only the skill name without explanation.
Use clear, standard terminology without buzzwords.
Prioritize technical skills and frameworks mentioned in the job posting.
Keep the original skills order where possible.

Return only the comma-separated list, nothing else."""

    def _get_experience_bullet_prompt(self, job_description, role_info):
        return f"""You are a professional resume writer helping tailor job experience bullets for a specific role.

Original role details:
{role_info}

Target job description:
{job_description}

Rewrite the experience points to:
1. Be extremely concise and direct - limit each bullet to a single line when possible
2. NEVER use the same action verb more than once across ALL bullets
3. AVOID ALL corporate buzzwords and fluff (no "spearheaded", "leveraged", "utilized", "facilitated", etc.)
4. Use straightforward, simple language that directly states what was done
5. Focus on concrete achievements and technical details
6. Include relevant keywords from the job description naturally
7. Start with varied, strong action verbs but keep them simple (e.g., "developed", "built", "created", "improved")
8. Include specific metrics where available
9. Keep to 3-4 bullet points maximum

Format each point as a clear, single-line bullet point.
Return only the bullet points, one per line."""

    def _get_summary_prompt(self, job_description, current_summary):
        return f"""You are a professional resume writer helping tailor a professional summary.

Current summary: {current_summary}

Job Description: {job_description}

Write a brief professional summary that:
1. Is 2-3 sentences MAXIMUM - brevity is critical
2. Uses clear, direct language without any buzzwords
3. Contains zero fluff or generalizations
4. Highlights only the most relevant skills and experience for this specific role
5. Naturally incorporates key terms from the job description
6. Maintains the candidate's original expertise level and core focus

Return only the summary paragraph, nothing else."""

    def generate_tailored_resume(self, job_title, company_name, job_description):
        """Generate a tailored resume based on the job description"""
        self.logger.info("DIAGNOSTICS - Starting generate_tailored_resume")
        
        # Log the entire resume_data structure to see what we're working with
        self.logger.info(f"DIAGNOSTICS - Resume data contains keys: {self.resume_data.keys()}")
        self.logger.info(f"DIAGNOSTICS - Skills value in resume_data: {self.resume_data.get('skills', 'NOT FOUND')} (type: {type(self.resume_data.get('skills', ''))})")
        
        # Extract skills
        if "skills" in self.resume_data and isinstance(self.resume_data["skills"], list):
            current_skills = ", ".join(self.resume_data["skills"])
            self.logger.info(f"DIAGNOSTICS - Skills from list: {current_skills}")
        elif "skills" in self.resume_data and isinstance(self.resume_data["skills"], str):
            current_skills = self.resume_data["skills"]
            self.logger.info(f"DIAGNOSTICS - Skills as string: {current_skills}")
        else:
            # Fallback
            current_skills = "HTML, CSS, JavaScript, Python, React, Node.js, SQL"
            self.logger.info(f"DIAGNOSTICS - Using fallback skills: {current_skills}")
        
        # Log the actual prompt
        tailored_skills_prompt = self._get_skills_prompt(job_description, current_skills)
        self.logger.info(f"DIAGNOSTICS - Skills prompt to OpenAI: <<<{tailored_skills_prompt}>>>")
        
        # Get and log the response
        tailored_skills = self._get_completion(tailored_skills_prompt)
        self.logger.info(f"DIAGNOSTICS - Raw skills response from OpenAI: <<<{tailored_skills}>>>")
        
        # Make sure we're returning a valid skills value
        if not tailored_skills or tailored_skills.strip() == "":
            tailored_skills = current_skills
            self.logger.warning("No skills returned from OpenAI, using original skills")
        
        result = {
            "summary": tailored_summary,
            "skills": tailored_skills,
            "experience": tailored_experience_list
        }
        
        self.logger.info(f"DIAGNOSTICS - Final result from generate_tailored_resume: {result}")
        self.logger.info(f"DIAGNOSTICS - Skills in final result: <<<{result.get('skills', 'NOT FOUND')}>>>")
        
        return result 