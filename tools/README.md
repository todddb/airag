# Tools

Command-line tools and utilities for managing the AI RAG system.

## Overview

| Tool | Purpose |
|------|---------|
| **airagctl** | Main CLI tool (like `kubectl` or `policyctl`) |
| **setup.sh** | Easy setup script |
| **dev.sh** | Development workflow helper |
| **backup.sh** | Backup and restore utility |
| **test-endpoints.sh** | API endpoint testing |

## airagctl - Main CLI Tool

The primary tool for managing AI RAG.

### Installation

```bash
# Add to PATH
export PATH="$PATH:$(pwd)/tools"

# Or create symlink
sudo ln -s $(pwd)/tools/airagctl /usr/local/bin/airagctl
```

### Usage

```bash
# Service Management
airagctl start              # Start all services
airagctl stop               # Stop all services
airagctl restart            # Restart all services
airagctl status             # Check service status
airagctl logs [service]     # View logs

# Operations
airagctl crawl <url>        # Crawl website
airagctl ask "question"     # Ask question
airagctl health             # Check system health
airagctl reset              # Reset database
airagctl backup             # Create backup
airagctl restore <file>     # Restore backup

# Development
airagctl dev                # Start in dev mode
```

### Examples

```bash
# Start system
airagctl start

# Crawl documentation
airagctl crawl https://docs.example.com

# Ask question
airagctl ask "What is the per diem rate for Denver?"

# Check health
airagctl health

# View logs
airagctl logs orchestrator-api

# Backup database
airagctl backup
```

## setup.sh - Easy Setup

Interactive setup wizard for first-time installation.

### Usage

```bash
# Interactive setup (recommended)
./tools/setup.sh

# Quick setup with defaults
./tools/setup.sh --quick

# Development setup
./tools/setup.sh --dev

# Full setup (asks questions)
./tools/setup.sh --full
```

### What It Does

1. ✓ Checks requirements (Docker, Docker Compose)
2. ✓ Checks port availability
3. ✓ Creates `.env` from template
4. ✓ Pulls base Docker images
5. ✓ Builds service images
6. ✓ Optionally pulls LLM models (~20GB)
7. ✓ Configures tools

## dev.sh - Development Helper

Streamlines development workflow with hot reload.

### Usage

```bash
# Start dev environment
./tools/dev.sh start

# Watch logs
./tools/dev.sh logs [service]

# Rebuild service
./tools/dev.sh rebuild <service>

# Run tests
./tools/dev.sh test

# Shell access
./tools/dev.sh shell <service>
```

### Features

- Hot reload for code changes
- Debug logging enabled
- Volume mounts for live editing
- Fast iteration cycle

### Examples

```bash
# Start with hot reload
./tools/dev.sh start

# Rebuild orchestrator after changes
./tools/dev.sh rebuild orchestrator-api

# Open shell in worker
./tools/dev.sh shell worker-api
```

## backup.sh - Backup & Restore

Manage vector database backups.

### Usage

```bash
# Create backup
./tools/backup.sh create

# List backups
./tools/backup.sh list

# Restore backup
./tools/backup.sh restore backups/qdrant_backup_20250113_120000.tar.gz

# Clean old backups (keep 5)
./tools/backup.sh cleanup

# Export collection as JSON
./tools/backup.sh export documents
```

### Backup Location

```
backups/
├── qdrant_backup_20250113_120000.tar.gz
├── qdrant_backup_20250113_140000.tar.gz
└── documents_export_20250113_150000.json
```

### Automated Backups

Add to crontab:

```bash
# Backup daily at 2 AM
0 2 * * * /path/to/airag/tools/backup.sh create

# Clean old backups weekly
0 3 * * 0 /path/to/airag/tools/backup.sh cleanup 10
```

## test-endpoints.sh - API Testing

Comprehensive endpoint testing suite.

### Usage

```bash
# Run all tests
./tools/test-endpoints.sh
```

