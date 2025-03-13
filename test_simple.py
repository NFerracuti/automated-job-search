import logging
from src.document_creator.docx_generator import DocxResumeGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_resume():
    """Test with hard-coded values for maximum reliability"""
    # Create a generator
    generator = DocxResumeGenerator()
    
    # Create minimal resume data
    resume_data = {
        "personal_info": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "location": "New York, NY"
        },
        "summary": "Experienced developer with strong technical skills.",
        # Explicit skills string
        "skills": "Python, JavaScript, HTML, CSS, React, Node.js",
        "experience": [
            {
                "company": "Example Corp",
                "title": "Software Developer",
                "startDate": "Jan 2020",
                "endDate": "Present",
                "description": [
                    "Developed web applications with React and Node.js",
                    "Implemented responsive design for mobile compatibility"
                ]
            }
        ],
        "education": [
            {
                "institution": "Example University",
                "area": "Computer Science",
                "studyType": "Bachelor",
                "startDate": "2016",
                "endDate": "2020"
            }
        ]
    }
    
    # Create document directly
    document_path = generator.create_resume(resume_data)
    
    logger.info(f"Document created at: {document_path}")
    logger.info("Please check the document for:")
    logger.info("1. Personal info section")
    logger.info("2. Skills section with: 'Python, JavaScript, HTML, CSS, React, Node.js'")
    logger.info("3. Experience bullets with 9pt font")

if __name__ == "__main__":
    test_simple_resume() 