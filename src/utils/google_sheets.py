import os
import json
import logging
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('GoogleSheets')

class GoogleSheetsManager:
    """Class to manage Google Sheets operations for job applications"""
    
    def __init__(self, config_path='config.json'):
        """Initialize with config from file"""
        # Load config
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set up credentials
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set in .env file")
        
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                creds_path, 
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Create service client
            self.service = build('sheets', 'v4', credentials=self.credentials)
            
            # Get spreadsheet ID from config
            self.spreadsheet_id = self.config["google_sheets"]["spreadsheet_id"]
            
            # Initialize the sheet if needed
            self._init_sheet()
            
        except Exception as e:
            self.logger.error(f"Error initializing Google Sheets Manager: {str(e)}")
            raise
    
    def _init_sheet(self):
        """Initialize the sheet with headers if needed"""
        try:
            # Get the sheet metadata first
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            # Check if "Jobs" sheet exists
            sheets = sheet_metadata.get('sheets', [])
            jobs_sheet = None
            for sheet in sheets:
                if sheet['properties']['title'] == 'Jobs':
                    jobs_sheet = sheet
                    break
            
            if not jobs_sheet:
                # Create new "Jobs" sheet with default formatting
                self.logger.info("Creating new 'Jobs' sheet...")
                result = self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={
                        "requests": [{
                            "addSheet": {
                                "properties": {
                                    "title": "Jobs",
                                    "gridProperties": {
                                        "rowCount": 1000,
                                        "columnCount": 15
                                    }
                                }
                            }
                        }]
                    }
                ).execute()
                
                # Get the new sheet's ID
                jobs_sheet = result['replies'][0]['addSheet']
            
            # Set up headers
            headers = self.config["google_sheets"]["sheets"]["jobs"]["columns"]
            
            # Update headers
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range='Jobs!A1',
                valueInputOption='RAW',
                body={
                    'values': [headers]
                }
            ).execute()
            
            # Only make headers bold, keep everything else default
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={
                    "requests": [{
                        "repeatCell": {
                            "range": {
                                "sheetId": jobs_sheet['properties']['sheetId'],
                                "startRowIndex": 0,
                                "endRowIndex": 1
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "textFormat": {
                                        "bold": True
                                    }
                                }
                            },
                            "fields": "userEnteredFormat.textFormat.bold"
                        }
                    }]
                }
            ).execute()
            
            self.logger.info("Sheet initialized successfully!")
            
        except Exception as e:
            self.logger.error(f"Error initializing sheet: {str(e)}")
            raise
    
    def add_jobs(self, jobs):
        """Add jobs to the spreadsheet"""
        if not jobs:
            return []
        
        try:
            # Get current jobs to check for duplicates
            current_jobs = self.get_all_jobs()
            current_urls = set(job.get('Job URL', '') for job in current_jobs)
            
            # Format new jobs for the spreadsheet
            rows_to_add = []
            added_jobs = []
            
            columns = self.config["google_sheets"]["sheets"]["jobs"]["columns"]
            
            for job in jobs:
                # Skip if job URL is already in spreadsheet
                if job.get('url', '') in current_urls:
                    self.logger.info(f"Skipping duplicate job: {job.get('title')} at {job.get('company')}")
                    continue
                
                row = []
                for column in columns:
                    if column == "Job Title":
                        row.append(job.get('title', ''))
                    elif column == "Company":
                        row.append(job.get('company', ''))
                    elif column == "Location":
                        row.append(job.get('location', ''))
                    elif column == "Job Type":
                        row.append(job.get('job_type', ''))
                    elif column == "Salary Range":
                        row.append(job.get('salary_text', ''))
                    elif column == "Job URL":
                        row.append(job.get('url', ''))
                    elif column == "Application Status":
                        row.append("Not Started")
                    elif column == "Custom Resume URL":
                        row.append('')
                    elif column == "Hiring Manager":
                        row.append(job.get('hiring_manager', ''))
                    elif column == "Contact Email":
                        row.append(job.get('contact_email', ''))
                    elif column == "Date Added":
                        row.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        row.append('')
                
                rows_to_add.append(row)
                added_jobs.append(job)
            
            if rows_to_add:
                self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range='Jobs!A2',
                    valueInputOption='RAW',
                    insertDataOption='INSERT_ROWS',
                    body={
                        'values': rows_to_add
                    }
                ).execute()
                
                self.logger.info(f"Added {len(rows_to_add)} jobs to spreadsheet")
                return added_jobs
            else:
                self.logger.info("No new jobs to add to spreadsheet")
                return []
                
        except Exception as e:
            self.logger.error(f"Error adding jobs to spreadsheet: {str(e)}")
            return []
    
    def get_all_jobs(self):
        """Get all jobs from the spreadsheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Jobs!A1:Z'
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            headers = values[0]
            jobs = []
            
            for row in values[1:]:
                # Pad row if necessary
                padded_row = row + [''] * (len(headers) - len(row))
                job = {headers[i]: padded_row[i] for i in range(len(headers))}
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error getting jobs from spreadsheet: {str(e)}")
            return []
    
    def update_job(self, job_url, updates):
        """Update a job in the spreadsheet by its URL"""
        try:
            # Get current jobs
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Jobs!A1:Z'
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning("No data found in spreadsheet")
                return False
            
            headers = values[0]
            url_index = headers.index('Job URL') if 'Job URL' in headers else -1
            
            if url_index == -1:
                logger.warning("Job URL column not found in spreadsheet")
                return False
            
            # Find the job row
            row_index = -1
            for i, row in enumerate(values[1:], 1):
                if len(row) > url_index and row[url_index] == job_url:
                    row_index = i
                    break
            
            if row_index == -1:
                logger.warning(f"Job with URL {job_url} not found in spreadsheet")
                return False
            
            # Update the row
            update_range = f'Jobs!A{row_index+1}:Z{row_index+1}'
            row_data = values[row_index]
            
            for key, value in updates.items():
                if key in headers:
                    col_index = headers.index(key)
                    # Extend row if needed
                    while len(row_data) <= col_index:
                        row_data.append('')
                    row_data[col_index] = value
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=update_range,
                valueInputOption='USER_ENTERED',
                body={
                    'values': [row_data]
                }
            ).execute()
            
            logger.info(f"Updated job with URL {job_url}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating job in spreadsheet: {str(e)}")
            return False
    
    def get_jobs_for_resume_generation(self):
        """Get jobs that need resume generation"""
        try:
            jobs = self.get_all_jobs()
            
            # Filter jobs that have no resume URL and are not applied or rejected
            resume_jobs = [
                job for job in jobs 
                if not job.get('Custom Resume URL') and 
                job.get('Application Status') == 'Not Started'
            ]
            
            logger.info(f"Found {len(resume_jobs)} jobs for resume generation")
            return resume_jobs
        
        except Exception as e:
            logger.error(f"Error getting jobs for resume generation: {str(e)}")
            return [] 