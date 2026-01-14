# AI RAG - Intelligent Question Answering System

> A production-ready, generalized AI-powered RAG (Retrieval-Augmented Generation) system with fuzzy matching, real-time streaming, and beautiful web UI.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](docker-compose.yml)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://python.org)

## ✨ Features

- 🤖 **Dual-LLM Architecture** - Orchestrator (14B) + Worker (32B) for intelligent task distribution
- 🔍 **Fuzzy Matching** - NO REGEX! Handles typos, variations, abbreviations naturally
- 📊 **Structured Data** - Extracts and searches tables (perfect for rates, prices, etc.)
- 🌐 **Web Crawling** - Automatic content ingestion from websites, PDFs, docs
- 💬 **Real-Time Streaming** - SSE-based thinking process visualization
- 🎨 **Beautiful UI** - Modern, responsive frontend with dark/light mode
- 🛠️ **Production Ready** - Docker Compose, health checks, backups, monitoring

## 🎯 The Problem It Solves

**Your BYU Policy System Issue:**
```python
# Old way - BREAKS on variations
if re.search(r'\bper diem\b', question):
    match = re.search(r'for\s+([^,]+),?\s*([A-Z]{2})?', question)
    # ✗ "Denver" (no state) → FAILS
    # ✗ "Arapahoe County" → FAILS  
    # ✗ "denver, co" (lowercase) → FAILS
```

**New Way - HANDLES EVERYTHING:**
```python
# AI-powered fuzzy matching
result = await structured_lookup.lookup(
    entity_type="location_rate",
    params={"location": "Denver"}
)
# ✓ "Denver" → "Denver, CO"
# ✓ "Arapahoe County" → "Aurora, CO"
# ✓ "denver co" → "Denver, CO"
# ✓ "Denvor" (typo) → "Denver, CO"
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 16GB RAM minimum (32GB recommended)
- 50GB disk space
- NVIDIA GPU (optional, for faster performance)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/airag.git
cd airag

# 2. Run setup wizard
./tools/setup.sh

# 3. Start services
./tools/airagctl start

# 4. Open browser
open http://localhost:8080
```

That's it! 🎉

### First Steps

```bash
# Crawl documentation
./tools/airagctl crawl https://docs.example.com

# Ask a question
./tools/airagctl ask "What is the per diem rate for Denver?"

# Check system health
./tools/airagctl health
```

## 📖 Documentation

- **[Getting Started](docs/GETTING_STARTED.md)** - Installation and first steps
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment guide
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  Modern UI (React-like vanilla JS)
│   (8080)    │  SSE streaming, dark/light mode
└──────┬──────┘
       │
┌──────▼──────────┐
│  Orchestrator   │  Smart routing (qwen2.5:14b)
│     (8000)      │  Intent classification, planning
└──────┬──────────┘
       │
┌──────▼──────────┐
│     Worker      │  Execution (qwen2.5:32b)
│     (8001)      │  RAG search, fuzzy matching
└──────┬──────────┘
       │
┌──────▼──────────┐
│     Qdrant      │  Vector database
│     (6333)      │  384-dim embeddings
└─────────────────┘
```

## 🎨 Key Innovations

### 1. No Regex Hell
Replace brittle regex patterns with intelligent LLM-based matching.

### 2. Dual-LLM Architecture
- **Orchestrator (14B)**: Fast intent classification and routing
- **Worker (32B)**: Deep reasoning and generation

### 3. Real-Time Thinking Display
Users see the AI's reasoning process in real-time.

## 🛠️ Tools

```bash
airagctl start              # Start services
airagctl stop               # Stop services
airagctl crawl <url>        # Crawl website
airagctl ask "question"     # Ask question
airagctl health             # Check health
airagctl backup             # Backup database
```

See [Tools Documentation](tools/README.md) for details.

## 📦 Components

| Component | Purpose | Port |
|-----------|---------|------|
| **Frontend** | Web UI | 8080 |
| **Orchestrator** | Smart routing | 8000 |
| **Worker** | RAG execution | 8001 |
| **Qdrant** | Vector DB | 6333 |
| **Ollama (×2)** | LLM serving | 11434, 11435 |
| **Crawler** | Content ingestion | - |

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for intelligent question answering**

**No regex patterns were harmed in the making of this system** 🎉
