import os
import json
import requests
from dotenv import load_dotenv
from src.scrapers.adzuna_api import AdzunaScraper
from src.utils.google_sheets import GoogleSheetsManager
import argparse
from datetime import datetime

def print_job_details(job, index):
    """Helper function to print job details in a consistent format"""
    print(f"\nJob {index + 1}:")
    print("-" * 40)
    print(f"Title: {job.get('title')}")
    print(f"Company: {job.get('company', {}).get('display_name') if isinstance(job.get('company'), dict) else job.get('company')}")
    print(f"Location: {job.get('location', {}).get('display_name') if isinstance(job.get('location'), dict) else job.get('location')}")
    print(f"Remote Type: {job.get('remote_type', 'Fully Remote')}")
    print(f"Salary: {job.get('salary_text', 'Not specified')}")
    print(f"URL: {job.get('redirect_url') or job.get('url')}")
    if job.get('description'):
        desc = job.get('description')[:200] + '...' if len(job.get('description', '')) > 200 else job.get('description')
        print(f"Description Preview: {desc}")
    print("-" * 40)

def test_direct_api():
    """Test direct API call to Adzuna"""
    app_id = os.getenv("ADZUNA_APP_ID")
    api_key = os.getenv("ADZUNA_API_KEY")
    
    url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        "app_id": app_id,
        "app_key": api_key,
        "what": "python developer remote",  # Added 'remote' to search query
        "content-type": "application/json",
        "results_per_page": 10  # Increased to get more results before filtering
    }
    
    print("\nTesting direct API call...")
    print("=" * 50)
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        print(f"API Connection Successful!")
        print(f"Total results found: {data.get('count', 0)}")
        
        # Filter for remote jobs
        remote_jobs = []
        for job in data.get('results', []):
            # Skip senior roles
            title_lower = job["title"].lower()
            if any(keyword.lower() in title_lower 
                  for keyword in ['senior', 'sr.', 'sr ', 'lead', 'principal', 'staff']):
                continue
                
            description = job.get('description', '').lower()
            title = job.get('title', '').lower()
            location = str(job.get('location', {}).get('display_name', '')).lower()
            
            # Keywords that indicate fully remote work
            remote_indicators = [
                'fully remote',
                '100% remote',
                'remote position',
                'work from home',
                'work from anywhere',
                'remote work',
                'remote opportunity'
            ]
            
            # Keywords that indicate hybrid or in-office requirements
            exclude_indicators = [
                'hybrid',
                'in office',
                'in-office',
                'on site',
                'on-site',
                'onsite',
                'must be in',
                'must work in',
                'must live in',
                'must be located',
                'must relocate',
                'required to work',
                'days per week in',
                'days in office',
                'office presence',
                'office attendance',
                'come to the office'
            ]
            
            # Skip if any exclude indicators are present
            if any(indicator in description for indicator in exclude_indicators):
                continue
            
            # Check if it's explicitly remote
            is_remote = (
                'remote' in title_lower or 
                'remote' in location or 
                any(indicator in description for indicator in remote_indicators)
            )
            
            if not is_remote:
                continue
                
            remote_jobs.append(job)
        
        print(f"\nFound {len(remote_jobs)} remote jobs from direct API")
        print("\nShowing first 5 remote jobs from direct API:")
        for i, job in enumerate(remote_jobs[:5]):
            print_job_details(job, i)
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_scraper(add_to_sheets=False):
    """Test the AdzunaScraper class"""
    print("\nTesting AdzunaScraper class...")
    print("=" * 50)
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        scraper = AdzunaScraper(config)
        # Use modified search terms to find remote jobs
        jobs = scraper.search("python developer remote", "")  # Empty location parameter
        
        print(f"Successfully found {len(jobs)} remote jobs")
        print("\nShowing first 5 remote jobs from scraper:")
        for i, job in enumerate(jobs[:5]):
            print_job_details(job, i)

        if add_to_sheets:
            print("\nAdding jobs to Google Sheets...")
            sheets_manager = GoogleSheetsManager()
            
            # Format jobs for Google Sheets
            sheet_jobs = []
            for job in jobs:
                sheet_data = {
                    "Job Title": job["title"],
                    "Company": job["company"],
                    "Location": job["location"],
                    "Job Type": "Remote",
                    "Salary Range": job.get("salary_text", "Not specified"),
                    "Job URL": job.get("redirect_url", job.get("url", "")),
                    "Application Status": "New",
                    "Custom Resume URL": "",  # Will be filled when resume is generated
                    "Date Added": datetime.now().strftime("%Y-%m-%d"),
                    "Job Description": job.get("description", "")[:1000],  # Truncate if too long
                    "Source": "Adzuna",
                    "Notes": ""
                }
                sheet_jobs.append(sheet_data)
            
            added_jobs = sheets_manager.add_jobs(sheet_jobs)
            print(f"Added {len(added_jobs)} new jobs to Google Sheets")
            
        return jobs
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

if __name__ == "__main__":
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Test Adzuna API and Scraper')
    parser.add_argument('--add-to-sheets', action='store_true', 
                      help='Add found jobs to Google Sheets')
    args = parser.parse_args()
    
    print("Testing Adzuna API Connection for Remote Jobs...")
    print("=" * 50)
    
    api_jobs = test_direct_api()
    scraper_jobs = test_scraper(add_to_sheets=args.add_to_sheets) 