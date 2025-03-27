"""Models for the web page data processing."""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class WebPageContent:
    """Class representing the content of a web page."""
    url: str
    body_text: str
    markdown_content: str
    meta_description: Optional[str] = None
    title: Optional[str] = None
    structured_data: Optional[Dict] = None
    source_file: Optional[str] = None
