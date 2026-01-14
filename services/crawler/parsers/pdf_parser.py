"""
PDF Parser - Parse PDF documents

Extracts text from PDF files.
"""

from io import BytesIO
from typing import Dict, Any, Optional

from pypdf import PdfReader
from loguru import logger

from .base import BaseParser


class PDFParser(BaseParser):
    """
    Parse PDF documents.
    
    Extracts text content from PDFs.
    """
    
    def parse(self, content: bytes, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse PDF content.
        
        Args:
            content: PDF bytes
            url: Source URL
            
        Returns:
            Parsed document
        """
        try:
            # Create PDF reader
            pdf_file = BytesIO(content)
            reader = PdfReader(pdf_file)
            
            # Extract metadata
            metadata = self._extract_metadata(reader)
            
            # Extract title
            title = metadata.get("title", "") or self._guess_title_from_url(url)
            
            # Extract text from all pages
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            full_text = "\n\n".join(text_parts)
            
            # Clean text
            full_text = self._clean_text(full_text)
            
            # Create document
            doc = self._create_document(
                text=full_text,
                title=title,
                url=url,
                doc_type="pdf",
                metadata={
                    **metadata,
                    "page_count": len(reader.pages),
                },
            )
            
            return doc
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            return None
    
    def _extract_metadata(self, reader: PdfReader) -> Dict[str, Any]:
        """Extract PDF metadata."""
        metadata = {}
        
        if reader.metadata:
            if reader.metadata.title:
                metadata["title"] = reader.metadata.title
            if reader.metadata.author:
                metadata["author"] = reader.metadata.author
            if reader.metadata.subject:
                metadata["subject"] = reader.metadata.subject
            if reader.metadata.creator:
                metadata["creator"] = reader.metadata.creator
        
        return metadata
    
    def _guess_title_from_url(self, url: str) -> str:
        """Guess title from URL filename."""
        # Extract filename
        parts = url.split("/")
        filename = parts[-1] if parts else "Untitled"
        
        # Remove extension
        if "." in filename:
            filename = ".".join(filename.split(".")[:-1])
        
        # Replace underscores/hyphens with spaces
        filename = filename.replace("_", " ").replace("-", " ")
        
        # Title case
        return filename.title()
