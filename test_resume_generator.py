import os
from dotenv import load_dotenv
from src.resume_generator.openai_generator import OpenAIResumeGenerator
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TestResumeGenerator')

def test_openai_generator():
    """Test OpenAI resume generation components"""
    print("\nTesting OpenAI Resume Generator...")
    print("=" * 50)
    
    try:
        print("\n1. Initializing OpenAI Resume Generator...")
        generator = OpenAIResumeGenerator()
        
        # Sample job description for testing
        job_description = """
        Senior Full Stack Developer
        
        We're looking for a Senior Full Stack Developer to join our growing team. The ideal candidate will have:
        
        - 3+ years of experience with React, TypeScript, and Node.js
        - Strong experience with Python and modern web frameworks like Django
        - Experience with mobile development using React Native
        - Familiarity with cloud services and containerization
        - Strong communication skills and experience working in Agile teams
        - Experience with test-driven development and automated testing
        - Background in developing scalable web applications
        - Experience mentoring junior developers
        
        You'll be responsible for:
        - Developing and maintaining our core web and mobile applications
        - Writing clean, maintainable code with proper documentation
        - Collaborating with product managers and designers
        - Contributing to technical architecture decisions
        - Mentoring junior team members
        - Participating in code reviews and agile ceremonies
        
        We offer:
        - Competitive salary
        - Remote work options
        - Health benefits
        - Professional development opportunities
        """
        
        print("\n2. Testing summary generation...")
        summary = generator._generate_summary(job_description)
        print(f"Generated Summary:\n{summary}\n")
        
        print("\n3. Testing skills section generation...")
        skills = generator._generate_skills_section(job_description)
        print(f"Generated Skills:\n{skills}\n")
        
        print("\n4. Testing experience bullet points generation...")
        # Get first experience item from resume data
        first_experience = generator.resume_data["experience"][0]
        bullets = generator._generate_experience_bullets(job_description, first_experience)
        print(f"Generated Experience Bullets for {first_experience['title']} at {first_experience['company']}:")
        for bullet in bullets:
            print(f"• {bullet}")
        
        print("\n5. Testing complete resume generation...")
        tailored_resume = generator.generate_tailored_resume(job_description)
        
        if tailored_resume:
            print("✓ Successfully generated complete tailored resume")
            # Save the tailored resume for inspection
            output_path = "generated_resumes/test_tailored_resume.json"
            os.makedirs("generated_resumes", exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(tailored_resume, f, indent=2)
            print(f"  Saved tailored resume to: {output_path}")
            
            # Print the results
            print("\n=== Tailored Resume Generated ===\n")
            
            print("=== Summary ===")
            print(tailored_resume["summary"])
            print("\n=== Skills ===")
            print(tailored_resume["skills"])
            print("\n=== Experience (First Role) ===")
            for bullet in tailored_resume["experience"][0]["description"]:
                print(f"• {bullet}")
        else:
            print("✗ Failed to generate complete tailored resume")
            
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    load_dotenv()
    test_openai_generator() 