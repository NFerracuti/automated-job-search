import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_resume_data():
    try:
        with open('assets/resume_data.json', 'r') as f:
            data = json.load(f)
        
        # Check skills structure
        logger.info(f"Skills type: {type(data.get('skills', []))}")
        logger.info(f"Skills content: {data.get('skills', [])}")
        
        # Print full structure
        logger.info(f"Full resume data structure: {json.dumps(data, indent=2)}")
    except Exception as e:
        logger.error(f"Error inspecting resume data: {str(e)}")

if __name__ == "__main__":
    inspect_resume_data() 