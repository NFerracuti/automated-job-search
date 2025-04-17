import os
import json
from dotenv import load_dotenv
from src.scrapers.reed_api import ReedScraper
from src.utils.google_sheets import GoogleSheetsManager
import argparse
from datetime import datetime

def print_job_details(job, index):
    """Helper function to print job details in a consistent format"""
    print(f"\nJob {index + 1}:")
    print("-" * 40)
    print(f"Title: {job.get('title')}")
    print(f"Company: {job.get('company')}")
    print(f"Location: {job.get('location')}")
    print(f"Remote Type: {job.get('remote_type', 'Fully Remote')}")
    print(f"Salary: {job.get('salary_text', 'Not specified')}")
    print(f"URL: {job.get('url')}")
    if job.get('description'):
        desc = job.get('description')[:200] + '...' if len(job.get('description', '')) > 200 else job.get('description')
        print(f"Description Preview: {desc}")
    print("-" * 40)

def test_scraper(add_to_sheets=False):
    """Test the ReedScraper class"""
    print("\nTesting ReedScraper class...")
    print("=" * 50)
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        scraper = ReedScraper(config)
        
        # Test different search combinations
        search_tests = [
            ("python developer", "remote"),  # Remote only
            ("javascript developer", "London"),  # Specific location
            ("react developer remote", "")  # Remote in keywords
        ]
        
        all_jobs = []
        for keywords, location in search_tests:
            print(f"\nSearching for: {keywords} in {location or 'any location'}")
            jobs = scraper.search(keywords, location)
            print(f"Found {len(jobs)} jobs")
            all_jobs.extend(jobs)
            
            if jobs:
                print("\nShowing first 2 jobs from this search:")
                for i, job in enumerate(jobs[:2]):
                    print_job_details(job, i)
        
        print(f"\nTotal unique jobs found: {len(all_jobs)}")

        if add_to_sheets and all_jobs:
            print("\nAdding jobs to Google Sheets...")
            sheets_manager = GoogleSheetsManager()
            
            # Format jobs for Google Sheets
            sheet_jobs = []
            for job in all_jobs:
                sheet_data = {
                    "Job Title": job["title"],
                    "Company": job["company"],
                    "Location": job["location"],
                    "Job Type": "Remote",
                    "Salary Range": job.get("salary_text", "Not specified"),
                    "Job URL": job["url"],
                    "Application Status": "New",
                    "Custom Resume URL": "",  # Will be filled when resume is generated
                    "Date Added": datetime.now().strftime("%Y-%m-%d"),
                    "Job Description": job.get("description", "")[:1000],  # Truncate if too long
                    "Source": "Reed",
                    "Notes": ""
                }
                sheet_jobs.append(sheet_data)
            
            added_jobs = sheets_manager.add_jobs(sheet_jobs)
            print(f"Added {len(added_jobs)} new jobs to Google Sheets")
            
        return all_jobs
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

if __name__ == "__main__":
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Test Reed API and Scraper')
    parser.add_argument('--add-to-sheets', action='store_true', 
                      help='Add found jobs to Google Sheets')
    args = parser.parse_args()
    
    print("Testing Reed API Connection for Remote Jobs...")
    print("=" * 50)
    
    scraper_jobs = test_scraper(add_to_sheets=args.add_to_sheets) 