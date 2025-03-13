import json

def load_resume_data():
    try:
        with open('assets/resume_data.json', 'r') as f:
            data = json.load(f)
            logger.info(f"DIAGNOSTICS - Resume data loaded, contains keys: {data.keys()}")
            logger.info(f"DIAGNOSTICS - Skills in resume_data: {data.get('skills', 'NOT FOUND')}")
            return data
    except Exception as e:
        logger.error(f"DIAGNOSTICS - Error loading resume data: {str(e)}")
        return {}

# Replace your existing resume_data loading with this function
resume_data = load_resume_data()

def process_job(job):
    # ... existing code ...
    
    # Generate tailored resume
    logger.info("DIAGNOSTICS - Calling OpenAI generator")
    tailored_resume = openai_generator.generate_tailored_resume(
        job_title=job.get('title', ''),
        company_name=job.get('company', {}).get('display_name', ''),
        job_description=job.get('description', '')
    )
    
    logger.info(f"DIAGNOSTICS - Received tailored resume: {tailored_resume}")
    logger.info(f"DIAGNOSTICS - Skills in tailored resume: <<<{tailored_resume.get('skills', 'NOT FOUND')}>>>")
    
    # Create a copy of resume_data to modify
    resume_data_copy = resume_data.copy()
    
    # Explicitly set the skills
    skills_value = tailored_resume.get('skills')
    logger.info(f"DIAGNOSTICS - Skills value to be added to resume: <<<{skills_value}>>>")
    
    if skills_value:
        resume_data_copy['skills'] = skills_value
        logger.info(f"DIAGNOSTICS - Set skills in resume_data_copy: <<<{resume_data_copy.get('skills', 'NOT SET')}>>>")
    else:
        logger.warning("DIAGNOSTICS - No skills found in tailored resume!")
    
    # Log the final data being sent to the document generator
    logger.info(f"DIAGNOSTICS - Resume data for document generator: {resume_data_copy}")
    logger.info(f"DIAGNOSTICS - Skills in resume data for document generator: <<<{resume_data_copy.get('skills', 'NOT FOUND')}>>>")
    
    # Generate document
    docx_generator = DocxResumeGenerator()
    document_path = docx_generator.create_resume(
        resume_data=resume_data_copy,
        metadata={
            "job_title": job.get('title', ''),
            "company_name": job.get('company', {}).get('display_name', '')
        }
    )
    
    # ... rest of the code ... 