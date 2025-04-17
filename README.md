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

3. Set up environment variables:

   - Copy `.env.example` to `.env`
   - Fill in your API keys and credentials:
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `REED_API_KEY`: Your Reed API key
     - `ADZUNA_API_KEY`: Your Adzuna API key
     - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google service account credentials

4. Configure the application:

   - Copy `config.example.json` to `config.json`
   - Customize the following sections:
     - `job_search`: Set your preferred keywords, locations, and salary requirements
     - `google_sheets`: Configure your spreadsheet name and structure
     - `resume`: Set your resume template path and Google Drive folder ID

5. Set up Google Sheets:

   - Create a new Google Sheet
   - Share it with the service account email from your credentials
   - Copy the spreadsheet ID from the URL
   - Update `config.json` with your spreadsheet ID

6. Run the application:

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

## License

MIT License
