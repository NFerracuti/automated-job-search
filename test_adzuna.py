import os
import json
import requests
from dotenv import load_dotenv
from src.scrapers.adzuna_api import AdzunaScraper

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
            description = job.get('description', '').lower()
            title = job.get('title', '').lower()
            location = str(job.get('location', {}).get('display_name', '')).lower()
            
            if ('remote' in description or 'remote' in title or 'remote' in location or
                'work from home' in description or 'wfh' in description):
                remote_jobs.append(job)
        
        print(f"\nFound {len(remote_jobs)} remote jobs from direct API")
        print("\nShowing first 5 remote jobs from direct API:")
        for i, job in enumerate(remote_jobs[:5]):
            print_job_details(job, i)
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_scraper():
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
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    print("Testing Adzuna API Connection for Remote Jobs...")
    print("=" * 50)
    
    test_direct_api()
    test_scraper() 