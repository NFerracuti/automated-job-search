from datetime import datetime
import requests
from .base_scraper import BaseScraper
import os

class AdzunaScraper(BaseScraper):
    """Scraper for Adzuna API"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.api_key = os.getenv("ADZUNA_API_KEY")
        self.base_url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
    
    def search(self, keywords, location, filters=None):
        """Search for jobs using Adzuna API"""
        try:
            # Add 'remote' to keywords if not already present
            if 'remote' not in keywords.lower():
                keywords = f"{keywords} remote"
            
            params = {
                "app_id": self.app_id,
                "app_key": self.api_key,
                "what": keywords,
                "content-type": "application/json",
                "results_per_page": self.config["job_search"]["max_results_per_board"]
            }
            
            # Only add location if it's not empty and not 'remote'
            if location and location.lower() != 'remote':
                params["where"] = location
            
            # Add salary filter if configured
            if self.config["job_search"]["min_salary"]:
                params["salary_min"] = self.config["job_search"]["min_salary"]
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data.get("results", []):
                # Skip jobs with excluded keywords
                if any(keyword.lower() in job["title"].lower() 
                      for keyword in self.config["job_search"]["excluded_keywords"]):
                    continue
                
                # Check for remote indicators
                description = job.get("description", "").lower()
                title = job.get("title", "").lower()
                location = str(job.get("location", {}).get("display_name", "")).lower()
                
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
                
                # Check if any exclude indicators are present
                if any(indicator in description for indicator in exclude_indicators):
                    continue
                
                # Check if it's explicitly remote (either in title/location or has strong remote indicators in description)
                is_remote = (
                    'remote' in title or 
                    'remote' in location or 
                    any(indicator in description for indicator in remote_indicators)
                )
                
                if not is_remote:
                    continue
                
                job_data = {
                    "title": job["title"],
                    "company": job["company"]["display_name"],
                    "location": job["location"]["display_name"],
                    "url": job["redirect_url"],
                    "salary_text": str(job.get("salary_min", "")) + " - " + str(job.get("salary_max", "")),
                    "salary": job.get("salary_min"),
                    "description": job.get("description", ""),
                    "source": "Adzuna",
                    "date_found": datetime.now().isoformat(),
                    "remote_type": "Fully Remote"  # Adding this field for clarity
                }
                jobs.append(job_data)
            
            self.logger.info(f"Found {len(jobs)} fully remote jobs from Adzuna matching criteria")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error searching Adzuna: {str(e)}")
            return []
    
    def login(self):
        """No login required for API"""
        pass
    
    def extract_job_details(self, job_url):
        """Job details already included in search results"""
        return {} 