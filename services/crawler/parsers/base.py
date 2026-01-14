"""
Base Parser - Abstract base class for all parsers

Defines the interface that all parsers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseParser(ABC):
    """
    Abstract base class for content parsers.
    
    All parsers must implement the parse() method.
    """
    
    @abstractmethod
    def parse(self, content: Any, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse content and extract structured data.
        
        Args:
            content: Raw content (varies by parser type)
            url: Source URL
            
        Returns:
            Parsed document dict with keys:
                - text: Main text content
                - title: Document title
                - url: Source URL
                - type: Content type
                - metadata: Additional metadata
                - structured_data: Optional structured data
        """
        pass
    
    def _create_document(
        self,
        text: str,
        title: str,
        url: str,
        doc_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        structured_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create standardized document structure.
        
        Args:
            text: Main text content
            title: Document title
            url: Source URL
            doc_type: Type of document
            metadata: Additional metadata
            structured_data: Structured data extracted
            
        Returns:
            Document dict
        """
        doc = {
            "text": text.strip(),
            "title": title.strip() if title else "Untitled",
            "url": url,
            "type": doc_type,
            "metadata": metadata or {},
        }
        
        if structured_data:
            doc["structured_data"] = structured_data
        
        return doc
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text content.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove multiple spaces
        text = " ".join(text.split())
        
        # Remove multiple newlines
        text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
        
        return text
