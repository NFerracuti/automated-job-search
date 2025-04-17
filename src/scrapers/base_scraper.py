import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("job_scraper.log"),
        logging.StreamHandler()
    ]
)

class BaseScraper(ABC):
    """Base class for all job board scrapers"""
    
    def __init__(self, config=None):
        """Initialize with optional config, otherwise load from file"""
        if config:
            self.config = config
        else:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.jobs = []
        # Add quick test mode flag - easy to remove later
        self.quick_test = os.getenv('QUICK_TEST', 'true').lower() == 'true'
    
    @abstractmethod
    def login(self):
        """Authenticate with the job board if needed"""
        pass
    
    @abstractmethod
    def search(self, keywords, location, filters=None):
        """Search for jobs with the given parameters"""
        pass
    
    @abstractmethod
    def extract_job_details(self, job_url):
        """Extract detailed information about a job"""
        pass
    
    def filter_jobs(self, jobs_list):
        """Filter jobs based on criteria in config"""
        filtered_jobs = []
        min_salary = self.config["job_search"]["min_salary"]
        excluded_keywords = self.config["job_search"]["excluded_keywords"]
        
        for job in jobs_list:
            # Skip jobs with excluded keywords in title
            if any(keyword.lower() in job.get("title", "").lower() for keyword in excluded_keywords):
                self.logger.info(f"Filtering out job: {job.get('title')} - contains excluded keyword")
                continue
            
            # Check salary if available
            salary = job.get("salary")
            if salary and isinstance(salary, (int, float)) and salary < min_salary:
                self.logger.info(f"Filtering out job: {job.get('title')} - salary below minimum")
                continue
            
            # Add timestamp
            job["date_found"] = datetime.now().isoformat()
            filtered_jobs.append(job)
        
        return filtered_jobs
    
    def save_results(self, filename=None):
        """Save scraped job results to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jobs_{self.__class__.__name__.lower()}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.jobs, f, indent=2)
        
        self.logger.info(f"Saved {len(self.jobs)} jobs to {filename}")
        return filename
    
    def run(self, keywords=None, location=None):
        """Run the full scraping workflow"""
        if not keywords:
            keywords = self.config["job_search"]["keywords"]
        
        if not location:
            location = self.config["job_search"]["locations"]
        
        try:
            self.login()
            for keyword in keywords:
                for loc in location:
                    self.logger.info(f"Searching for {keyword} in {loc}")
                    jobs = self.search(keyword, loc)
                    self.jobs.extend(jobs)
                    
                    # If in quick test mode and we found at least one job, stop searching
                    if self.quick_test and len(self.jobs) > 0:
                        self.logger.info("Quick test mode: Found a job, stopping search")
                        break
                
                # If in quick test mode and we found at least one job, stop searching keywords
                if self.quick_test and len(self.jobs) > 0:
                    break
            
            self.jobs = self.filter_jobs(self.jobs)
            return self.save_results()
        
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            return None 