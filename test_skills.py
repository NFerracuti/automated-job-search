import json
import logging
from src.document_creator.docx_generator import DocxResumeGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_skills_section():
    """Test creating a resume with skills section only"""
    try:
        # Load resume data
        with open('assets/resume_data.json', 'r') as f:
            resume_data = json.load(f)
        
        logger.info(f"Resume data loaded with keys: {resume_data.keys()}")
        logger.info(f"Skills in resume data: {resume_data.get('skills', 'NOT FOUND')}")
        
        # Force some skills value
        resume_data['skills'] = "Python, JavaScript, React, HTML, CSS, Node.js"
        logger.info(f"Set skills to: {resume_data['skills']}")
        
        # Create document
        generator = DocxResumeGenerator()
        output_path = generator.create_resume(
            resume_data=resume_data,
            metadata={"job_title": "Test Job", "company_name": "Test Company"}
        )
        
        logger.info(f"Document created at: {output_path}")
        logger.info("Check the document to see if skills are displayed correctly")
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")

if __name__ == "__main__":
    test_skills_section() 