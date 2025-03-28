"""Service for handling website scraping operations."""

import time
import requests
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class WebService:
    """Service for handling website scraping operations."""
    
    def __init__(self, rate_limit: float = 1.0):
        """Initialize the web service.
        
        Args:
            rate_limit: Minimum time between requests in seconds
        """
        self.rate_limit = rate_limit
        self.last_request = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _wait_for_rate_limit(self):
        """Wait to respect rate limiting."""
        now = time.time()
        time_since_last = now - self.last_request
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.last_request = time.time()
    
    def get_page_content(self, url: str) -> Optional[str]:
        """Get the content of a webpage.
        
        Args:
            url: URL to fetch
            
        Returns:
            Page content if successful, None otherwise
        """
        try:
            self._wait_for_rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None
    
    def get_management_pages(self, base_url: str) -> list[str]:
        """Get URLs of pages likely to contain management information.
        
        Args:
            base_url: Company website base URL
            
        Returns:
            List of relevant page URLs
        """
        content = self.get_page_content(base_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        management_urls = []
        
        # Keywords that might indicate management/board pages
        keywords = [
            'management', 'leadership', 'team', 'board', 'directors',
            'governance', 'about', 'company', 'corporate', 'executives'
        ]
        
        # Find links containing keywords
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().lower()
            
            # Check if link text or URL contains keywords
            if any(keyword in text or keyword in href.lower() for keyword in keywords):
                full_url = urljoin(base_url, href)
                if full_url.startswith(base_url):  # Only include internal links
                    management_urls.append(full_url)
        
        return list(set(management_urls))  # Remove duplicates
    
    def get_website_content(self, url: str) -> Optional[str]:
        """Get all relevant content from a company website.
        
        Args:
            url: Company website URL
            
        Returns:
            Combined content from relevant pages if successful, None otherwise
        """
        # Get management-related page URLs
        management_urls = self.get_management_pages(url)
        if not management_urls:
            print(f"No management pages found for {url}")
            return None
        
        # Fetch content from each page
        all_content = []
        for page_url in management_urls:
            content = self.get_page_content(page_url)
            if content:
                # Parse HTML and extract text
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for element in soup(['script', 'style']):
                    element.decompose()
                
                # Get text content
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                all_content.append(text)
        
        if not all_content:
            print(f"No content extracted from {url}")
            return None
        
        return '\n\n'.join(all_content) 