import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from urllib.parse import unquote
from dataclasses import dataclass
import re
import spacy
from minio import Minio
from bs4 import BeautifulSoup
from src.models import WebPageContent
import logging
import os

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
        """
        Merge contact information from another Person object.
        If the same name is found with different roles, favor an executive role over a board role.
        """
        if self.name == other.name:
            if self.role != other.role:
                if self.role in DataReader.EXECUTIVE_ROLES and other.role in DataReader.BOARD_ROLES:
                    pass  # keep current executive role
                elif other.role in DataReader.EXECUTIVE_ROLES and self.role in DataReader.BOARD_ROLES:
                    self.role = other.role
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
    executives: List[Person]
    board_members: List[Person]
    source_file: str

    @property
    def people(self) -> List[Person]:
        """
        Return a combined list of executives and board members.
        This property is provided for backward compatibility.
        """
        return self.executives + self.board_members

    def __str__(self):
        output = []
        output.append(f"URL: {self.url}")
        output.append(f"Title: {self.title}")
        output.append(f"Source File: {self.source_file}\n")
        
        output.append("=== Management Sections ===")
        for section in self.sections:
            output.append(f"\n[{section}]")
            output.append("-" * 50)
            output.append(section)
        
        # Append JSON output for the final executives list.
        output.append("\n\n=== Final Executives List ===")
        if not self.executives:
            output.append("No executives extracted")
        else:
            exec_list = [{"name": p.name, "role": p.role, "contact_info": p.contact_info} for p in self.executives]
            output.append(json.dumps(exec_list, indent=2))
        
        # Append JSON output for the final board members list.
        output.append("\n\n=== Final Board Members List ===")
        if not self.board_members:
            output.append("No board members extracted")
        else:
            board_list = [{"name": p.name, "role": p.role, "contact_info": p.contact_info} for p in self.board_members]
            output.append(json.dumps(board_list, indent=2))
        
        return "\n".join(output)


