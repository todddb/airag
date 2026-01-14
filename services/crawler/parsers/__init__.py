"""
Parsers Package

Content parsers for different file types:
- HTMLParser: HTML pages
- PDFParser: PDF documents
- DocumentParser: Word/Excel files
- TableParser: HTML tables (for structured data)
"""

from .base import BaseParser
from .html_parser import HTMLParser
from .pdf_parser import PDFParser
from .document_parser import DocumentParser
from .table_parser import TableParser

__all__ = [
    "BaseParser",
    "HTMLParser",
    "PDFParser",
    "DocumentParser",
    "TableParser",
]

__version__ = "1.0.0"
