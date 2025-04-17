import os
import shutil
from pathlib import Path

def setup_environment():
    print("Setting up Automated Job Search System...")
    
    # Create necessary directories
    directories = [
        "generated_resumes",
        "assets",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Copy example files if they don't exist
    if not os.path.exists(".env"):
        shutil.copy(".env.example", ".env")
        print("\nCreated .env file. Please edit it with your API keys and credentials.")
    
    if not os.path.exists("config.json"):
        shutil.copy("config.example.json", "config.json")
        print("Created config.json. Please customize it with your preferences.")
    
    # Check for required files
    required_files = [
        "assets/resume_template_example.txt",
        "requirements.txt"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"\nWarning: Required file {file} not found!")
    
    print("\nSetup complete! Please:")
    print("1. Edit .env with your API keys and credentials")
    print("2. Customize config.json with your preferences")
    print("3. Run 'python main.py' to start the application")

if __name__ == "__main__":
    setup_environment() 