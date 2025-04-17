# Automated Job Search System

## Setup Instructions

1. Clone the repository:

```bash
git clone https://github.com/yourusername/automated-job-search.git
cd automated-job-search
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up Google Cloud Console:

   1. Go to [Google Cloud Console](https://console.cloud.google.com/)
   2. Create a new project or select an existing one
   3. Enable required APIs:
      - Go to "APIs & Services" > "Library"
      - Search for and enable:
        - Google Sheets API
        - Google Drive API
   4. Create service account credentials:
      - Go to "APIs & Services" > "Credentials"
      - Click "Create Credentials" > "Service Account"
      - Fill in service account details
      - Click "Create and Continue"
      - For Role, select "Editor" (or create custom role with Sheets and Drive permissions)
      - Click "Done"
   5. Generate JSON key:
      - Click on the created service account
      - Go to "Keys" tab
      - Click "Add Key" > "Create new key"
      - Choose JSON format
      - Click "Create"
      - Save the downloaded JSON file as `google-services-account.json` in the project root directory
   6. Share Google Sheet:
      - Create a new Google Sheet
      - Click "Share" button
      - Add the service account email (found in the JSON file)
      - Give "Editor" access
      - Get the spreadsheet ID from the URL:
        - The URL format is: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
        - Copy the ID between `/d/` and `/edit`
      - Add the spreadsheet ID to `config.json`:
        ```json
        "google_sheets": {
            "spreadsheet_id": "YOUR_SPREADSHEET_ID",
            ...
        }
        ```

4. Set up Job Board APIs:

   a. Reed API:

   1. Go to [Reed Developer Portal](https://www.reed.co.uk/developers)
   2. Sign in or create an account
   3. Navigate to "API Keys" section
   4. Click "Generate new API key"
   5. Copy the generated API key
   6. Note: Keep this key secure and never share it publicly

   b. Adzuna API:

   1. Go to [Adzuna API Portal](https://developer.adzuna.com/)
   2. Sign in or create an account
   3. Navigate to "My Apps" section
   4. Click "Create new app"
   5. Fill in the required details
   6. Once created, you'll receive an App ID and App Key
   7. Note: Keep these keys secure and never share them publicly

5. Set up OpenAI API (you must be an Openai paid subscriber to this):

   1. Go to [OpenAI Platform](https://platform.openai.com/)
   2. Sign in or create an account
   3. Click on your profile icon > "View API keys"
   4. Click "Create new secret key"
   5. Copy the generated API key
   6. Note: Keep this key secure and never share it publicly

6. Set up environment variables:

   - Copy `.env.example` to `.env`
   - Fill in your API keys and credentials:
     - `OPENAI_API_KEY`: Your OpenAI API key (from step 5)
     - `REED_API_KEY`: Your Reed API key (from step 4a)
     - `ADZUNA_API_KEY`: Your Adzuna API key (from step 4b)
     - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google service account JSON file (e.g., "./google-services-account.json")

7. Configure the application:

   - Copy `config.example.json` to `config.json`
   - Customize the following sections:
     - `job_search`: Set your preferred keywords, locations, and salary requirements
     - `google_sheets`: Configure your spreadsheet name and structure
     - `resume`: Set your resume template path and Google Drive folder ID

8. Run the application:

```bash
python main.py
```

## Configuration

The system uses two configuration files:

1. `.env`: Contains sensitive information and API keys
2. `config.json`: Contains application settings and preferences

### Environment Variables (.env)

- API keys for various services
- Google service account credentials
- Other sensitive configuration

### Application Config (config.json)

- Job search parameters
- Google Sheets configuration
- Resume generation settings

## Features

- Automated job search across multiple platforms
- Customizable job filtering
- Automated resume generation
- Google Sheets integration for tracking applications
- Support for multiple job boards (LinkedIn, Reed, Adzuna)

## Security Notes

- Never commit your `.env` or `config.json` files
- Keep your API keys secure
- Use environment variables for sensitive data
- Regularly rotate your API keys

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
