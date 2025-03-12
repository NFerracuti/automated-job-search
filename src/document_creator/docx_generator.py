import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any

from docxtpl import DocxTemplate
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DocxGenerator')

class DocxResumeGenerator:
    """Class to generate Word documents from resume data"""
    
    def __init__(self, config_path='config.json', template_path=None):
        # Load config
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Template path
        self.template_path = template_path or os.getenv('RESUME_TEMPLATE_PATH', 'assets/resume_template.docx')
        
        # Set up Google Drive client for uploading documents
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path:
            try:
                self.credentials = service_account.Credentials.from_service_account_file(
                    creds_path, 
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                self.drive_service = build('drive', 'v3', credentials=self.credentials)
                self.use_google_drive = True
                logger.info("Google Drive integration enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Drive: {str(e)}")
                self.use_google_drive = False
        else:
            self.use_google_drive = False
        
        logger.info("Docx Resume Generator initialized")
    
    def _create_basic_resume(self, resume_data):
        """Create a resume document from scratch without using a template"""
        doc = Document()
        
        # Personal info section
        personal = resume_data["personal_info"]
        name = doc.add_paragraph()
        name_run = name.add_run(personal["name"])
        name_run.bold = True
        name_run.font.size = Pt(18)
        name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        contact_info = doc.add_paragraph()
        contact_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_info.add_run(f"{personal['email']} | {personal['phone']} | {personal['location']}")
        
        if personal.get("linkedin") or personal.get("github") or personal.get("portfolio"):
            links = []
            if personal.get("linkedin"):
                links.append(personal["linkedin"])
            if personal.get("github"):
                links.append(personal["github"])
            if personal.get("portfolio"):
                links.append(personal["portfolio"])
            
            links_text = doc.add_paragraph()
            links_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
            links_text.add_run(" | ".join(links))
        
        doc.add_paragraph()  # Spacer
        
        # Summary section
        if resume_data.get("summary"):
            summary_heading = doc.add_heading("Professional Summary", level=2)
            doc.add_paragraph(resume_data["summary"])
        
        # Skills section
        if resume_data.get("skills"):
            skills_heading = doc.add_heading("Skills", level=2)
            
            if isinstance(resume_data["skills"], list):
                skills_text = ", ".join(resume_data["skills"])
                doc.add_paragraph(skills_text)
            elif isinstance(resume_data["skills"], dict):
                for category, skills in resume_data["skills"].items():
                    if skills:
                        skill_para = doc.add_paragraph()
                        skill_para.add_run(f"{category.replace('_', ' ').title()}: ").bold = True
                        skill_para.add_run(", ".join(skills))
        
        # Experience section
        if resume_data.get("experience"):
            exp_heading = doc.add_heading("Professional Experience", level=2)
            
            for job in resume_data["experience"]:
                # Job title and company
                job_heading = doc.add_paragraph()
                job_title = job_heading.add_run(f"{job['title']}, {job['company']}")
                job_title.bold = True
                
                # Location and dates on the same line, right-aligned
                tab_stops = job_heading.paragraph_format.tab_stops
                tab_stops.add_tab_stop(Inches(6.5), WD_ALIGN_PARAGRAPH.RIGHT)
                job_heading.add_run("\t")
                job_heading.add_run(f"{job['location']} | {job['dates']}")
                
                # Job description bullet points
                for bullet in job["description"]:
                    bullet_para = doc.add_paragraph(style='List Bullet')
                    bullet_para.add_run(bullet)
        
        # Education section
        if resume_data.get("education"):
            edu_heading = doc.add_heading("Education", level=2)
            
            for edu in resume_data["education"]:
                # Degree and institution
                edu_heading = doc.add_paragraph()
                degree = edu_heading.add_run(f"{edu['degree']}, {edu['institution']}")
                degree.bold = True
                
                # Location and dates on the same line, right-aligned
                tab_stops = edu_heading.paragraph_format.tab_stops
                tab_stops.add_tab_stop(Inches(6.5), WD_ALIGN_PARAGRAPH.RIGHT)
                edu_heading.add_run("\t")
                edu_heading.add_run(f"{edu['location']} | {edu['dates']}")
                
                # Highlights
                if edu.get("highlights"):
                    for highlight in edu["highlights"]:
                        highlight_para = doc.add_paragraph(style='List Bullet')
                        highlight_para.add_run(highlight)
        
        # Projects section (optional)
        if resume_data.get("projects"):
            projects_heading = doc.add_heading("Projects", level=2)
            
            for project in resume_data["projects"]:
                project_para = doc.add_paragraph()
                project_name = project_para.add_run(f"{project['name']}")
                project_name.bold = True
                
                if project.get("dates"):
                    tab_stops = project_para.paragraph_format.tab_stops
                    tab_stops.add_tab_stop(Inches(6.5), WD_ALIGN_PARAGRAPH.RIGHT)
                    project_para.add_run("\t")
                    project_para.add_run(f"{project['dates']}")
                
                if project.get("description"):
                    desc_para = doc.add_paragraph(style='List Bullet')
                    desc_para.add_run(project["description"])
                
                if project.get("technologies"):
                    tech_para = doc.add_paragraph(style='List Bullet')
                    tech_para.add_run(f"Technologies: {', '.join(project['technologies'])}")
                
                if project.get("url"):
                    url_para = doc.add_paragraph(style='List Bullet')
                    url_para.add_run(f"Link: {project['url']}")
        
        # Certifications section (optional)
        if resume_data.get("certifications"):
            cert_heading = doc.add_heading("Certifications", level=2)
            
            for cert in resume_data["certifications"]:
                cert_para = doc.add_paragraph()
                cert_para.add_run(f"{cert['name']}, {cert['issuer']} ({cert['date']})")
        
        return doc
    
    def _create_template_resume(self, resume_data):
        """Create a resume document using the template"""
        try:
            doc = DocxTemplate(self.template_path)
            context = resume_data.copy()
            
            # Format skills as comma-separated string if it's a list
            if isinstance(context.get("skills"), list):
                context["skills_text"] = ", ".join(context["skills"])
            
            # Add formatting helpers
            context["now"] = datetime.now().strftime("%B %d, %Y")
            
            # Render the template
            doc.render(context)
            return doc
            
        except Exception as e:
            logger.error(f"Error creating resume from template: {str(e)}")
            # Fallback to basic resume
            return self._create_basic_resume(resume_data)
    
    def generate_resume_file(self, resume_data, output_path=None):
        """Generate a resume document and save it to file"""
        try:
            # Create filename if not provided
            if not output_path:
                if resume_data.get("metadata", {}).get("job_title") and resume_data.get("metadata", {}).get("company"):
                    job_title = resume_data["metadata"]["job_title"].replace(" ", "_")
                    company = resume_data["metadata"]["company"].replace(" ", "_")
                    timestamp = datetime.now().strftime("%Y%m%d")
                    
                    # Get name from resume data
                    name = resume_data["personal_info"]["name"].replace(" ", "_")
                    
                    filename = f"{name}_{job_title}_{company}_{timestamp}.docx"
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"resume_{timestamp}.docx"
                
                output_dir = "generated_resumes"
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, filename)
            
            # Generate resume document
            if os.path.exists(self.template_path):
                doc = self._create_template_resume(resume_data)
            else:
                logger.warning(f"Template not found at {self.template_path}, using basic layout")
                doc = self._create_basic_resume(resume_data)
            
            # Save document
            doc.save(output_path)
            logger.info(f"Resume saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating resume file: {str(e)}")
            return None
    
    def upload_to_google_drive(self, file_path):
        """Upload a file to Google Drive and return the URL"""
        if not self.use_google_drive:
            logger.warning("Google Drive integration not enabled")
            return None
        
        try:
            file_name = os.path.basename(file_path)
            
            # Create a folder for resumes if it doesn't exist
            folder_name = "Automated Job Application Resumes"
            folder_id = self._get_or_create_folder(folder_name)
            
            # Upload the file
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            # Set permissions to anyone with the link can view
            self.drive_service.permissions().create(
                fileId=file.get('id'),
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
            
            logger.info(f"Resume uploaded to Google Drive: {file.get('webViewLink')}")
            return file.get('webViewLink')
            
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {str(e)}")
            return None
    
    def _get_or_create_folder(self, folder_name):
        """Get or create a folder in Google Drive"""
        try:
            # Check if folder exists
            results = self.drive_service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            
            # Create folder if it doesn't exist
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
            
        except Exception as e:
            logger.error(f"Error getting/creating folder: {str(e)}")
            raise 