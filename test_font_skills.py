import os
import logging
from src.document_creator.docx_generator import DocxResumeGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_document():
    """Test document creation with explicit skills and font sizes"""
    # Create test resume data with explicit skills
    test_data = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "123-456-7890",
        "summary": "Experienced developer with strong skills",
        # Explicitly set skills
        "skills": "Python, Javascript, HTML, CSS, React, Node.js",
        "experience": [
            {
                "company": "Test Company",
                "title": "Developer",
                "startDate": "Jan 2020",
                "endDate": "Present",
                "description": [
                    "Developed user interfaces and responsive web applications", 
                    "Created backend APIs and integrations with third-party services",
                    "Implemented CI/CD pipelines for automated deployment"
                ]
            }
        ],
        "education": [
            {
                "institution": "Test University",
                "area": "Computer Science",
                "studyType": "Bachelor",
                "startDate": "2016",
                "endDate": "2020"
            }
        ]
    }
    
    # Generate document
    generator = DocxResumeGenerator()
    output_path = generator.create_resume(
        resume_data=test_data,
        metadata={"job_title": "Test Job", "company_name": "Test Company"}
    )
    
    logger.info(f"Test document created at: {output_path}")
    logger.info(f"Please check that:")
    logger.info(f"1. Skills section shows: '{test_data['skills']}'")
    logger.info(f"2. Job description bullets use 9pt font")

if __name__ == "__main__":
    test_direct_document() 