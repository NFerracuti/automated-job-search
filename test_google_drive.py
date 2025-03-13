import logging
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_google_drive_connection():
    """Test direct Google Drive API connection"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get credentials file path
        credentials_file = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        logger.info(f"Looking for credentials at: {credentials_file}")
        
        if not credentials_file or not os.path.exists(credentials_file):
            logger.error(f"Credentials file not found: {credentials_file}")
            return
            
        # Initialize service
        SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES)
        
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Test a simple API call
        results = drive_service.files().list(
            pageSize=5, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        
        if not items:
            logger.info("No files found in Google Drive.")
        else:
            logger.info("Google Drive connection successful! Files found:")
            for item in items:
                logger.info(f"{item['name']} ({item['id']})")
                
    except Exception as e:
        logger.error(f"Error testing Google Drive: {str(e)}")

if __name__ == "__main__":
    test_google_drive_connection() 