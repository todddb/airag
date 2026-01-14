# Documentation

Complete documentation for the AI RAG system.

## Quick Links

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment guide (local, cloud, production) |
| [API.md](API.md) | API reference documentation |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Development guide |
| [FAQ.md](FAQ.md) | Frequently asked questions |

## Getting Started

**New users**: Start with the main README in the project root, then:
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system
2. Follow [DEPLOYMENT.md](DEPLOYMENT.md) - Get it running
3. Check [FAQ.md](FAQ.md) - Common questions

**Developers**: Go to [DEVELOPMENT.md](DEVELOPMENT.md)

**API users**: See [API.md](API.md)

## Document Overview

### ARCHITECTURE.md

**Complete system architecture**

Topics covered:
- System overview and components
- Dual-LLM architecture explanation
- Data flow diagrams
- Technology stack
- Design decisions (why no regex!)
- Scaling considerations
- Performance characteristics

**Read this to understand HOW the system works.**

### DEPLOYMENT.md

**Deployment in any environment**

Topics covered:
- Quick start guide
- Local development setup
- Production deployment
- Cloud deployment (AWS, GCP, Azure)
- SSL/TLS configuration
- Monitoring and backups
- Troubleshooting

**Read this to GET the system running.**

### API.md

**Complete API reference**

Topics covered:
- Orchestrator API endpoints
- Worker API endpoints
- Request/response formats
- Common patterns
- Error handling
- Code examples (Python, cURL)

**Read this to INTEGRATE with the system.**

### DEVELOPMENT.md

**Developer guide**

Topics covered:
- Development environment setup
- Project structure
- Code style guidelines
- Testing procedures
- Common development tasks
- Contributing guidelines

**Read this to CONTRIBUTE to the system.**

### FAQ.md

**Frequently asked questions**

Topics covered:
- General questions
- Setup questions
- Usage questions
- Technical questions
- Troubleshooting
- Best practices

**Read this for QUICK ANSWERS.**

## Key Concepts

### Dual-LLM Architecture

The system uses TWO LLMs:
- **Orchestrator** (qwen2.5:14b): Fast classification
- **Worker** (qwen2.5:32b): Detailed generation

**Why?** Best balance of speed and quality.

### No Regex!

Unlike traditional systems (like your BYU policy tool), AI RAG uses:
- LLM-based intent classification
- Fuzzy matching with confidence scores
- Natural language understanding

**Result**: Handles variations, typos, abbreviations naturally.

### Vector Search

Documents are converted to 384-dimensional vectors:
- Semantic similarity search
- Better than keyword matching
- Understands meaning, not just words

### Structured Lookup

Special handling for structured data (tables):
- Fuzzy location matching
- Alias resolution
- Multi-level fallbacks

**Example**: "Denver" → "Denver, CO" (even without state specified!)

## Architecture Diagram

```
User
  ↓
Frontend (nginx + JavaScript)
  ↓
Orchestrator (FastAPI + LLM 14B)
  ├─ Intent Classification
  ├─ Query Planning
  └─ Response Validation
  ↓
Worker (FastAPI + LLM 32B)
  ├─ RAG Search (Vector + Generation)
  ├─ Structured Lookup (Fuzzy Matching)
  └─ Context Building
  ↓
Qdrant (Vector Database)
  ↑
Crawler (Content Ingestion)
```

## Quick Start Commands

```bash
# Setup
./tools/setup.sh

# Start
./tools/airagctl start

# Crawl content
./tools/airagctl crawl https://example.com

# Ask question
./tools/airagctl ask "What is the rate for Denver?"

# Check health
./tools/airagctl health

# View logs
./tools/airagctl logs

# Backup
./tools/backup.sh create

# Test
./tools/test-endpoints.sh
```

## URLs

When running locally:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8080 |
| Orchestrator | http://localhost:8000 |
| Worker | http://localhost:8001 |
| Qdrant | http://localhost:6333 |
| Orchestrator Docs | http://localhost:8000/docs |
| Worker Docs | http://localhost:8001/docs |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, FastAPI |
| LLMs | Ollama (qwen2.5) |
| Embeddings | sentence-transformers |
| Vector DB | Qdrant |
| Frontend | HTML/CSS/JavaScript, nginx |
| Containers | Docker, Docker Compose |

## Common Workflows

### First Time Setup

1. Run `./tools/setup.sh`
2. Start services: `./tools/airagctl start`
3. Crawl content: `./tools/airagctl crawl <url>`
4. Open frontend: http://localhost:8080

### Development

1. Setup dev: `./tools/setup.sh --dev`
2. Start with hot reload: `./tools/dev.sh start`
3. Edit code (auto-reloads)
4. Test: `./tools/test-endpoints.sh`

### Production

1. Setup: `./tools/setup.sh --full`
2. Configure SSL (see DEPLOYMENT.md)
3. Setup systemd service
4. Setup automated backups
5. Monitor health

## File Locations

```
docs/
├── README.md           # This file
├── ARCHITECTURE.md     # System architecture
├── DEPLOYMENT.md       # Deployment guide
├── API.md             # API reference
├── DEVELOPMENT.md     # Development guide
└── FAQ.md             # FAQ
```

## Need Help?

1. **Quick answer**: Check [FAQ.md](FAQ.md)
2. **Setup issue**: See [DEPLOYMENT.md](DEPLOYMENT.md)
3. **API question**: Read [API.md](API.md)
4. **Development**: Check [DEVELOPMENT.md](DEVELOPMENT.md)
5. **Still stuck**: Open GitHub issue

## Contributing

Want to improve the docs?

1. Fork repository
2. Edit markdown files
3. Submit pull request

Documentation improvements are always welcome!

## Version

Documentation for AI RAG v1.0.0

Last updated: January 2025

---

**Part of AI RAG Batch 7**  
**Status**: Complete ✅
