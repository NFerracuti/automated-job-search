import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_and_display_skills():
    """Extract and display skills from resume_data.json"""
    try:
        # Load the resume data
        with open('assets/resume_data.json', 'r') as f:
            data = json.load(f)
        
        logger.info(f"Resume data contains keys: {data.keys()}")
        
        # Extract skills
        if 'skills' in data:
            skills_data = data['skills']
            logger.info(f"Skills data type: {type(skills_data)}")
            logger.info(f"Skills data: {skills_data}")
            
            # If skills is a dictionary, extract all skills
            if isinstance(skills_data, dict):
                all_skills = []
                for category, skill_list in skills_data.items():
                    logger.info(f"Category: {category}, Skills: {skill_list}")
                    if isinstance(skill_list, list):
                        all_skills.extend(skill_list)
                
                skills_text = ", ".join(all_skills)
                logger.info(f"Extracted skills: {skills_text}")
            else:
                logger.info(f"Skills is not a dictionary: {skills_data}")
        else:
            logger.warning("No 'skills' key in resume data")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    extract_and_display_skills() 