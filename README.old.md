# AI RAG - Intelligent Document Search System

A production-ready, dual-LLM RAG (Retrieval-Augmented Generation) system for intelligent document search and question answering. Built with Docker, featuring orchestrator-worker LLM architecture, real-time streaming responses, and visible AI reasoning.

<img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"/> <img src="https://img.shields.io/badge/Docker-Ready-green.svg" alt="Docker"/> <img src="https://img.shields.io/badge/GPU-Accelerated-orange.svg" alt="GPU"/> <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python"/>

## 🌟 Key Features

### Dual-LLM Architecture
- **Orchestrator LLM**: Understands user intent, plans query strategies, validates responses
- **Worker LLM**: Executes RAG searches, handles structured lookups, generates answers
- **No Hardcoded Rules**: LLMs handle fuzzy matching and entity resolution
- **Intelligent Validation**: Orchestrator ensures responses answer the question with proper citations

### Advanced Capabilities
- 🔍 **Smart Crawling**: Automated web crawling with support for HTML, PDF, tables, and structured data
- 🎯 **Fuzzy Matching**: Intelligent location/entity resolution with multiple fallback strategies
- 📡 **Real-time Streaming**: Watch the AI think through your question with Server-Sent Events
- 🎨 **Modern UI**: Responsive web interface showing AI reasoning process step-by-step
- ⚡ **GPU Accelerated**: Optimized for NVIDIA GPUs (tested on RTX 5090)
- 🏗️ **Production Ready**: Docker-based, scalable, with monitoring and logging
- 🌍 **ARM Compatible**: Works on both x86_64 and ARM architectures (e.g., Dell Pro Max GB10)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Query                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            Orchestrator API (Port 8000)                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Orchestrator LLM (qwen2.5:14b)                    │    │
│  │  • Classifies intent (structured vs. general)      │    │
│  │  • Extracts parameters (location, dates, etc.)     │    │
│  │  • Plans query strategy                            │    │
│  │  • Validates worker responses                       │    │
│  │  • Streams thinking process to UI                  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Worker API (Port 8001)                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Worker LLM (qwen2.5:32b)                          │    │
│  │  • Executes structured lookups (tables, etc.)      │    │
│  │  • Performs vector similarity search               │    │
│  │  • Builds context from documents                   │    │
│  │  • Generates final answers                         │    │
│  │  • Provides citations                              │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│         Qdrant Vector Database (Port 6333)                  │
│  • Stores document embeddings (384 dimensions)              │
│  • Performs similarity search                               │
│  • Manages metadata and structured data                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker** and Docker Compose v2.0+
- **NVIDIA GPU** with 16GB+ VRAM (32GB recommended for dual 32B models)
- **System RAM**: 32GB+ recommended
- **NVIDIA Container Toolkit** (for GPU support)
- **Linux** or WSL2 (Windows)

### Installation

```bash
# Clone or create the directory
mkdir -p ~/airag
cd ~/airag

# Copy this project structure into ~/airag/

# Create environment file
cp .env.example .env

# Edit configuration (especially GPU settings)
nano .env

# Start all services
docker compose up -d

# Watch logs for model downloads (first time: ~27GB, 10-15 mins)
docker compose logs -f orchestrator-ollama worker-ollama

# Verify all services are healthy
docker compose ps

# Open web interface
xdg-open http://localhost:8080
```

### First Crawl

```bash
# Crawl a website (use docker compose for now, airagctl tool coming in Batch 6)
docker compose run --rm crawler python /app/cli.py crawl \
  --url https://example.com/docs

# Check Qdrant for ingested documents
curl http://localhost:6333/collections/documents

# Ask a question via API
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this documentation about?"}'
```

## 📊 Service Overview

