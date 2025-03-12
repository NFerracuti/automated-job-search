#!/usr/bin/env python3
"""
Automated Job Application Workflow

This script automates the job application process by:
1. Scraping job boards for relevant positions
2. Storing job listings in Google Sheets
3. Customizing resumes using OpenAI
4. Generating tailored resume documents
5. Tracking application status and details
"""

import os
import json
import time
import argparse
import logging
from datetime import datetime

from dotenv import load_dotenv

# Import components
from src.scrapers import LinkedInScraper
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
logger = logging.getLogger('main')

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
    
    # Add other job board scrapers here as they're implemented
    # if job_boards.get("indeed"):
    #     logger.info("Scraping Indeed jobs...")
    #     indeed_scraper = IndeedScraper(config=config, headless=not args.show_browser)
    #     indeed_jobs = indeed_scraper.run()
    #     if indeed_jobs:
    #         with open(indeed_jobs, 'r') as f:
    #             jobs.extend(json.load(f))
    
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

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Automated Job Application Workflow")
    
    # Main commands
    parser.add_argument("--setup", action="store_true", help="Run initial setup")
    parser.add_argument("--scrape", action="store_true", help="Scrape job boards")
    parser.add_argument("--generate-resumes", action="store_true", help="Generate tailored resumes")
    parser.add_argument("--full-workflow", action="store_true", help="Run the complete workflow")
    
    # Options
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--show-browser", action="store_true", help="Show browser during scraping")
    parser.add_argument("--skip-sheets", action="store_true", help="Skip adding jobs to Google Sheets")
    parser.add_argument("--max-resumes", type=int, help="Maximum number of resumes to generate")
    
    args = parser.parse_args()
    
    # Default to --help if no arguments provided
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Run setup if requested
    if args.setup:
        setup()
        return
    
    # Run workflow components
    if args.scrape or args.full_workflow:
        job_file = scrape_jobs(args)
        logger.info(f"Job scraping completed. Results in {job_file}")
    
    if args.generate_resumes or args.full_workflow:
        generate_resumes(args)
        logger.info("Resume generation completed")
    
    logger.info("Job application workflow completed")

if __name__ == "__main__":
    main() 