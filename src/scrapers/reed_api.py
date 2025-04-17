from datetime import datetime
import requests
from .base_scraper import BaseScraper
import os
import base64

class ReedScraper(BaseScraper):
    """Scraper for Reed.co.uk API"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = os.getenv("REED_API_KEY")
        self.base_url = "https://www.reed.co.uk/api/1.0/search"
        
        # Create Basic Auth header
        auth_str = f"{self.api_key}:"  # Empty password
        auth_bytes = auth_str.encode('ascii')
        self.auth_header = base64.b64encode(auth_bytes).decode('ascii')
    
    def search(self, keywords, location, filters=None):
        """Search for jobs using Reed.co.uk API"""
        try:
            # Add 'remote' to keywords if not already present
            if 'remote' not in keywords.lower():
                keywords = f"{keywords} remote"
            
            params = {
                "keywords": keywords,
                "resultsToTake": self.config["job_search"]["max_results_per_board"],
                "permanent": "true",  # Only permanent positions
                "fullTime": "true"    # Full-time positions
            }
            
            # Add location if it's not 'remote'
            if location and location.lower() != 'remote':
                params["locationName"] = location
                params["distanceFromLocation"] = 20  # 20 miles radius
            
            # Add salary filter if configured
            if self.config["job_search"]["min_salary"]:
                params["minimumSalary"] = self.config["job_search"]["min_salary"]
            
            headers = {
                "Authorization": f"Basic {self.auth_header}",
                "Content-Type": "application/json"
            }
            
            self.logger.info(f"Searching Reed with params: {params}")
            response = requests.get(self.base_url, params=params, headers=headers)
            
            if response.status_code != 200:
                self.logger.error(f"Reed API error: {response.status_code} - {response.text}")
                return []
                
            data = response.json()
            
            if not isinstance(data, dict) or 'results' not in data:
                self.logger.error(f"Unexpected response format: {data}")
                return []
            
            jobs = []
            for job in data['results']:
                title_lower = job["jobTitle"].lower()
                description_lower = job.get("jobDescription", "").lower()
                location = str(job.get("locationName", "")).lower()
                
                # Keywords to exclude from both title and description
                exclude_keywords = [
                    'senior',
                    'sr.',
                    'sr ',
                    'lead',
                    'principal',
                    'staff',
                    'manager',
                    'director',
                    'head of',
                    'chief'
                ]
                
                # Skip if excluded keywords are in title or description
                if any(keyword in title_lower for keyword in exclude_keywords) or \
                   any(keyword in description_lower for keyword in exclude_keywords):
                    continue
                
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
                
                # Check if it's explicitly remote
                is_remote = (
                    'remote' in title_lower or 
                    'remote' in location or 
                    any(indicator in description_lower for indicator in remote_indicators)
                )
                
                if not is_remote:
                    continue
                
                # Format salary text
                salary_min = job.get("minimumSalary")
                salary_max = job.get("maximumSalary")
                salary_text = "Not specified"
                if salary_min and salary_max:
                    salary_text = f"£{salary_min:,} - £{salary_max:,}"
                elif salary_min:
                    salary_text = f"£{salary_min:,}+"
                elif salary_max:
                    salary_text = f"Up to £{salary_max:,}"
                
                job_data = {
                    "title": job["jobTitle"],
                    "company": job["employerName"],
                    "location": job["locationName"],
                    "url": job.get("jobUrl") or f"https://www.reed.co.uk/jobs/{job['jobId']}",
                    "salary_text": salary_text,
                    "salary": job.get("minimumSalary"),
                    "description": job.get("jobDescription", ""),
                    "source": "Reed",
                    "date_found": datetime.now().isoformat(),
                    "remote_type": "Fully Remote",
                    "job_id": job["jobId"]
                }
                jobs.append(job_data)
            
            self.logger.info(f"Found {len(jobs)} fully remote jobs from Reed matching criteria")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error searching Reed: {str(e)}")
            return []
    
    def login(self):
        """No login required for API"""
        pass
    
    def extract_job_details(self, job_url):
        """Get detailed job information if needed"""
        try:
            # Extract job ID from URL
            job_id = job_url.split('/')[-1]
            
            # Call the details API
            url = f"https://www.reed.co.uk/api/1.0/jobs/{job_id}"
            headers = {
                "Authorization": f"Basic {self.auth_header}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get job details: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting job details: {str(e)}")
            return {} 