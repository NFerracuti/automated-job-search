# Automated Job Application Workflow

This tool automates the job application process by:

1. Scraping job boards for relevant positions
2. Storing job listings in Google Sheets
3. Customizing resumes using OpenAI
4. Generating tailored resume documents
5. Tracking application status and details

## Setup Instructions

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables in `.env` file:
   ```
   OPENAI_API_KEY=your_openai_key
   GOOGLE_CREDENTIALS_PATH=path_to_google_credentials.json
   RESUME_TEMPLATE_PATH=path_to_resume_template.docx
   ```
4. Run the setup script: `python setup.py`
5. Start the application: `python main.py`

## Components

- `src/scrapers/`: Job board scraping modules
- `src/resume_generator/`: Resume customization with OpenAI
- `src/document_creator/`: Document generation tools
- `src/utils/`: Helper functions and utilities

## Usage

The application can be run in several modes:

- Scrape and store jobs: `python main.py --scrape`
- Generate resumes: `python main.py --generate-resumes`
- Full workflow: `python main.py --full-workflow`

See `python main.py --help` for all options.

## Configuration

Edit `config.json` to customize:

- Job search parameters
- Resume template settings
- Application tracking preferences
