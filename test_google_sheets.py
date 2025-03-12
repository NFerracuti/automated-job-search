import os
from dotenv import load_dotenv
from src.utils.google_sheets import GoogleSheetsManager
import json
from datetime import datetime

def test_google_sheets():
    """Test Google Sheets integration"""
    print("\nTesting Google Sheets Integration...")
    print("=" * 50)
    
    try:
        # First, verify config structure
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        spreadsheet_id = config.get('google_sheets', {}).get('spreadsheet_id')
        if not spreadsheet_id:
            print("Error: spreadsheet_id not found in config.json")
            print("Current config structure:", json.dumps(config.get('google_sheets', {}), indent=2))
            return
            
        print(f"Found spreadsheet ID in config: {spreadsheet_id}")
        
        # Initialize the sheets manager
        sheets_manager = GoogleSheetsManager()
        
        # Create a test job entry
        test_job = {
            "title": "Test Python Developer",
            "company": "Test Company",
            "location": "Remote",
            "job_type": "Full-time",
            "salary_text": "100000 - 150000",
            "url": "https://example.com/job",
            "description": "This is a test job posting",
            "source": "Test",
            "date_found": datetime.now().isoformat()
        }
        
        print("\nAttempting to add test job to Google Sheets...")
        result = sheets_manager.add_jobs([test_job])
        
        if result:
            print("Successfully added test job!")
            
            print("\nRetrieving all jobs from sheet...")
            all_jobs = sheets_manager.get_all_jobs()
            print(f"Found {len(all_jobs)} total jobs in sheet")
            
            if all_jobs:
                print("\nMost recent job entry:")
                latest_job = all_jobs[-1]
                for key, value in latest_job.items():
                    print(f"{key}: {value}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    load_dotenv()
    
    # First verify we can load the credentials
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds_path:
        print("Error: GOOGLE_APPLICATION_CREDENTIALS not set in .env file")
        exit(1)
    
    if not os.path.exists(creds_path):
        print(f"Error: Credentials file not found at {creds_path}")
        exit(1)
        
    print(f"Found credentials file at: {creds_path}")
    
    # Load config to get spreadsheet name
    with open('config.json', 'r') as f:
        config = json.load(f)
    spreadsheet_name = config["google_sheets"]["spreadsheet_name"]
    print(f"Will look for spreadsheet named: {spreadsheet_name}")
    
    test_google_sheets() 