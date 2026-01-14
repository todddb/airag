"""
HTML Parser - Parse HTML pages

Extracts text, titles, and structure from HTML.
Handles tables and structured content.
"""

from typing import Dict, Any, Optional, List

from bs4 import BeautifulSoup, Tag
from loguru import logger

from .base import BaseParser
from .table_parser import TableParser


class HTMLParser(BaseParser):
    """
    Parse HTML content.
    
    Extracts:
    - Main text content
    - Title
    - Tables (as structured data)
    - Metadata (description, etc.)
    """
    
    def __init__(self):
        """Initialize HTML parser."""
        self.table_parser = TableParser()
    
    def parse(self, content: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse HTML content.
        
        Args:
            content: HTML string
            url: Source URL
            
        Returns:
            Parsed document
        """
        try:
            soup = BeautifulSoup(content, "html.parser")
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract text
            text = self._extract_text(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup)
            
            # Extract tables
            tables = self._extract_tables(soup)
            
            # Create document
            doc = self._create_document(
                text=text,
                title=title,
                url=url,
                doc_type="html",
                metadata=metadata,
                structured_data={"tables": tables} if tables else None,
            )
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try <title> tag
        if soup.title:
            return soup.title.string or ""
        
        # Try <h1>
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        return "Untitled"
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """
        Extract main text content.
        
        Removes scripts, styles, navigation, etc.
        """
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        # Try to find main content
        main_content = soup.find("main") or soup.find("article") or soup.find("body")
        
        if not main_content:
            main_content = soup
        
        # Extract text
        text = main_content.get_text(separator="\n", strip=True)
        
        # Clean
        text = self._clean_text(text)
        
        return text
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML."""
        metadata = {}
        
        # Description meta tag
        desc = soup.find("meta", attrs={"name": "description"})
        if desc and desc.get("content"):
            metadata["description"] = desc["content"]
        
        # Keywords meta tag
        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords and keywords.get("content"):
            metadata["keywords"] = keywords["content"]
        
        # Author meta tag
        author = soup.find("meta", attrs={"name": "author"})
        if author and author.get("content"):
            metadata["author"] = author["content"]
        
        # Open Graph meta tags
        og_title = soup.find("meta", property="og:title")
        if og_title:
            metadata["og_title"] = og_title.get("content", "")
        
        return metadata
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract and parse tables."""
        tables = []
        
        for table_elem in soup.find_all("table"):
            try:
                table_data = self.table_parser.parse_table(table_elem)
                if table_data:
                    tables.append(table_data)
            except Exception as e:
                logger.debug(f"Error parsing table: {e}")
        
        return tables
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content using heuristics.
        
        Tries to identify the main content area.
        """
        # Try common content containers
        content_selectors = [
            "main",
            "article",
            ".content",
            ".main-content",
            "#content",
            "#main",
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(separator="\n", strip=True)
        
        # Fallback to body
        return soup.body.get_text(separator="\n", strip=True) if soup.body else ""
