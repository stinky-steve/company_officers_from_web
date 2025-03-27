import json
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import unquote
from dataclasses import dataclass
import re
import spacy
from langdetect import detect
from minio import Minio
from bs4 import BeautifulSoup
from src.models import WebPageContent
import logging

logger = logging.getLogger(__name__)

@dataclass
class Person:
    name: str
    role: str
    contact_info: Optional[Dict[str, str]] = None
    
    def standardize_role(self):
        """Standardize role names to common formats."""
        role_mapping = {
            r'^[Cc][Ee][Oo]$': 'Chief Executive Officer',
            r'^[Cc][Ff][Oo]$': 'Chief Financial Officer',
            r'^[Cc][Oo][Oo]$': 'Chief Operating Officer',
            r'^[Vv][Pp]$': 'Vice President',
            r'^[Ii][Rr]$': 'Investor Relations',
            r'^[Dd]irector$': 'Director',
            r'^[Pp]resident$': 'President',
            r'^[Cc]hairman$': 'Chairman',
            r'^[Cc]hairperson$': 'Chairman',
            r'^[Tt]reasurer$': 'Treasurer',
            r'^[Ss]ecretary$': 'Secretary'
        }
        
        for pattern, standard in role_mapping.items():
            if re.match(pattern, self.role.strip()):
                self.role = standard
                break
    
    def merge_with(self, other: 'Person') -> None:
        """Merge contact information from another Person object."""
        if self.name == other.name and self.role == other.role:
            if other.contact_info:
                if not self.contact_info:
                    self.contact_info = {}
                self.contact_info.update(other.contact_info)
    
    def __eq__(self, other):
        if not isinstance(other, Person):
            return False
        return self.name == other.name and self.role == other.role
    
    def __hash__(self):
        return hash((self.name, self.role))

@dataclass 
class ProcessedContent:
    url: str
    title: str
    sections: List[str]
    people: List['Person']
    source_file: str
    
    def __str__(self):
        output = []
        output.append(f"URL: {self.url}")
        output.append(f"Title: {self.title}")
        output.append(f"Source File: {self.source_file}\n")
        
        output.append("=== Management Sections ===\n")
        for section in self.sections:
            output.append(f"[{section}]")
            output.append("-" * 50)
            output.append(section)
            output.append("\n")
            
        output.append("=== Extracted People ===")
        if not self.people:
            output.append("No people extracted")
        else:
            for person in self.people:
                output.append(f"\nName: {person.name}")
                output.append(f"Role: {person.role}")
                if person.contact_info:
                    output.append("Contact Info:")
                    for key, value in person.contact_info.items():
                        output.append(f"  {key}: {value}")
        
        return "\n".join(output)

