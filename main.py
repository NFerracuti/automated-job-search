#!/usr/bin/env python3
"""
Automated Job Application Workflow

This script automates the job application process by:
1. Scraping job boards for relevant positions
2. Storing job listings in Google Sheets
3. Customizing resumes using OpenAI
4. Generating tailored resume documents
5. Tracking application status and details

Quick Test Mode:
Set QUICK_TEST=true in your environment to stop after finding 1 job per board (default: true)
Set QUICK_TEST=false to scrape all jobs up to max_results_per_board
"""

import os
import json
import time
import argparse
import logging
from datetime import datetime

from dotenv import load_dotenv

# Import components
from src.scrapers import AdzunaScraper, ReedScraper
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.utils.google_sheets import GoogleSheetsManager
from src.resume_generator.openai_generator import OpenAIResumeGenerator
from src.document_creator.docx_generator import DocxResumeGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("job_application.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutomatedJobSearch')

def scrape_jobs(args):
    """Scrape jobs from configured job boards"""
    logger.info("Starting job scraping...")
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    job_boards = config["job_search"]["job_boards"]
    jobs = []
    
    # LinkedIn
    if job_boards.get("linkedin"):
        logger.info("Scraping LinkedIn jobs...")
        linkedin_scraper = LinkedInScraper(config=config, headless=not args.show_browser)
        linkedin_jobs = linkedin_scraper.run()
        if linkedin_jobs:
            with open(linkedin_jobs, 'r') as f:
                jobs.extend(json.load(f))
    
    # Adzuna
    if job_boards.get("adzuna"):
        logger.info("Scraping Adzuna jobs...")
        adzuna_scraper = AdzunaScraper(config=config)
        adzuna_jobs = adzuna_scraper.run()
        if adzuna_jobs:
            with open(adzuna_jobs, 'r') as f:
                jobs.extend(json.load(f))
    
    # Reed
    if job_boards.get("reed"):
        logger.info("Scraping Reed jobs...")
        reed_scraper = ReedScraper(config=config)
        reed_jobs = reed_scraper.run()
        if reed_jobs:
            with open(reed_jobs, 'r') as f:
                jobs.extend(json.load(f))
    
    logger.info(f"Found {len(jobs)} jobs across all platforms")
    
    # Save combined results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_file = f"jobs_combined_{timestamp}.json"
    with open(combined_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    logger.info(f"Saved combined results to {combined_file}")
    
    # Add to Google Sheets
    if not args.skip_sheets:
        logger.info("Adding jobs to Google Sheets...")
        sheets_manager = GoogleSheetsManager()
        added_jobs = sheets_manager.add_jobs(jobs)
        logger.info(f"Added {len(added_jobs)} new jobs to Google Sheets")
    
    return combined_file

def generate_resumes(args):
    """Generate tailored resumes for jobs"""
    logger.info("Starting resume generation...")
    
    # Get jobs that need resumes
    sheets_manager = GoogleSheetsManager()
    jobs_for_resumes = sheets_manager.get_jobs_for_resume_generation()
    
    if not jobs_for_resumes:
        logger.info("No jobs found that need resume generation")
        return
    
    if args.max_resumes and len(jobs_for_resumes) > args.max_resumes:
        logger.info(f"Limiting resume generation to {args.max_resumes} jobs")
        jobs_for_resumes = jobs_for_resumes[:args.max_resumes]
    
    # Initialize generators
    resume_generator = OpenAIResumeGenerator()
    docx_generator = DocxResumeGenerator()
    
    for job in jobs_for_resumes:
        job_title = job.get('Job Title', '')
        company = job.get('Company', '')
        job_url = job.get('Job URL', '')
        
        if not job_url:
            logger.warning(f"Skipping job without URL: {job_title} at {company}")
            continue
        
        logger.info(f"Generating resume for {job_title} at {company}")
        
        # Get job description
        # This is a simplified approach - for a real implementation, you would
        # need to scrape the job description from the URL or have it in your database
        job_description = "Please enter a method to extract the job description from the URL here"
        if args.debug:
            # In debug mode, use a placeholder description
            job_description = f"This is a job for a {job_title} at {company}. The ideal candidate has experience with Python, JavaScript, and web development."
        
        # Generate tailored resume data
        tailored_resume = resume_generator.generate_tailored_resume(
            job_description=job_description,
            job_title=job_title,
            company=company
        )
        
        # Generate resume document
        resume_file = docx_generator.generate_resume_file(tailored_resume)
        
        if resume_file:
            # Upload to Google Drive
            resume_url = docx_generator.upload_to_google_drive(resume_file)
            
            if resume_url:
                # Update Google Sheet with resume URL
                sheets_manager.update_job(job_url, {
                    'Custom Resume URL': resume_url
                })
                
                logger.info(f"Resume for {job_title} at {company} generated and uploaded")
            else:
                logger.warning(f"Failed to upload resume for {job_title} at {company}")
        else:
            logger.warning(f"Failed to generate resume for {job_title} at {company}")
        
        # Wait between API calls to avoid rate limiting
        time.sleep(2)
    
    logger.info(f"Resume generation completed for {len(jobs_for_resumes)} jobs")

def setup_google_services():
    """Guide the user through setting up Google services"""
    print("=== Setting up Google Services ===")
    print("To use Google Sheets and Drive, you need to set up a Google Cloud project and create credentials:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project")
    print("3. Enable the Google Sheets API and Google Drive API")
    print("4. Create a service account")
    print("5. Download the JSON credentials file")
    print("6. Set the path to this file in your .env file as GOOGLE_APPLICATION_CREDENTIALS")
    
    input("Press Enter once you've completed these steps...")
    
    print("\nNow, you need to share your Google Sheet with the service account email:")
    print("1. The email is in the JSON file you downloaded (client_email field)")
    print("2. Create a new Google Sheet or use an existing one")
    print("3. Share the sheet with the service account email, giving it edit access")
    
    input("Press Enter once you've completed these steps...")
    print("\nGoogle services setup complete!")

def setup():
    """Initial setup for the application"""
    print("=== Automated Job Application Workflow Setup ===")
    
    # Create .env file from template if it doesn't exist
    if not os.path.exists(".env"):
        print("Creating .env file from template...")
        with open(".env.example", "r") as template:
            with open(".env", "w") as env_file:
                env_file.write(template.read())
        print(".env file created. Please edit it with your API keys and settings.")
    
    # Set up directories
    os.makedirs("generated_resumes", exist_ok=True)
    os.makedirs("assets", exist_ok=True)
    
    # Guide user through API key setup
    print("\nYou will need the following API keys:")
    print("1. OpenAI API key (https://platform.openai.com/account/api-keys)")
    print("2. Google API credentials (explained in next step)")
    
    input("Press Enter to continue...")
    
    # Guide user through Google services setup
    setup_google_services()
    
    # Remind user to add resume template
    print("\nDon't forget to add your resume template to assets/resume_template.docx")
    print("This template should be a Word document with template fields matching the resume_data.json structure")
    
    print("\nSetup complete! Edit your config.json file to customize job search parameters.")

def load_resume_data():
    """Load resume data from the specified file"""
    resume_data_path = os.getenv('RESUME_DATA_PATH', 'assets/resume_data.json')
    try:
        with open(resume_data_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Resume data loaded from {resume_data_path}")
        
        # Log personal details
        if 'personal_info' in data:
            logger.info(f"Personal info found: Name = {data['personal_info'].get('name', 'NOT FOUND')}")
        else:
            logger.warning("No personal_info section found in resume_data")
        
        # Log skills
        if 'skills' in data:
            if isinstance(data['skills'], dict):
                skill_categories = list(data['skills'].keys())
                sample_skills = []
                for category in list(data['skills'].keys())[:2]:  # Log first two categories
                    if isinstance(data['skills'][category], list):
                        sample_skills.extend(data['skills'][category][:3])  # First three skills
                logger.info(f"Skills found as dictionary with categories: {skill_categories}")
                logger.info(f"Sample skills: {sample_skills}")
            elif isinstance(data['skills'], list):
                logger.info(f"Skills found as list: {data['skills'][:5]}...")  # First five skills
            elif isinstance(data['skills'], str):
                logger.info(f"Skills found as string: {data['skills'][:50]}...")  # First 50 chars
            else:
                logger.warning(f"Skills found but in unexpected format: {type(data['skills'])}")
        else:
            logger.warning("No skills section found in resume_data")
            
        return data
    except Exception as e:
        logger.error(f"Error loading resume data: {str(e)}")
        return {}

def process_job_application(job_data):
    """Process a single job application"""
    try:
        # Load resume data first
        resume_data = load_resume_data()
        
        logger.info(f"Processing job application for: {job_data['title']} at {job_data['company']}")
        
        # 1. Generate tailored resume content using OpenAI
        logger.info("Generating tailored resume content...")
        resume_data_path = os.getenv('RESUME_DATA_PATH', 'assets/resume_data.json')
        openai_generator = OpenAIResumeGenerator(resume_data_path)
        
        # Log before calling OpenAI
        if 'skills' in resume_data:
            if isinstance(resume_data['skills'], dict):
                logger.info(f"Skills being sent to OpenAI: dictionary with {len(resume_data['skills'])} categories")
            else:
                logger.info(f"Skills being sent to OpenAI: {str(resume_data['skills'])[:50]}...")
        else:
            logger.warning("No skills being sent to OpenAI")
        
        # Combine job title, description, and requirements for better context
        full_job_description = f"""
        {job_data['title']}
        
        Company: {job_data['company']}
        Location: {job_data['location']}
        
        Job Description:
        {job_data['description']}
        
        Requirements:
        {job_data.get('requirements', 'Not specified')}
        """
        
        tailored_resume = openai_generator.generate_tailored_resume(full_job_description)
        
        # Log after receiving OpenAI response
        logger.info(f"Tailored resume received from OpenAI with keys: {tailored_resume.keys()}")
        if 'skills' in tailored_resume:
            logger.info(f"Skills returned from OpenAI: {tailored_resume['skills'][:100]}...")
        else:
            logger.warning("No skills returned from OpenAI")
        
        # Add metadata about the job
        tailored_resume["metadata"] = {
            "job_title": job_data["title"],
            "company": job_data["company"],
            "job_id": job_data.get("id", "unknown"),
            "job_url": job_data.get("redirect_url", ""),
            "application_date": datetime.now().isoformat(),
            "tailored": True
        }
        
        # 2. Generate Word document
        logger.info("Generating Word document...")
        doc_generator = DocxResumeGenerator()
        
        # Log before passing to document generator
        logger.info(f"Data being passed to document generator:")
        logger.info(f"  - Summary: {tailored_resume.get('summary', '')[:50]}...")
        logger.info(f"  - Skills: {tailored_resume.get('skills', '')[:100]}...")
        
        # Generate resume file
        doc_path = doc_generator.generate_resume_file(tailored_resume)
        
        if not doc_path:
            raise Exception("Failed to generate resume document")
        
        # 3. Upload to Google Drive
        logger.info("Uploading to Google Drive...")
        drive_url = doc_generator.upload_to_google_drive(doc_path)
        
        if not drive_url:
            raise Exception("Failed to upload resume to Google Drive")
        
        # 4. Update job data with resume information
        job_data.update({
            "resume_path": doc_path,
            "resume_drive_url": drive_url,
            "application_date": datetime.now().isoformat(),
            "status": "Resume Generated"
        })
        
        # 5. Add to Google Sheets
        logger.info("Adding job to Google Sheets...")
        sheets_manager = GoogleSheetsManager()
        
        # Format job data for Google Sheets
        sheet_data = {
            "Job Title": job_data["title"],
            "Company": job_data["company"],
            "Location": job_data["location"],
            "Job Type": "Remote",  # Since we're filtering for remote jobs
            "Salary Range": job_data.get("salary_text", "Not specified"),
            "Job URL": job_data.get("redirect_url", job_data.get("url", "")),
            "Application Status": "Resume Generated",
            "Custom Resume URL": drive_url,
            "Date Added": datetime.now().strftime("%Y-%m-%d"),
            "Job Description": job_data.get("description", "")[:1000],  # Truncate if too long
            "Source": job_data.get("source", "Adzuna"),
            "Notes": f"Resume generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        # Add to Google Sheets
        added_jobs = sheets_manager.add_jobs([sheet_data])
        
        if not added_jobs:
            logger.warning("Failed to add job to Google Sheets")
        else:
            logger.info("Successfully added job to Google Sheets")
            job_data["sheets_status"] = "Added"
        
        logger.info(f"Successfully processed job application. Resume URL: {drive_url}")
        return job_data
        
    except Exception as e:
        logger.error(f"Error processing job application: {str(e)}")
        raise

def main():
    """Main function to run the automated job search process"""
    try:
        load_dotenv()
        logger.info("Starting automated job search process...")
        
        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        all_jobs = []
        processed_jobs = []
        quick_test = os.getenv('QUICK_TEST', 'true').lower() == 'true'
        
        # Initialize scrapers in priority order
        scrapers = []
        if config["job_search"]["job_boards"].get("reed"):
            scrapers.append(("Reed", ReedScraper(config)))
        if config["job_search"]["job_boards"].get("adzuna"):
            scrapers.append(("Adzuna", AdzunaScraper(config)))
        
        # Process each job board
        for scraper_name, scraper in scrapers:
            try:
                logger.info(f"Starting {scraper_name} job search...")
                found_jobs = False
                
                # Search for jobs using each keyword and location combination
                for keyword in config["job_search"]["keywords"]:
                    if found_jobs and quick_test:
                        break
                        
                    for location in config["job_search"]["locations"]:
                        logger.info(f"Searching {scraper_name} for {keyword} in {location}")
                        jobs = scraper.search(keyword, location)
                        
                        if jobs:
                            logger.info(f"Found {len(jobs)} jobs from {scraper_name} for {keyword} in {location}")
                            all_jobs.extend(jobs)
                            found_jobs = True
                            if quick_test:
                                break
                        else:
                            logger.info(f"No jobs found from {scraper_name} for {keyword} in {location}")
                        
                        # Add a small delay between searches
                        time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {scraper_name}: {str(e)}")
                continue
        
        if not all_jobs:
            logger.warning("No jobs found from any source")
            return
        
        # Remove duplicates based on job URL
        unique_jobs = []
        seen_urls = set()
        for job in all_jobs:
            url = job.get('url') or job.get('redirect_url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)
        
        logger.info(f"Found {len(unique_jobs)} unique jobs across all platforms")
        
        # Filter out senior roles and apply other criteria
        filtered_jobs = [
            job for job in unique_jobs 
            if not any(term.lower() in job['title'].lower() 
                      for term in config["job_search"]["excluded_keywords"])
        ]
        
        logger.info(f"After filtering, {len(filtered_jobs)} jobs remain")
        
        # Process jobs in batches
        batch_size = 3  # Process 3 jobs at a time
        for i in range(0, len(filtered_jobs), batch_size):
            batch = filtered_jobs[i:i + batch_size]
            logger.info(f"Processing batch of {len(batch)} jobs")
            
            for job in batch:
                try:
                    logger.info(f"Processing job: {job['title']} at {job['company']}")
                    processed_job = process_job_application(job)
                    processed_jobs.append(processed_job)
                    
                    # Save the processed job data
                    output_dir = "processed_jobs"
                    os.makedirs(output_dir, exist_ok=True)
                    output_path = os.path.join(
                        output_dir, 
                        f"job_{processed_job.get('job_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )
                    
                    with open(output_path, 'w') as f:
                        json.dump(processed_job, f, indent=2)
                    
                    logger.info(f"Job processing complete. Results saved to: {output_path}")
                    
                    # Add a delay between processing jobs
                    time.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error processing job {job['title']}: {str(e)}")
                    continue
            
            # Add a longer delay between batches
            time.sleep(10)
        
        # Print summary of all processed jobs
        print("\n=== Job Application Summary ===")
        print(f"Total jobs found: {len(unique_jobs)}")
        print(f"Jobs after filtering: {len(filtered_jobs)}")
        print(f"Jobs successfully processed: {len(processed_jobs)}")
        print("\nProcessed Jobs Details:")
        
        for job in processed_jobs:
            print(f"\nJob: {job['title']}")
            print(f"Company: {job['company']}")
            print(f"Location: {job['location']}")
            print(f"Source: {job['source']}")
            print(f"Job URL: {job.get('redirect_url', job.get('url', 'Not available'))}")
            print(f"Resume Drive URL: {job.get('resume_drive_url', 'Not generated')}")
            print(f"Application Date: {job.get('application_date', 'Not processed')}")
            print(f"Status: {job.get('status', 'Unknown')}")
            print(f"Google Sheets Status: {job.get('sheets_status', 'Not added')}")
            print("-" * 50)
        
        logger.info("Job search process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automated Job Search and Application Process')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--skip-sheets', action='store_true', help='Skip Google Sheets integration')
    args = parser.parse_args()
    
    main() 