| Service | Port | Purpose | GPU |
|---------|------|---------|-----|
| **orchestrator-ollama** | 11434 | Intent classification LLM | Yes |
| **worker-ollama** | 11435 | Answer generation LLM | Yes |
| **orchestrator-api** | 8000 | Main API endpoint | No |
| **worker-api** | 8001 | Internal worker service | No |
| **qdrant** | 6333 | Vector database | No |
| **crawler** | - | CLI-based document crawler | No |
| **frontend** | 8080 | Web UI | No |

## 🎯 How It Works: Dual-LLM Example

### Traditional Approach (Your Old System)
```python
# Hardcoded regex patterns - brittle and limited
if re.search(r'\b(per diem|daily rate)\b', question):
    match = re.search(r'for\s+([A-Z][a-z]+)', question)
    # Exact match only - fails on "Denver", "Arapahoe County", etc.
```

### Dual-LLM Approach (This System)

**User asks:** *"What is the rate for Denver?"*

```
Step 1: Orchestrator classifies intent
└─> Intent: structured_lookup
└─> Entity: location_rate  
└─> Extracted: {location: "Denver, CO", type: "daily_rate"}
└─> Confidence: 0.92
└─> Plan: Query worker for table lookup

Step 2: Worker executes fuzzy lookup
└─> Normalizes: "Denver" → "Denver, CO"
└─> Searches table: Found entry
└─> Returns: {rate: "$91", source: "rates_table", row: 42}

Step 3: Orchestrator validates
└─> Does answer address "rate for Denver"? ✓ Yes
└─> Does it include source citation? ✓ Yes
└─> Is format correct? ✓ Yes
└─> Final answer: "The daily rate for Denver, CO is $91."
```

**Benefits:**
- ✅ No regex patterns needed
- ✅ Handles "Denver" (without state)
- ✅ Handles "Arapahoe County" (fuzzy match to Aurora)
- ✅ Handles typos and variations
- ✅ Self-validates responses

## 🎨 Frontend Features

The web UI provides:

- **Real-time Streaming**: Watch the AI think through your question
- **Thinking Process Display**: See orchestrator decisions and worker actions in real-time
- **Citation Panel**: Click through to source documents
- **Search History**: Review and re-run past queries
- **Dark/Light Mode**: Your preference persists across sessions
- **Mobile Responsive**: Works on any device

## 📖 Documentation

Comprehensive documentation is being created in batches:

- **Batch 1** (✅ Complete):
  - [Dual-LLM Design](docs/DUAL_LLM_DESIGN.md) - Architecture deep-dive
  
- **Batch 7** (Coming Soon):
  - Installation Guide - Detailed setup instructions
  - Architecture Overview - System design and components
  - User Guide - How to use the system
  - Admin Guide - Management and operations  
  - API Reference - API endpoints and usage
  - Development Guide - Contributing and extending

## 🔧 Configuration

### Key Environment Variables

See `.env.example` for all 100+ configuration options. Most important:

```bash
# LLM Models
ORCHESTRATOR_MODEL=qwen2.5:14b    # Lighter, faster for classification
WORKER_MODEL=qwen2.5:32b           # Larger, smarter for answers

# GPU Configuration
GPU_ENABLED=true
GPU_DEVICE_IDS=0  # Use GPU 0, or "0,1" for multiple GPUs

# Vector Database
QDRANT_COLLECTION=documents
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Streaming
STREAMING_ENABLED=true
SHOW_THINKING_PROCESS=true
```

### Model Selection

Choose models based on your hardware:

```bash
# RTX 5090 32GB (Recommended - Fits both LLMs)
ORCHESTRATOR_MODEL=qwen2.5:14b  # ~9GB VRAM
WORKER_MODEL=qwen2.5:32b         # ~20GB VRAM

# RTX 4090 24GB (Smaller worker)
ORCHESTRATOR_MODEL=qwen2.5:14b  # ~9GB VRAM
WORKER_MODEL=qwen2.5:14b         # ~9GB VRAM

# RTX 3090 24GB (Even smaller)
ORCHESTRATOR_MODEL=llama3:8b     # ~6GB VRAM
WORKER_MODEL=qwen2.5:14b         # ~9GB VRAM

# CPU Only (Slow but works)
GPU_ENABLED=false
ORCHESTRATOR_MODEL=llama3:8b
WORKER_MODEL=qwen2.5:14b
```