class DataReader:
    def __init__(self, minio_service: Minio, bucket: str):
        self.minio_service = minio_service
        self.bucket = bucket
        # Initialize spaCy model
        self.nlp = spacy.load("en_core_web_sm")
        
        # Define regex patterns
        self.contact_patterns = [
            r"Corporate\s+[Oo]ffice",
            r"[Ii]nvestor\s+[Rr]elations\s+[Cc]ontact",
            r"[Cc]ontact\s+[Ii]nformation",
            r"[Cc]ontact\s+[Uu]s",
            r"[Cc]orporate\s+[Cc]ontacts?"
        ]
        
        self.management_patterns = [
            r"[Bb]oard\s+of\s+[Dd]irectors",
            r"[Ee]xecutive\s+[Tt]eam",
            r"[Mm]anagement\s+[Tt]eam",
            r"[Ll]eadership\s+[Tt]eam",
            r"[Ss]enior\s+[Mm]anagement",
            r"[Oo]fficers",
            r"[Dd]irectors"
        ]
        
        self.role_patterns = [
            r"[Cc][Ee][Oo]",
            r"[Cc]hief\s+[Ee]xecutive\s+[Oo]fficer",
            r"[Cc][Ff][Oo]",
            r"[Cc]hief\s+[Ff]inancial\s+[Oo]fficer",
            r"[Cc][Oo][Oo]",
            r"[Cc]hief\s+[Oo]perating\s+[Oo]fficer",
            r"[Pp]resident",
            r"[Dd]irector",
            r"[Cc]hairman",
            r"[Cc]hairperson",
            r"[Vv]ice\s+[Pp]resident",
            r"[Tt]reasurer",
            r"[Ss]ecretary",
            r"[Ii]nvestor\s+[Rr]elations",
            r"[Cc]orporate\s+[Ss]ecretary",
            r"[Cc]orporate\s+[Cc]ommunications",
            r"[Cc]orporate\s+[Dd]evelopment",
            r"[Cc]orporate\s+[Aa]ffairs",
            r"[Cc]orporate\s+[Rr]elations",
            r"[Cc]orporate\s+[Cc]ontact",
            r"[Cc]ontact\s+[Pp]erson",
            r"[Cc]ontact\s+[Rr]epresentative"
        ]

    def read_json_file(self, object_name: str) -> Optional[WebPageContent]:
        """
        Read and parse a JSON file from MinIO storage.
        
        Args:
            object_name: Name of the object (file) in MinIO bucket
            
        Returns:
            WebPageContent object if successful, None if parsing fails
        """
        try:
            # Create a temporary file to store the downloaded content
            temp_dir = Path("data/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / "temp.json"
            
            # Download the file from MinIO
            try:
                self.minio_service.client.fget_object(
                    self.bucket,
                    object_name,
                    str(temp_file)
                )
            except Exception as e:
                logger.error(f"Error downloading file {object_name}: {str(e)}")
                return None
            
            # Read and parse the JSON file
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from {object_name}: {str(e)}")
                return None
            except UnicodeDecodeError as e:
                # Try with a different encoding
                try:
                    with open(temp_file, 'r', encoding='latin-1') as f:
                        data = json.load(f)
                except Exception as e2:
                    logger.error(f"Error reading file with alternate encoding {object_name}: {str(e2)}")
                    return None
            finally:
                # Clean up temporary file
                if temp_file.exists():
                    temp_file.unlink()
            
            # Extract URL from filename (it's URL-encoded in the filename)
            url = unquote(object_name.replace('.json', ''))
            
            # Clean HTML content if present
            try:
                body_text = self.clean_html(data.get('body_text', ''))
                markdown_content = self.clean_html(data.get('markdown_content', ''))
                
                # If both body_text and markdown_content are empty, try content field
                if not body_text and not markdown_content and 'content' in data:
                    body_text = self.clean_html(data['content'])
                
                # Create WebPageContent object with structured data
                content = WebPageContent(
                    url=url,
                    body_text=body_text,
                    markdown_content=markdown_content,
                    meta_description=data.get('meta_description'),
                    title=data.get('title'),
                    structured_data=data,  # Pass the entire data object as structured_data
                    source_file=object_name
                )
                
                return content
                
            except Exception as e:
                logger.error(f"Error processing content from {object_name}: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Unexpected error reading file {object_name}: {str(e)}")
            return None

    def clean_html(self, html: str) -> str:
        """
        Clean HTML content by removing tags and converting HTML entities to their corresponding characters.
        
        Args:
            html: HTML content to clean
            
        Returns:
            Cleaned text
        """
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    def process_content(self, content: WebPageContent) -> ProcessedContent:
        """Process webpage content to extract management information.
        
        Args:
            content (WebPageContent): The webpage content to process
            
        Returns:
            ProcessedContent: The processed content with extracted people and their roles
        """
        text = content.body_text
        if not text and content.structured_data:
            if 'sections' in content.structured_data:
                sections = content.structured_data['sections']
                if isinstance(sections, dict):
                    text = ' '.join(str(v) for v in sections.values())
                elif isinstance(sections, list):
                    text = ' '.join(str(s) for s in sections)
                else:
                    text = str(sections)

        if not text:
            return ProcessedContent(
                url=content.url, 
                title=content.title, 
                sections=[],
                people=[],
                source_file=content.source_file
            )

        # Initialize spaCy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)

        # First pass - find contact sections
        contact_sections = []
        for pattern in self.contact_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                contact_sections.append(text[start:end])

        # Second pass - find management sections and roles
        management_sections = []
        for pattern in self.role_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                management_sections.append(text[start:end])

        # Process all sections to extract people
        people_dict = {}  # Use dict to handle duplicates
        sections_to_process = contact_sections + management_sections
        
        if not sections_to_process:
            sections_to_process = [text]  # Process entire text if no sections found

        for section in sections_to_process:
            section_doc = nlp(section)
            
            # Extract names (PERSON entities)
            for ent in section_doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text.strip()
                    
                    # Find role near the name
                    role = None
                    context_start = max(0, ent.start_char - 100)
                    context_end = min(len(section), ent.end_char + 100)
                    context = section[context_start:context_end]
                    
                    for pattern in self.role_patterns:
                        role_match = re.search(pattern, context, re.IGNORECASE)
                        if role_match:
                            role = role_match.group().strip()
                            break
                    
                    # Find contact info near the name
                    contact_info = {}
                    
                    # Look for email
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', context)
                    if email_match:
                        contact_info['email'] = email_match.group()
                        
                    # Look for phone numbers
                    phone_match = re.search(r'(?:\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', context)
                    if phone_match:
                        contact_info['phone'] = phone_match.group()
                    
                    # Create Person object if we found a role
                    if role:
                        person = Person(name=name, role=role, contact_info=contact_info if contact_info else None)
                        person.standardize_role()
                        
                        # Use name+role as key to handle duplicates
                        key = (person.name, person.role)
                        if key in people_dict:
                            people_dict[key].merge_with(person)
                        else:
                            people_dict[key] = person

        # Convert dict values to list
        people = list(people_dict.values())
        
        # Sort people by name
        people.sort(key=lambda x: x.name)

        return ProcessedContent(
            url=content.url, 
            title=content.title, 
            sections=sections_to_process,
            people=people,
            source_file=content.source_file
        )