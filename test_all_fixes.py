import json
import logging
from src.document_creator.docx_generator import DocxResumeGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_all_fixes():
    """Test all our fixes in one go"""
    logger.info("Testing all fixes")
    
    # Create a generator
    generator = DocxResumeGenerator()
    
    # Create sample tailored resume (what OpenAI would return)
    tailored_resume = {
        "summary": "Experienced developer with a strong background in Python and JavaScript development.",
        "skills": "Python, JavaScript, React, HTML5, CSS3, Node.js, Git",
        "experience": []  # We don't need to set this as it uses the original experience
    }
    
    # Test the generate_resume_file method directly
    document_path = generator.generate_resume_file(tailored_resume)
    
    logger.info(f"Document created at: {document_path}")
    logger.info("Please check the document for:")
    logger.info("1. Skills section properly shows the skills")
    logger.info("2. Job description bullets use 9pt font")

if __name__ == "__main__":
    test_all_fixes() 