import json
import logging
from src.document_creator.docx_generator import DocxResumeGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hardcoded_sections():
    """Test the hardcoded skills and personal info sections"""
    logger.info("Testing hardcoded sections")
    
    # Create a generator
    generator = DocxResumeGenerator()
    
    # Create tailored resume with minimal info
    tailored_resume = {
        "summary": "Experienced developer with a focus on web technologies.",
        "skills": "Python, JavaScript, React, HTML5, CSS3, Node.js"
    }
    
    # Test the generate_resume_file method
    document_path = generator.generate_resume_file(tailored_resume)
    
    logger.info(f"Document created at: {document_path}")
    logger.info("Please check the document for:")
    logger.info("1. Personal info section showing correct details")
    logger.info("2. Skills section properly showing the skills")
    logger.info("3. All formatting looking correct")

if __name__ == "__main__":
    test_hardcoded_sections() 