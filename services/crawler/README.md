# Crawler Service

Web crawling and document ingestion service for the AI RAG system.

## What This Service Does

1. **Web Crawling** - Discovers and downloads web pages
2. **Content Parsing** - Extracts text from HTML, PDF, Word, Excel
3. **Table Extraction** - Parses HTML tables into structured data
4. **Document Ingestion** - Chunks, embeds, and stores in Qdrant

## Key Features

### Intelligent Crawling
- Depth limits (avoid infinite loops)
- Rate limiting (polite crawling)
- Domain scoping (stays on same site)
- Link filtering (skips login, downloads)
- Sitemap support

### Multi-Format Parsing
- **HTML**: Main content extraction, table parsing
- **PDF**: Multi-page text extraction
- **Word (.docx)**: Paragraphs and tables
- **Excel (.xlsx)**: All sheets

### Table Parsing (Important!)
Automatically detects and extracts rate tables:
```
HTML table → Structured data → Searchable in Qdrant
```

Example:
```
| Location    | Rate |
|-------------|------|
| Denver, CO  | $91  |

Becomes:
{location: "Denver, CO", rate: "$91", type: "location_rate"}
```

## CLI Usage

```bash
# Crawl a website
python cli.py crawl --url https://example.com/docs

# Crawl from file
python cli.py crawl --file urls.txt --max-pages 500

# Include PDFs
python cli.py crawl --url https://docs.example.com --include-pdf

# Test a single page
python cli.py test https://example.com

# Check status
python cli.py status

# List documents
python cli.py list --limit 50

# Reset database
python cli.py reset
```

## Via Docker Compose

```bash
# From project root
docker compose run --rm crawler python /app/cli.py crawl \
  --url https://example.com

# Or use the Makefile
make crawl URL=https://example.com
```

## Document Processing Pipeline

```
1. Fetch URL
   ↓
2. Parse content (HTML/PDF/DOCX)
   ↓
3. Extract tables (if HTML)
   ↓
4. Chunk text (512 chars, 50 overlap)
   ↓
5. Generate embeddings (384-dim vectors)
   ↓
6. Store in Qdrant
```

## Configuration

Set via environment variables:

- `QDRANT_URL` - Vector database URL
- `QDRANT_COLLECTION` - Collection name
- `EMBEDDING_MODEL` - Embedding model (default: all-MiniLM-L6-v2)
- `MAX_PAGES_PER_DOMAIN` - Crawl limit
- `MAX_DEPTH` - Maximum depth from start URL

## Parsers

### HTMLParser
- Extracts main content
- Removes navigation, scripts, styles
- Parses tables
- Extracts metadata

### TableParser
- Detects rate tables
- Extracts headers and rows
- Identifies location-rate pairs
- Converts to structured data

### PDFParser
- Multi-page extraction
- Metadata reading
- Clean text output

### DocumentParser
- Word (.docx) support
- Excel (.xlsx) support
- Table extraction

## Dependencies

- beautifulsoup4, lxml - HTML parsing
- pypdf - PDF parsing
- python-docx, openpyxl - Document parsing
- sentence-transformers - Embeddings
- qdrant-client - Vector storage
- click, rich - CLI interface

## Example: Crawling Rate Tables

```bash
# 1. Crawl a site with rate tables
python cli.py crawl --url https://example.com/rates

# 2. Tables are automatically parsed:
#    - HTML tables detected
#    - Headers/rows extracted
#    - Rate data identified
#    - Stored as structured data

# 3. Now queries work with fuzzy matching:
#    "Denver" → finds "Denver, CO" → returns $91
```

## Generalized (Not BYU-Specific)

This crawler works for any website:
- Corporate knowledge bases
- Documentation sites
- Support articles
- Product catalogs
- Research papers

NO hardcoded BYU logic!

---

**Part of AI RAG Batch 4**  
**Status**: Complete ✅  
**Next**: Frontend (Batch 5)
