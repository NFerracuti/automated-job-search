import json
import logging
from src.document_creator.docx_generator import DocxResumeGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fixed_sections():
    """Test the fixed docx generator with hardcoded sections"""
    logger.info("Testing fixed document generator")
    
    # Create a generator
    generator = DocxResumeGenerator()
    
    # Create tailored resume with skills
    tailored_resume = {
        "summary": "Experienced developer with a focus on web and mobile technologies.",
        "skills": "Python, JavaScript, React, HTML5, CSS3, Node.js, Git"
    }
    
    # Generate resume
    document_path = generator.generate_resume_file(tailored_resume)
    
    logger.info(f"Document created at: {document_path}")
    logger.info("Please check for:")
    logger.info("1. Skills section with correct content")
    logger.info("2. Job descriptions with 9pt font")

if __name__ == "__main__":
    test_fixed_sections() 