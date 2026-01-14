#!/usr/bin/env python3
"""
Crawler CLI - Command-Line Interface

Main entry point for crawling operations.
Usage:
    python cli.py crawl --url https://example.com
    python cli.py crawl --file urls.txt
    python cli.py status
    python cli.py reset
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

import click
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from crawler import WebCrawler
from ingest import DocumentIngestor

# =============================================================================
# Configuration
# =============================================================================

console = Console()

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger.add(
    "/app/logs/crawler.log",
    rotation="50 MB",
    retention="7 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
)

# =============================================================================
# CLI Group
# =============================================================================

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """AI RAG Crawler - Web crawling and document ingestion tool."""
    pass

# =============================================================================
# Crawl Command
# =============================================================================

@cli.command()
@click.option("--url", "-u", help="Single URL to crawl")
@click.option("--file", "-f", type=click.Path(exists=True), help="File containing URLs (one per line)")
@click.option("--max-pages", "-m", default=100, help="Maximum pages to crawl per domain")
@click.option("--max-depth", "-d", default=3, help="Maximum crawl depth")
@click.option("--delay", default=1.0, help="Delay between requests (seconds)")
@click.option("--include-pdf", is_flag=True, help="Include PDF files")
@click.option("--include-docs", is_flag=True, help="Include Word/Excel documents")
@click.option("--output", "-o", help="Output directory for downloaded files")
def crawl(
    url: Optional[str],
    file: Optional[str],
    max_pages: int,
    max_depth: int,
    delay: float,
    include_pdf: bool,
    include_docs: bool,
    output: Optional[str],
):
    """
    Crawl websites and ingest content.
    
    Examples:
        crawl --url https://example.com
        crawl --file urls.txt --max-pages 500
        crawl --url https://docs.example.com --include-pdf
    """
    console.print("[bold blue]AI RAG Crawler[/bold blue]")
    console.print()
    
    # Validate input
    if not url and not file:
        console.print("[red]Error: Must provide either --url or --file[/red]")
        sys.exit(1)
    
    # Get URLs
    urls = []
    if url:
        urls.append(url)
    if file:
        with open(file, 'r') as f:
            urls.extend([line.strip() for line in f if line.strip()])
    
    console.print(f"URLs to crawl: {len(urls)}")
    console.print(f"Max pages per domain: {max_pages}")
    console.print(f"Max depth: {max_depth}")
    console.print()
    
    # Initialize crawler
    crawler = WebCrawler(
        max_pages_per_domain=max_pages,
        max_depth=max_depth,
        delay_seconds=delay,
        include_pdf=include_pdf,
        include_docs=include_docs,
    )
    
    # Initialize ingestor
    ingestor = DocumentIngestor()
    
    # Crawl each URL
    total_pages = 0
    total_ingested = 0
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Crawling...", total=len(urls))
        
        for start_url in urls:
            try:
                console.print(f"\n[bold]Crawling: {start_url}[/bold]")
                
                # Crawl
                documents = crawler.crawl(start_url)
                total_pages += len(documents)
                
                console.print(f"Found {len(documents)} documents")
                
                # Ingest
                if documents:
                    console.print("Ingesting to vector database...")
                    ingested = ingestor.ingest_documents(documents)
                    total_ingested += ingested
                    console.print(f"✓ Ingested {ingested} documents")
                
            except Exception as e:
                console.print(f"[red]Error crawling {start_url}: {e}[/red]")
                logger.error(f"Error: {e}", exc_info=True)
            
            progress.update(task, advance=1)
    
    # Summary
    console.print()
    console.print("[bold green]Crawl Complete![/bold green]")
    console.print(f"Total pages crawled: {total_pages}")
    console.print(f"Total documents ingested: {total_ingested}")

# =============================================================================
# Status Command
# =============================================================================

@cli.command()
def status():
    """Show crawler and database status."""
    console.print("[bold blue]AI RAG Crawler Status[/bold blue]")
    console.print()
    
    # Initialize ingestor to check DB
    try:
        ingestor = DocumentIngestor()
        
        # Get collection info
        collection_info = ingestor.get_collection_info()
        
        # Create table
        table = Table(title="Vector Database Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Collection Name", collection_info.get("name", "N/A"))
        table.add_row("Total Documents", str(collection_info.get("points_count", 0)))
        table.add_row("Vector Dimension", str(collection_info.get("vector_size", 0)))
        table.add_row("Status", collection_info.get("status", "unknown"))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error checking status: {e}[/red]")
        sys.exit(1)

# =============================================================================
# Reset Command
# =============================================================================

@cli.command()
@click.confirmation_option(prompt="Are you sure you want to delete all data?")
def reset():
    """Reset database (delete all crawled data)."""
    console.print("[bold yellow]Resetting database...[/bold yellow]")
    
    try:
        ingestor = DocumentIngestor()
        ingestor.reset_collection()
        console.print("[bold green]✓ Database reset complete[/bold green]")
    except Exception as e:
        console.print(f"[red]Error resetting database: {e}[/red]")
        sys.exit(1)

# =============================================================================
# List Command
# =============================================================================

@cli.command()
@click.option("--limit", "-l", default=20, help="Number of documents to show")
def list(limit: int):
    """List crawled documents."""
    console.print("[bold blue]Crawled Documents[/bold blue]")
    console.print()
    
    try:
        ingestor = DocumentIngestor()
        documents = ingestor.list_documents(limit=limit)
        
        if not documents:
            console.print("No documents found")
            return
        
        # Create table
        table = Table()
        table.add_column("URL", style="cyan", no_wrap=False)
        table.add_column("Title", style="green")
        table.add_column("Type", style="yellow")
        
        for doc in documents:
            url = doc.get("url", "N/A")[:60]
            title = doc.get("title", "N/A")[:40]
            doc_type = doc.get("type", "N/A")
            table.add_row(url, title, doc_type)
        
        console.print(table)
        console.print(f"\nShowing {len(documents)} of {limit} documents")
        
    except Exception as e:
        console.print(f"[red]Error listing documents: {e}[/red]")
        sys.exit(1)

# =============================================================================
# Test Command
# =============================================================================

@cli.command()
@click.argument("url")
def test(url: str):
    """Test crawling a single URL (doesn't ingest)."""
    console.print(f"[bold blue]Testing URL: {url}[/bold blue]")
    console.print()
    
    try:
        crawler = WebCrawler(max_pages_per_domain=1, max_depth=1)
        documents = crawler.crawl(url)
        
        if not documents:
            console.print("[yellow]No content extracted[/yellow]")
            return
        
        doc = documents[0]
        
        console.print(f"[green]✓ Successfully crawled[/green]")
        console.print()
        console.print(f"Title: {doc.get('title', 'N/A')}")
        console.print(f"Type: {doc.get('type', 'N/A')}")
        console.print(f"Text length: {len(doc.get('text', ''))} characters")
        console.print()
        console.print("Preview:")
        console.print(doc.get('text', '')[:500] + "...")
        
    except Exception as e:
        console.print(f"[red]Error testing URL: {e}[/red]")
        sys.exit(1)

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    cli()
