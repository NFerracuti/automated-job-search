import os
import json
import logging
from datetime import datetime

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

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
        # Load config
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Load credentials
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set in .env file")
        
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                creds_path, 
                scopes=['https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive']
            )
            
            # Create service clients
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            
            # Get or create the job tracking spreadsheet
            self.spreadsheet_id = self._get_or_create_spreadsheet()
            
            logger.info(f"Google Sheets Manager initialized. Spreadsheet ID: {self.spreadsheet_id}")
        
        except Exception as e:
            logger.error(f"Error initializing Google Sheets Manager: {str(e)}")
            raise
    
    def _get_or_create_spreadsheet(self):
        """Get the job tracking spreadsheet or create it if it doesn't exist"""
        spreadsheet_name = self.config["google_sheets"]["spreadsheet_name"]
        
        try:
            # Search for existing spreadsheet
            results = self.drive_service.files().list(
                q=f"name='{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                spreadsheet_id = files[0]['id']
                logger.info(f"Found existing spreadsheet: {spreadsheet_name} ({spreadsheet_id})")
                return spreadsheet_id
            
            # Create new spreadsheet if not found
            sheet_metadata = {
                'properties': {
                    'title': spreadsheet_name
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'Jobs',
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': len(self.config["google_sheets"]["sheets"]["jobs"]["columns"])
                            }
                        }
                    }
                ]
            }
            
            spreadsheet = self.sheets_service.spreadsheets().create(
                body=sheet_metadata
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            
            # Add header row
            self._update_values(
                spreadsheet_id,
                'Jobs!A1:Z1',
                [self.config["google_sheets"]["sheets"]["jobs"]["columns"]]
            )
            
            # Format header row
            format_request = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {
                                        'red': 0.2,
                                        'green': 0.2,
                                        'blue': 0.2
                                    },
                                    'textFormat': {
                                        'bold': True,
                                        'foregroundColor': {
                                            'red': 1.0,
                                            'green': 1.0,
                                            'blue': 1.0
                                        }
                                    }
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    }
                ]
            }
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=format_request
            ).execute()
            
            logger.info(f"Created new spreadsheet: {spreadsheet_name} ({spreadsheet_id})")
            return spreadsheet_id
        
        except Exception as e:
            logger.error(f"Error getting/creating spreadsheet: {str(e)}")
            raise
    
    def _update_values(self, spreadsheet_id, range_name, values):
        """Update values in the specified range"""
        try:
            body = {
                'values': values
            }
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return result
        
        except Exception as e:
            logger.error(f"Error updating values: {str(e)}")
            raise
    
    def _append_values(self, spreadsheet_id, range_name, values):
        """Append values to the specified range"""
        try:
            body = {
                'values': values
            }
            
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            return result
        
        except Exception as e:
            logger.error(f"Error appending values: {str(e)}")
            raise
    
    def add_jobs(self, jobs):
        """Add jobs to the spreadsheet"""
        if not jobs:
            logger.warning("No jobs to add to spreadsheet")
            return []
        
        try:
            # Get current jobs in the spreadsheet to avoid duplicates
            current_jobs = self.get_all_jobs()
            current_urls = set(job.get('Job URL', '') for job in current_jobs)
            
            # Format jobs for the spreadsheet
            rows_to_add = []
            added_jobs = []
            
            columns = self.config["google_sheets"]["sheets"]["jobs"]["columns"]
            
            for job in jobs:
                # Skip if job URL is already in spreadsheet
                if job.get('url', '') in current_urls:
                    logger.info(f"Skipping duplicate job: {job.get('title')} at {job.get('company')}")
                    continue
                
                # Map job data to spreadsheet columns
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
                        row.append('')  # Will be filled later
                    elif column == "Hiring Manager":
                        row.append(job.get('hiring_manager', ''))
                    elif column == "Contact Email":
                        row.append(job.get('contact_email', ''))
                    elif column == "Date Added":
                        row.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        row.append('')  # Default empty value for other columns
                
                rows_to_add.append(row)
                added_jobs.append(job)
            
            if rows_to_add:
                result = self._append_values(
                    self.spreadsheet_id,
                    'Jobs!A2:Z',
                    rows_to_add
                )
                
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
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Jobs!A1:Z'
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.info("No data found in spreadsheet")
                return []
            
            # Convert to list of dictionaries
            headers = values[0]
            jobs = []
            
            for row in values[1:]:
                # Pad row if necessary
                padded_row = row + [''] * (len(headers) - len(row))
                job = {headers[i]: padded_row[i] for i in range(len(headers))}
                jobs.append(job)
            
            logger.info(f"Retrieved {len(jobs)} jobs from spreadsheet")
            return jobs
        
        except Exception as e:
            logger.error(f"Error getting jobs from spreadsheet: {str(e)}")
            return []
    
    def update_job(self, job_url, updates):
        """Update a job in the spreadsheet by its URL"""
        try:
            # Get current jobs
            result = self.sheets_service.spreadsheets().values().get(
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
            
            self._update_values(
                self.spreadsheet_id,
                update_range,
                [row_data]
            )
            
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