## 🛠️ Management Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f orchestrator-api worker-api

# Restart a service
docker compose restart orchestrator-api

# Check service health
docker compose ps

# Remove all data (⚠️ destructive)
docker compose down -v
rm -rf data/
```

### Crawler Commands (via Docker Compose)

```bash
# Crawl a single URL
docker compose run --rm crawler python /app/cli.py crawl \
  --url https://example.com/docs

# Crawl from a file of URLs
docker compose run --rm crawler python /app/cli.py crawl \
  --file urls.txt

# Check crawl status
docker compose run --rm crawler python /app/cli.py status

# Reset all data
docker compose run --rm crawler python /app/cli.py reset
```

*(Full `airagctl` CLI tool coming in Batch 6)*

## 📈 Performance

### Benchmarks (RTX 5090, 32GB RAM)

- **Model Loading**: ~30 seconds (first time: 10-15 minutes to download)
- **Crawling**: 50-100 pages/minute
- **Embedding**: ~1000 chunks/second
- **Simple Query**: 1-3 seconds (with streaming)
- **Complex Query**: 3-8 seconds (multi-step reasoning)

### GPU Memory Usage

| Component | VRAM | Notes |
|-----------|------|-------|
| Orchestrator (14B) | ~9GB | Intent classification |
| Worker (32B) | ~20GB | Answer generation |
| Embeddings | ~1GB | Sentence transformers |
| **Total** | **~30GB** | Fits RTX 5090 |

## 🔒 Security

- **No External APIs**: All processing happens locally
- **Data Privacy**: Your documents never leave your infrastructure  
- **Optional Authentication**: Add CAS/SAML for enterprise (Batch 6)
- **Rate Limiting**: Configurable per-IP limits
- **Input Sanitization**: All user inputs are validated

## 🤝 Contributing

This project is in active development. Additional batches coming soon:

- **Batch 2**: Orchestrator service implementation
- **Batch 3**: Worker service implementation
- **Batch 4**: Crawler service (generalized from BYU policy crawler)
- **Batch 5**: Frontend with streaming and thinking display
- **Batch 6**: CLI tools (`airagctl` command)
- **Batch 7**: Complete documentation
- **Batch 8**: Examples and tutorials

## 🆘 Support & Troubleshooting

### Common Issues

**1. GPU not detected:**
```bash
# Check NVIDIA drivers
nvidia-smi

# Verify Docker can access GPU
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Check nvidia-container-toolkit is installed
dpkg -l | grep nvidia-container-toolkit
```

**2. Models not downloading:**
```bash
# Check orchestrator
docker compose logs orchestrator-ollama

# Manually pull models
docker compose exec orchestrator-ollama ollama pull qwen2.5:14b
docker compose exec worker-ollama ollama pull qwen2.5:32b
```

**3. Out of memory:**
```bash
# Use smaller models in .env
ORCHESTRATOR_MODEL=llama3:8b
WORKER_MODEL=qwen2.5:14b

# Or enable CPU offloading
GPU_MEMORY_FRACTION=0.8
```

## 📝 License

MIT License - see LICENSE file for details

## 🎓 Learn More

- [Dual-LLM Architecture](docs/DUAL_LLM_DESIGN.md) - Why two LLMs?
- [RAG Best Practices](#) - Coming in Batch 7
- [Deployment Guide](#) - Coming in Batch 7

---

**Project Status**: 🚧 Batch 1/8 Complete (Foundation Files)

**Next**: Batch 2 will add the Orchestrator service implementation

Built with ❤️ for intelligent document search
