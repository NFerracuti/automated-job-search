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
logger = logging.getLogger('GoogleSheetsManager')

class GoogleSheetsManager:
    """Class to manage Google Sheets operations for job applications"""
    
    def __init__(self, config_path='config.json'):
        """Initialize the Google Sheets manager"""
        try:
            # Load config
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            
            # Set up Google Sheets API client
            creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not creds_path:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set in .env file")
            
            credentials = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                       'https://www.googleapis.com/auth/drive']
            )
            
            self.service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            
            # Get or create spreadsheet
            self.spreadsheet_id = self.config["google_sheets"].get("spreadsheet_id")
            if not self.spreadsheet_id:
                self.create_job_tracker_spreadsheet()
            
            logger.info("Google Sheets Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Google Sheets Manager: {str(e)}")
            raise
    
    def create_job_tracker_spreadsheet(self):
        """Create a new job tracker spreadsheet"""
        try:
            # Create new spreadsheet
            spreadsheet = {
                'properties': {
                    'title': self.config["google_sheets"]["spreadsheet_name"]
                },
                'sheets': [{
                    'properties': {
                        'title': 'Jobs',
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    }
                }]
            }
            
            sheet = self.service.spreadsheets().create(body=spreadsheet).execute()
            self.spreadsheet_id = sheet['spreadsheetId']
            
            # Update config with new spreadsheet ID
            self.config["google_sheets"]["spreadsheet_id"] = self.spreadsheet_id
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Set up header row
            headers = self.config["google_sheets"]["sheets"]["jobs"]["columns"]
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range='Jobs!A1',
                valueInputOption='RAW',
                body={
                    'values': [headers]
                }
            ).execute()
            
            # Format header row
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.8,
                                'green': 0.8,
                                'blue': 0.8
                            },
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            logger.info(f"Created new job tracker spreadsheet with ID: {self.spreadsheet_id}")
            
        except Exception as e:
            logger.error(f"Error creating job tracker spreadsheet: {str(e)}")
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
                job_url = job.get('Job URL', '')
                if job_url in current_urls:
                    logger.info(f"Skipping duplicate job: {job.get('Job Title')} at {job.get('Company')}")
                    continue
                
                # Create row with columns in correct order
                row = []
                for column in columns:
                    row.append(str(job.get(column, '')))
                
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
                
                logger.info(f"Added {len(rows_to_add)} jobs to spreadsheet")
                return added_jobs
            else:
                logger.info("No new jobs to add to spreadsheet")
                return []
                
        except Exception as e:
            logger.error(f"Error adding jobs to spreadsheet: {str(e)}")
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
            logger.error(f"Error getting jobs from spreadsheet: {str(e)}")
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