class DataReader:
    # Define canonical role sets.
    EXECUTIVE_ROLES = {
        "Chief Executive Officer", "Chief Operating Officer", "President", "Vice President",
        "Corporate Secretary", "Chief Financial Officer"
    }
    BOARD_ROLES = {
        "Director", "Chairman", "Board Member"
    }

    def __init__(self, minio_client: Minio, bucket_name: str):
        self.bucket_name = bucket_name
        self.minio_client = minio_client
        self.nlp = spacy.load("en_core_web_sm")
        
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
    
    def is_excluded_url(self, url: str) -> bool:
        """
        Return True if the URL contains any excluded keyword.
        This method filters out URLs such as those with "press-release", "news", "blog", or "announcement".
        """
        excluded_keywords = [
            "press-release", "news", "blog", "announcement", "press", "update", 
            "release", "media", "breaking", "newsroom", "reports", "financial-news", "corporate-news", "projects"
        ]
        return any(kw in url.lower() for kw in excluded_keywords)

    def read_json_file(self, object_name: str) -> Optional[WebPageContent]:
        """
        Read and parse a JSON file from MinIO storage.
        """
        try:
            temp_dir = Path("data/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / "temp.json"
            try:
                self.minio_client.fget_object(self.bucket_name, object_name, str(temp_file))
            except Exception as e:
                logger.error(f"Error downloading file {object_name}: {str(e)}")
                return None
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from {object_name}: {str(e)}")
                return None
            except UnicodeDecodeError:
                try:
                    with open(temp_file, 'r', encoding='latin-1') as f:
                        data = json.load(f)
                except Exception as e2:
                    logger.error(f"Error reading file with alternate encoding {object_name}: {str(e2)}")
                    return None
            finally:
                if temp_file.exists():
                    temp_file.unlink()
            url = unquote(object_name.replace('.json', ''))
            try:
                body_text = self.clean_html(data.get('body_text', ''))
                markdown_content = self.clean_html(data.get('markdown_content', ''))
                if not body_text and not markdown_content and 'content' in data:
                    body_text = self.clean_html(data['content'])
                content = WebPageContent(
                    url=url,
                    body_text=body_text,
                    markdown_content=markdown_content,
                    meta_description=data.get('meta_description'),
                    title=data.get('title'),
                    structured_data=data,
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
        Clean HTML content by removing tags.
        """
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    def get_relevant_sections(self, text: str) -> List[str]:
        """
        Use sentence segmentation to extract sections that mention contact, management, or role keywords.
        """
        doc = self.nlp(text)
        sections = []
        combined_patterns = self.contact_patterns + self.management_patterns + self.role_patterns
        for sent in doc.sents:
            for pattern in combined_patterns:
                if re.search(pattern, sent.text, re.IGNORECASE):
                    sections.append(sent.text)
                    break
        if not sections:
            sections.append(text)
        return sections

    def extract_people_from_section(self, section: str) -> List[Person]:
        """
        Extract Person entities and associated roles from a section.
        """
        people = []
        sent_doc = self.nlp(section)
        for ent in sent_doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                role = None
                best_distance = float('inf')
                for pattern in self.role_patterns:
                    for m in re.finditer(pattern, section, re.IGNORECASE):
                        distance = abs(m.start() - ent.start_char)
                        if distance < best_distance:
                            best_distance = distance
                            role = m.group().strip()
                if role:
                    contact_info = {}
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', section)
                    if email_match:
                        contact_info['email'] = email_match.group()
                    phone_match = re.search(r'(?:\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', section)
                    if phone_match:
                        contact_info['phone'] = phone_match.group()
                    person = Person(name=name, role=role, contact_info=contact_info if contact_info else None)
                    person.standardize_role()
                    people.append(person)
        return people

    def deduplicate_people(self, people: List[Person]) -> List[Person]:
        """
        Deduplicate people by name and merge records.
        """
        deduped = {}
        for person in people:
            if person.name in deduped:
                deduped[person.name].merge_with(person)
            else:
                deduped[person.name] = person
        return list(deduped.values())
    
    def merge_similar_people(self, people: List[Person]) -> List[Person]:
        """
        Further merge entries if one person's name is a substring of another's and they share the same role.
        This helps to combine entries like "Mustapha Elouafi" and "Elouafi".
        """
        merged = []
        used = set()
        for i, p1 in enumerate(people):
            if i in used:
                continue
            for j in range(i+1, len(people)):
                p2 = people[j]
                if p1.role == p2.role:
                    name1 = p1.name.lower().strip()
                    name2 = p2.name.lower().strip()
                    if name1 in name2 or name2 in name1:
                        if len(name1) < len(name2):
                            p1.merge_with(p2)
                            used.add(j)
                        else:
                            p2.merge_with(p1)
                            used.add(j)
            merged.append(p1)
        return merged

    def is_valid_person(self, person: Person) -> bool:
        """
        Filter out entries that are clearly not a person's name.
        This list excludes non-person entries like various mine or resource names, company identifiers, etc.
        """
        excluded_names = [
            "qualified person", "mine", "mines", "silver mine", "gold mine", "copper mine", "zinc mine",
            "ore", "ores", "mineral", "minerals", "mining", "quarry", "deposit", "resource", "resources",
            "exploration", "development", "corporation", "company", "inc", "llc", "limited", "group", "holdings",
            "press", "media", "news", "blog", "announcement", "report", "consultant", "advisor"
        ]
        if any(ex_kw in person.name.lower() for ex_kw in excluded_names):
            return False
        if len(person.name) < 3:
            return False
        return True

    def is_executive_page(self, url: str) -> bool:
        """
        Check if the URL indicates an executive/management page.
        """
        executive_keywords = ["team", "management", "leadership", "executive", "officer"]
        return any(kw in url.lower() for kw in executive_keywords)

    def is_board_page(self, url: str) -> bool:
        """
        Check if the URL indicates a board of directors page.
        """
        board_keywords = ["board", "director", "chairman"]
        return any(kw in url.lower() for kw in board_keywords)

    def categorize_people(self, people: List[Person], url: str) -> Tuple[List[Person], List[Person]]:
        """
        Categorize deduplicated people into executives and board members based on role and URL context.
        A person may appear in both lists if, for example, the CEO also serves on the board.
        """
        executives = []
        board_members = []
        is_exec_page = self.is_executive_page(url)
        is_board_page = self.is_board_page(url)
        
        for person in people:
            if not self.is_valid_person(person):
                continue

            in_exec_role = person.role in self.EXECUTIVE_ROLES
            in_board_role = person.role in self.BOARD_ROLES

            if is_exec_page and not is_board_page:
                if in_exec_role:
                    executives.append(person)
                else:
                    executives.append(person)
            elif is_board_page and not is_exec_page:
                if in_board_role:
                    board_members.append(person)
                else:
                    board_members.append(person)
            else:
                if in_exec_role:
                    executives.append(person)
                if in_board_role:
                    board_members.append(person)
                if in_exec_role and person.role == "Chief Executive Officer":
                    if person not in board_members:
                        board_members.append(person)
                        
        return executives, board_members

    def process_content(self, content: WebPageContent) -> ProcessedContent:
        """
        Process webpage content to extract, deduplicate, filter, and categorize management information.
        If the URL is excluded (e.g., contains "press-release", "news", "blog", or "announcement"),
        return a ProcessedContent with empty lists.
        """
        if self.is_excluded_url(content.url):
            logger.info(f"URL excluded from processing: {content.url}")
            return ProcessedContent(
                url=content.url,
                title=content.title,
                sections=[],
                executives=[],
                board_members=[],
                source_file=content.source_file
            )
        
        text = content.body_text
        if not text and content.structured_data:
            sections_data = content.structured_data.get('sections')
            if sections_data:
                if isinstance(sections_data, dict):
                    text = ' '.join(str(v) for v in sections_data.values())
                elif isinstance(sections_data, list):
                    text = ' '.join(str(s) for s in sections_data)
                else:
                    text = str(sections_data)
                    
        if not text:
            return ProcessedContent(
                url=content.url,
                title=content.title,
                sections=[],
                executives=[],
                board_members=[],
                source_file=content.source_file
            )
        
        sections_to_process = self.get_relevant_sections(text)
        all_people = []
        for section in sections_to_process:
            all_people.extend(self.extract_people_from_section(section))
        
        deduped_people = self.deduplicate_people(all_people)
        merged_people = self.merge_similar_people(deduped_people)
        filtered_people = [p for p in merged_people if self.is_valid_person(p)]
        executives, board_members = self.categorize_people(filtered_people, content.url)
        
        logger.debug("Debug - Executives: " + ", ".join(f"{p.name} ({p.role})" for p in executives))
        logger.debug("Debug - Board Members: " + ", ".join(f"{p.name} ({p.role})" for p in board_members))
        
        return ProcessedContent(
            url=content.url,
            title=content.title,
            sections=sections_to_process,
            executives=executives,
            board_members=board_members,
            source_file=content.source_file
        )

    def read_json_files(self, working_dir: str) -> List[Dict[str, Any]]:
        """Read all JSON files from the working directory."""
        results = []
        try:
            for file in os.listdir(working_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(working_dir, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            results.append(data)
                    except Exception as e:
                        logger.error(f"Error reading file {file}: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading directory {working_dir}: {str(e)}")
        return results