### What It Tests

**Orchestrator API (8000):**
- Health check
- Root endpoint
- Intent classification
- Question answering

**Worker API (8001):**
- Health check
- Root endpoint

**Frontend (8080):**
- Health check
- Main page
- Static assets (CSS, JS)

**Qdrant (6333):**
- Health check
- Collections list

**Ollama (11434, 11435):**
- Service availability

**Integration:**
- Full question flow

### Example Output

```
========================================
AI RAG Endpoint Testing
========================================

========================================
Testing Orchestrator API (Port 8000)
========================================
Testing Health Check... ✓ OK (200)
Testing Root Endpoint... ✓ OK (200)
Testing Classify Intent... ✓ OK (200)
Testing Ask Question... ✓ OK (200)

Orchestrator: 4 passed, 0 failed

========================================
Test Summary
========================================
✓ All tests passed!

ℹ System is fully operational
```

## Common Workflows

### First Time Setup

```bash
# 1. Run setup
./tools/setup.sh

# 2. Start services
./tools/airagctl start

# 3. Test endpoints
./tools/test-endpoints.sh

# 4. Crawl content
./tools/airagctl crawl https://docs.example.com

# 5. Open frontend
open http://localhost:8080
```

### Development Workflow

```bash
# 1. Start in dev mode
./tools/dev.sh start

# 2. Edit code (changes reload automatically)
vim services/orchestrator/app.py

# 3. Watch logs
./tools/dev.sh logs orchestrator-api

# 4. Test changes
./tools/test-endpoints.sh
```

### Production Deployment

```bash
# 1. Setup production
./tools/setup.sh --full

# 2. Start services
./tools/airagctl start

# 3. Create initial backup
./tools/backup.sh create

# 4. Setup automated backups (crontab)
crontab -e
# Add: 0 2 * * * /path/to/tools/backup.sh create

# 5. Monitor health
watch -n 60 './tools/airagctl health'
```

### Troubleshooting

```bash
# Check service status
./tools/airagctl status

# View logs for specific service
./tools/airagctl logs orchestrator-api

# Test all endpoints
./tools/test-endpoints.sh

# Restart services
./tools/airagctl restart

# Check system health
./tools/airagctl health
```

## Requirements

All tools require:
- **Docker** (20.10+)
- **Docker Compose** (2.0+)
- **bash** (4.0+)
- **curl** (for API testing)
- **jq** (optional, for JSON parsing)

Check with:
```bash
docker --version
docker compose version
curl --version
jq --version
```

## Environment Variables

Tools respect these environment variables:

- `COMPOSE_FILE` - Custom compose file
- `PROJECT_ROOT` - Project root directory
- `BACKUP_DIR` - Backup directory
- `LOG_LEVEL` - Logging level

## Tips

1. **Add to PATH**: Add `tools/` to your PATH for easy access
2. **Aliases**: Create shell aliases for common commands
3. **Autocomplete**: Enable bash completion if available
4. **Monitoring**: Use `watch` with health checks
5. **Logs**: Pipe logs through `jq` for formatting

### Useful Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias rag='airagctl'
alias rag-start='airagctl start'
alias rag-stop='airagctl stop'
alias rag-logs='airagctl logs'
alias rag-health='airagctl health'
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8000

# Stop conflicting service or change port in .env
```

### Docker Not Running

```bash
# Start Docker daemon
sudo systemctl start docker

# Or on Mac
open -a Docker
```

### Permission Denied

```bash
# Make scripts executable
chmod +x tools/*.sh

# Or run with bash
bash tools/airagctl start
```

### Services Won't Start

```bash
# Check logs
./tools/airagctl logs

# Rebuild images
docker compose build --no-cache

# Reset everything
docker compose down -v
./tools/setup.sh --quick
```

---

**Part of AI RAG Batch 6**  
**Status**: Complete ✅  
**Next**: Documentation (Batch 7)
