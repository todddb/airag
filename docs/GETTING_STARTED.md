# Getting Started with AI RAG

This guide will help you get AI RAG up and running in less than 10 minutes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [First Run](#first-run)
- [Crawling Content](#crawling-content)
- [Asking Questions](#asking-questions)
- [Using the Web UI](#using-the-web-ui)
- [Next Steps](#next-steps)

## Prerequisites

### Required

- **Docker** 20.10 or later
- **Docker Compose** 2.0 or later
- **16GB RAM** minimum (32GB recommended)
- **50GB disk space** (for models and data)
- **curl** (for API testing)

### Optional

- **NVIDIA GPU** with CUDA support (for faster performance)
- **jq** (for JSON formatting in CLI)

### Check Your System

```bash
# Check Docker
docker --version
# Should show: Docker version 20.10.0 or later

# Check Docker Compose
docker compose version
# Should show: Docker Compose version v2.0.0 or later

# Check available disk space
df -h
# Should have at least 50GB free

# Check RAM
free -h
# Should have at least 16GB total
```

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/airag.git
cd airag
```

### Step 2: Run Setup

**Option A: Interactive Setup (Recommended for First Time)**

```bash
./tools/setup.sh
```

The setup wizard will:
1. Check system requirements
2. Check port availability
3. Create `.env` configuration
4. Pull Docker base images
5. Build service images
6. Optionally pull LLM models (~20GB, takes 10-30 min)

**Option B: Quick Setup (Use Defaults)**

```bash
./tools/setup.sh --quick
```

Skips questions and uses default configuration.

**Option C: Development Setup**

```bash
./tools/setup.sh --dev
```

Sets up development environment with hot reload.

### Step 3: Verify Installation

```bash
# Check that setup completed
ls -la .env
# Should see .env file

# Check Docker images
docker images | grep airag
# Should see airag images
```

## First Run

### Start Services

```bash
./tools/airagctl start
```

This will:
1. Build images (if not already built)
2. Start all Docker containers
3. Pull LLM models (first time only, ~20GB)
4. Wait for services to be healthy

**Note**: First start takes 15-30 minutes due to model downloads. Subsequent starts take ~30 seconds.

### Verify Services

```bash
# Check service status
./tools/airagctl status

# Should show all services running:
# - orchestrator-api
# - worker-api
# - frontend
# - qdrant
# - orchestrator-ollama
# - worker-ollama

# Run comprehensive tests
./tools/test-endpoints.sh

# Should show all tests passing
```

### Check Health

```bash
./tools/airagctl health
```

Expected output:
```
Orchestrator API:
✓ Running

Worker API:
✓ Running

Frontend:
✓ Running at http://localhost:8080

Qdrant Vector DB:
✓ Running
```

## Crawling Content

Before asking questions, you need to crawl some content.

### Crawl a Website

```bash
# Crawl documentation site
./tools/airagctl crawl https://docs.python.org/3/

# Crawl with options
./tools/airagctl crawl https://example.com \
  --max-pages 100 \
  --max-depth 2
```

### Crawl Multiple URLs

Create a file `urls.txt`:
```
https://docs.python.org/3/
https://numpy.org/doc/
https://pandas.pydata.org/docs/
```

Then crawl:
```bash
./tools/airagctl crawl --file urls.txt
```

### Check What Was Crawled

```bash
# Via CLI
docker compose run --rm crawler python /app/cli.py list

# Or check Qdrant
curl http://localhost:6333/collections/documents
```

## Asking Questions

### Via CLI

```bash
# Ask a question (non-streaming)
./tools/airagctl ask "What is a Python list comprehension?"

# Will show:
# - The answer
# - Source citations
```

### Via API

```bash
# Non-streaming
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is a Python list comprehension?", "stream": false}' \
  | jq .

# Streaming (SSE)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is a Python list comprehension?", "stream": true}'
```

## Using the Web UI

### Open Browser

```bash
open http://localhost:8080
# Or visit manually in your browser
```

### Try Example Questions

The welcome screen shows example questions you can click:

- "What are the travel policies?"
- "What is the per diem rate for Denver?"
- "How do I submit an expense report?"
- "What is the mileage reimbursement rate?"

### Watch AI Thinking

When you ask a question, you'll see the AI's thinking process:

```
💭 Analyzing your question...
⚡ Classifying intent: general_rag
👀 Searching knowledge base...
✓ Response validated
🤖 [Answer appears here]
```

### View Sources

Each answer includes source citations with links to the original documents.

### Toggle Dark Mode

Click the 🌙/☀️ button in the top right to switch themes.

## Next Steps

### 1. Crawl Your Own Content

```bash
# Your company docs
./tools/airagctl crawl https://company.com/docs

# Your product documentation
./tools/airagctl crawl https://docs.yourproduct.com
```

### 2. Learn the Architecture

Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand how the system works.

### 3. Customize Configuration

Edit `.env`:
```bash
# Change models
ORCHESTRATOR_MODEL=qwen2.5:14b
WORKER_MODEL=qwen2.5:32b

# Adjust performance
TEMPERATURE=0.7
MAX_TOKENS=2000

# Change collection name
QDRANT_COLLECTION=my_documents
```

Then restart:
```bash
./tools/airagctl restart
```

### 4. Set Up Backups

```bash
# Create backup
./tools/backup.sh create

# Schedule automated backups (crontab)
crontab -e
# Add: 0 2 * * * /path/to/airag/tools/backup.sh create
```

### 5. Monitor System

```bash
# Watch logs
./tools/airagctl logs

# Watch specific service
./tools/airagctl logs orchestrator-api

# Check health periodically
watch -n 60 './tools/airagctl health'
```

## Common Issues

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process or change port in .env
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Reduce concurrent services or upgrade RAM
```

### Models Not Downloading

```bash
# Pull models manually
docker compose exec orchestrator-ollama ollama pull qwen2.5:14b
docker compose exec worker-ollama ollama pull qwen2.5:32b
```

### Services Won't Start

```bash
# Check logs
./tools/airagctl logs

# Rebuild from scratch
docker compose down -v
./tools/setup.sh --quick
```

## Getting Help

- **Documentation**: [docs/](.)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API Docs**: [API.md](API.md)
- **GitHub Issues**: Report bugs and request features

## Summary

You now have AI RAG running! Here's what to remember:

```bash
# Start/stop services
./tools/airagctl start
./tools/airagctl stop

# Crawl content
./tools/airagctl crawl <url>

# Ask questions
./tools/airagctl ask "question"
open http://localhost:8080

# Monitor health
./tools/airagctl health
./tools/airagctl logs
```

Ready to explore more? Check out:
- [Architecture Guide](ARCHITECTURE.md)
- [API Reference](API.md)
- [Deployment Guide](DEPLOYMENT.md)
