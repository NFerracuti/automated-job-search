import os
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

from .base_scraper import BaseScraper

load_dotenv()

class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn jobs"""
    
    def __init__(self, config=None, headless=True):
        super().__init__(config)
        self.base_url = "https://www.linkedin.com"
        self.job_search_url = f"{self.base_url}/jobs/search"
        
        # Configure Selenium
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        # LinkedIn credentials
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")
    
    def __del__(self):
        """Clean up the driver when the object is destroyed"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except:
            pass
    
    def login(self):
        """Login to LinkedIn using credentials from .env file"""
        if not self.email or not self.password:
            self.logger.warning("LinkedIn credentials not found in .env file. Proceeding without login.")
            return False
        
        try:
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for the login form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter credentials and submit
            self.driver.find_element(By.ID, "username").send_keys(self.email)
            self.driver.find_element(By.ID, "password").send_keys(self.password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            
            # Wait for the dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "feed-identity-module__actor-meta"))
            )
            
            self.logger.info("Successfully logged in to LinkedIn")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to login to LinkedIn: {str(e)}")
            return False
    
    def search(self, keyword, location, filters=None):
        """Search for jobs on LinkedIn"""
        jobs = []
        max_results = self.config["job_search"]["max_results_per_board"]
        
        try:
            # Construct search URL
            search_url = f"{self.job_search_url}/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
            if filters:
                for key, value in filters.items():
                    search_url += f"&{key}={value}"
            
            self.driver.get(search_url)
            time.sleep(2)  # Allow page to load
            
            # Scroll to load more jobs
            job_list_container = self.driver.find_element(By.CLASS_NAME, "jobs-search__results-list")
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", job_list_container)
            
            while len(jobs) < max_results:
                # Scroll down
                self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", job_list_container)
                time.sleep(1.5)
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", job_list_container)
                if new_height == last_height:
                    break
                last_height = new_height
                
                # Extract job listings
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-search-card")
                
                for card in job_cards:
                    if len(jobs) >= max_results:
                        break
                    
                    try:
                        job_id = card.get_attribute("data-id")
                        # Skip if we already processed this job
                        if any(j["job_id"] == job_id for j in jobs):
                            continue
                        
                        title_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__title")
                        company_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__subtitle")
                        location_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                        link_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__title a")
                        
                        job = {
                            "job_id": job_id,
                            "title": title_element.text.strip(),
                            "company": company_element.text.strip(),
                            "location": location_element.text.strip(),
                            "url": link_element.get_attribute("href"),
                            "source": "LinkedIn",
                            "keyword": keyword,
                            "search_location": location
                        }
                        
                        # Try to extract salary if available
                        try:
                            salary_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__salary-info")
                            job["salary_text"] = salary_element.text.strip()
                            # Extract numeric salary if possible
                            salary_match = re.search(r'\$(\d+,?\d+)', job["salary_text"])
                            if salary_match:
                                job["salary"] = int(salary_match.group(1).replace(',', ''))
                        except NoSuchElementException:
                            job["salary_text"] = "Not specified"
                        
                        jobs.append(job)
                    
                    except Exception as e:
                        self.logger.error(f"Error extracting job card: {str(e)}")
            
            self.logger.info(f"Found {len(jobs)} LinkedIn jobs for {keyword} in {location}")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error searching LinkedIn jobs: {str(e)}")
            return []
    
    def extract_job_details(self, job_url):
        """Extract detailed job information from the job page"""
        try:
            self.driver.get(job_url)
            time.sleep(2)  # Allow page to load
            
            # Extract job description
            job_description = self.driver.find_element(By.CLASS_NAME, "show-more-less-html__markup").text
            
            # Try to find the hiring manager/recruiter
            hiring_manager = None
            try:
                recruiter_section = self.driver.find_element(By.CLASS_NAME, "jobs-poster__name")
                hiring_manager = recruiter_section.text.strip()
            except NoSuchElementException:
                pass
            
            # Try to extract additional details
            details = {}
            try:
                criteria_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-criteria-item")
                for element in criteria_elements:
                    try:
                        label = element.find_element(By.CSS_SELECTOR, ".job-criteria-subheader").text.strip()
                        value = element.find_element(By.CSS_SELECTOR, ".job-criteria-text").text.strip()
                        details[label.lower().replace(' ', '_')] = value
                    except:
                        continue
            except:
                pass
            
            return {
                "description": job_description,
                "hiring_manager": hiring_manager,
                "details": details
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting job details: {str(e)}")
            return {"description": "Failed to extract job details"}

if __name__ == "__main__":
    # Test the scraper
    scraper = LinkedInScraper()
    results = scraper.run(keywords=["python developer"], location=["remote"])
    print(f"Saved results to {results}") 