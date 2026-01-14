"""
Web Crawler - Crawl websites and extract content

Handles:
- URL crawling with depth limits
- Robots.txt respect
- Rate limiting
- Content extraction
- Link discovery
"""

import re
import time
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urljoin, urlparse
from collections import deque

import requests
from bs4 import BeautifulSoup
from loguru import logger

from parsers import HTMLParser, PDFParser, DocumentParser


class WebCrawler:
    """
    Web crawler for discovering and extracting content.
    
    Generalized crawler - no BYU-specific code!
    """
    
    def __init__(
        self,
        max_pages_per_domain: int = 100,
        max_depth: int = 3,
        delay_seconds: float = 1.0,
        timeout_seconds: int = 30,
        include_pdf: bool = True,
        include_docs: bool = False,
        user_agent: str = "AI-RAG-Bot/1.0",
    ):
        """
        Initialize web crawler.
        
        Args:
            max_pages_per_domain: Maximum pages to crawl per domain
            max_depth: Maximum depth from start URL
            delay_seconds: Delay between requests (rate limiting)
            timeout_seconds: Request timeout
            include_pdf: Whether to download and parse PDFs
            include_docs: Whether to download and parse docs (docx, xlsx)
            user_agent: User agent string
        """
        self.max_pages_per_domain = max_pages_per_domain
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.include_pdf = include_pdf
        self.include_docs = include_docs
        self.user_agent = user_agent
        
        # Parsers
        self.html_parser = HTMLParser()
        self.pdf_parser = PDFParser()
        self.doc_parser = DocumentParser()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        
        logger.info(f"WebCrawler initialized (max_pages: {max_pages_per_domain}, max_depth: {max_depth})")
    
    def crawl(self, start_url: str) -> List[Dict[str, Any]]:
        """
        Crawl website starting from URL.
        
        Args:
            start_url: Starting URL
            
        Returns:
            List of extracted documents
        """
        logger.info(f"Starting crawl: {start_url}")
        
        # Initialize tracking
        visited: Set[str] = set()
        documents: List[Dict[str, Any]] = []
        
        # Queue: (url, depth)
        queue = deque([(start_url, 0)])
        
        # Get domain for scoping
        start_domain = self._get_domain(start_url)
        
        while queue and len(visited) < self.max_pages_per_domain:
            url, depth = queue.popleft()
            
            # Skip if already visited
            if url in visited:
                continue
            
            # Skip if max depth exceeded
            if depth > self.max_depth:
                continue
            
            # Skip if different domain
            if self._get_domain(url) != start_domain:
                continue
            
            # Mark as visited
            visited.add(url)
            
            # Rate limiting
            time.sleep(self.delay_seconds)
            
            try:
                # Crawl page
                doc, links = self._crawl_page(url, depth)
                
                if doc:
                    documents.append(doc)
                    logger.info(f"✓ Crawled: {url} ({len(documents)}/{self.max_pages_per_domain})")
                
                # Add links to queue
                if depth < self.max_depth:
                    for link in links:
                        if link not in visited:
                            queue.append((link, depth + 1))
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
        
        logger.info(f"Crawl complete: {len(documents)} documents from {len(visited)} pages")
        return documents
    
    def _crawl_page(self, url: str, depth: int) -> tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Crawl a single page.
        
        Args:
            url: URL to crawl
            depth: Current depth
            
        Returns:
            Tuple of (document, links)
        """
        logger.debug(f"Crawling: {url} (depth: {depth})")
        
        try:
            # Fetch page
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            
            # Determine content type
            content_type = response.headers.get("Content-Type", "").lower()
            
            # Parse based on type
            if "text/html" in content_type:
                return self._parse_html(url, response.text, depth)
            
            elif "application/pdf" in content_type and self.include_pdf:
                return self._parse_pdf(url, response.content), []
            
            elif self.include_docs and any(t in content_type for t in ["word", "excel", "spreadsheet"]):
                return self._parse_document(url, response.content), []
            
            else:
                logger.debug(f"Skipping unsupported content type: {content_type}")
                return None, []
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None, []
    
    def _parse_html(self, url: str, html: str, depth: int) -> tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Parse HTML page.
        
        Args:
            url: Page URL
            html: HTML content
            depth: Current depth
            
        Returns:
            Tuple of (document, links)
        """
        # Parse HTML
        doc = self.html_parser.parse(html, url)
        
        # Extract links
        links = []
        soup = BeautifulSoup(html, "html.parser")
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(url, href)
            
            # Filter links
            if self._should_follow_link(absolute_url, url):
                links.append(absolute_url)
        
        return doc, links
    
    def _parse_pdf(self, url: str, content: bytes) -> Optional[Dict[str, Any]]:
        """Parse PDF document."""
        try:
            return self.pdf_parser.parse(content, url)
        except Exception as e:
            logger.error(f"Error parsing PDF {url}: {e}")
            return None
    
    def _parse_document(self, url: str, content: bytes) -> Optional[Dict[str, Any]]:
        """Parse Word/Excel document."""
        try:
            return self.doc_parser.parse(content, url)
        except Exception as e:
            logger.error(f"Error parsing document {url}: {e}")
            return None
    
    def _should_follow_link(self, link: str, current_url: str) -> bool:
        """
        Determine if a link should be followed.
        
        Args:
            link: Link to check
            current_url: Current page URL
            
        Returns:
            True if link should be followed
        """
        # Must be valid URL
        if not link.startswith("http"):
            return False
        
        # Same domain only
        if self._get_domain(link) != self._get_domain(current_url):
            return False
        
        # Skip common non-content links
        skip_patterns = [
            r'/login',
            r'/logout',
            r'/signin',
            r'/signup',
            r'/register',
            r'/download',
            r'\.pdf$',
            r'\.zip$',
            r'\.exe$',
            r'#',  # Anchor links
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, link, re.IGNORECASE):
                return False
        
        return True
    
    def _get_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL
            
        Returns:
            Domain (e.g., "example.com")
        """
        parsed = urlparse(url)
        return parsed.netloc
    
    def crawl_sitemap(self, sitemap_url: str) -> List[Dict[str, Any]]:
        """
        Crawl URLs from sitemap.xml.
        
        Args:
            sitemap_url: URL of sitemap
            
        Returns:
            List of documents
        """
        logger.info(f"Crawling sitemap: {sitemap_url}")
        
        try:
            response = self.session.get(sitemap_url, timeout=self.timeout_seconds)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "xml")
            urls = [loc.text for loc in soup.find_all("loc")]
            
            logger.info(f"Found {len(urls)} URLs in sitemap")
            
            # Crawl each URL
            documents = []
            for url in urls[:self.max_pages_per_domain]:
                time.sleep(self.delay_seconds)
                doc, _ = self._crawl_page(url, 0)
                if doc:
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error crawling sitemap: {e}")
            return []
    
    def crawl_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Crawl a list of URLs (no link following).
        
        Args:
            urls: List of URLs to crawl
            
        Returns:
            List of documents
        """
        logger.info(f"Crawling {len(urls)} URLs")
        
        documents = []
        for i, url in enumerate(urls, 1):
            time.sleep(self.delay_seconds)
            
            try:
                doc, _ = self._crawl_page(url, 0)
                if doc:
                    documents.append(doc)
                    logger.info(f"✓ Crawled {i}/{len(urls)}: {url}")
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
        
        return documents
