# =============================================================================
# AI RAG Makefile
# Common tasks for managing the AI RAG system
# =============================================================================

.PHONY: help start stop restart logs status health crawl reset clean test

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "AI RAG - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  1. cp .env.example .env"
	@echo "  2. nano .env  (configure your settings)"
	@echo "  3. make start"
	@echo "  4. make logs  (wait for models to download)"
	@echo "  5. Open http://localhost:8080"

# =============================================================================
# Service Management
# =============================================================================

start: ## Start all services
	@echo "Starting AI RAG services..."
	docker compose up -d
	@echo "✓ Services started"
	@echo ""
	@echo "Access points:"
	@echo "  - Web UI:           http://localhost:8080"
	@echo "  - Orchestrator API: http://localhost:8000"
	@echo "  - Worker API:       http://localhost:8001"
	@echo "  - Qdrant:           http://localhost:6333"
	@echo ""
	@echo "Run 'make logs' to watch startup progress"

stop: ## Stop all services
	@echo "Stopping AI RAG services..."
	docker compose down
	@echo "✓ Services stopped"

restart: ## Restart all services
	@echo "Restarting AI RAG services..."
	docker compose restart
	@echo "✓ Services restarted"

logs: ## Show logs from all services
	docker compose logs -f

logs-orchestrator: ## Show orchestrator logs
	docker compose logs -f orchestrator-api orchestrator-ollama

logs-worker: ## Show worker logs
	docker compose logs -f worker-api worker-ollama

logs-crawler: ## Show crawler logs
	docker compose logs -f crawler

status: ## Show status of all services
	@docker compose ps

health: ## Check health of all services
	@echo "Checking service health..."
	@echo ""
	@curl -sf http://localhost:8000/health && echo "✓ Orchestrator API: healthy" || echo "✗ Orchestrator API: unhealthy"
	@curl -sf http://localhost:8001/health && echo "✓ Worker API: healthy" || echo "✗ Worker API: unhealthy"
	@curl -sf http://localhost:6333/health && echo "✓ Qdrant: healthy" || echo "✗ Qdrant: unhealthy"
	@curl -sf http://localhost:11434/api/tags > /dev/null && echo "✓ Orchestrator Ollama: healthy" || echo "✗ Orchestrator Ollama: unhealthy"
	@curl -sf http://localhost:11435/api/tags > /dev/null && echo "✓ Worker Ollama: healthy" || echo "✗ Worker Ollama: unhealthy"

# =============================================================================
# Model Management
# =============================================================================

pull-models: ## Pull LLM models (if not auto-downloaded)
	@echo "Pulling Orchestrator model..."
	docker compose exec orchestrator-ollama ollama pull $(shell grep ORCHESTRATOR_MODEL .env | cut -d '=' -f2 || echo "qwen2.5:14b")
	@echo "Pulling Worker model..."
	docker compose exec worker-ollama ollama pull $(shell grep WORKER_MODEL .env | cut -d '=' -f2 || echo "qwen2.5:32b")
	@echo "✓ Models pulled"

list-models: ## List downloaded models
	@echo "Orchestrator models:"
	@docker compose exec orchestrator-ollama ollama list
	@echo ""
	@echo "Worker models:"
	@docker compose exec worker-ollama ollama list

# =============================================================================
# Crawling
# =============================================================================

crawl: ## Crawl a URL (use: make crawl URL=https://example.com)
	@if [ -z "$(URL)" ]; then \
		echo "Error: URL is required. Usage: make crawl URL=https://example.com"; \
		exit 1; \
	fi
	@echo "Crawling $(URL)..."
	docker compose run --rm crawler python /app/cli.py crawl --url $(URL)
	@echo "✓ Crawl complete"

crawl-file: ## Crawl URLs from file (use: make crawl-file FILE=urls.txt)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE is required. Usage: make crawl-file FILE=urls.txt"; \
		exit 1; \
	fi
	@echo "Crawling URLs from $(FILE)..."
	docker compose run --rm crawler python /app/cli.py crawl --file $(FILE)
	@echo "✓ Crawl complete"

crawl-status: ## Show crawl status
	docker compose run --rm crawler python /app/cli.py status

# =============================================================================
# Data Management
# =============================================================================

reset: ## Reset all data (⚠️  destructive!)
	@echo "⚠️  This will delete all crawled data, embeddings, and models!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Stopping services..."; \
		docker compose down; \
		echo "Removing data..."; \
		rm -rf data/; \
		echo "✓ All data removed"; \
	else \
		echo "Reset cancelled"; \
	fi

reset-vectors: ## Reset vector database only (keeps models)
	@echo "Resetting vector database..."
	docker compose run --rm crawler python /app/cli.py reset
	@echo "✓ Vector database reset"

backup: ## Create backup of data directory
	@echo "Creating backup..."
	@BACKUP_NAME="airag-backup-$$(date +%Y%m%d-%H%M%S).tar.gz"; \
	tar -czf $$BACKUP_NAME data/; \
	echo "✓ Backup created: $$BACKUP_NAME"

# =============================================================================
# Development
# =============================================================================

shell-orchestrator: ## Open shell in orchestrator container
	docker compose exec orchestrator-api /bin/bash

shell-worker: ## Open shell in worker container
	docker compose exec worker-api /bin/bash

shell-crawler: ## Open shell in crawler container
	docker compose run --rm crawler /bin/bash

test: ## Run system tests (coming in Batch 6)
	@echo "Tests not yet implemented (coming in Batch 6)"
	@echo "For now, try:"
	@echo "  make health"

benchmark: ## Run benchmarks (coming in Batch 6)
	@echo "Benchmarks not yet implemented (coming in Batch 6)"

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Remove temporary files and caches
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	@echo "✓ Cleanup complete"

prune: ## Remove all Docker resources (⚠️  destructive!)
	@echo "⚠️  This will remove all Docker containers, volumes, and networks!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v --remove-orphans; \
		docker system prune -f; \
		echo "✓ Docker resources pruned"; \
	else \
		echo "Prune cancelled"; \
	fi

# =============================================================================
# GPU Management
# =============================================================================

gpu-status: ## Show GPU status
	@echo "GPU Status:"
	@nvidia-smi || echo "Error: nvidia-smi not found. Is NVIDIA driver installed?"

gpu-test: ## Test GPU access in Docker
	@echo "Testing GPU access in Docker..."
	docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# =============================================================================
# Monitoring
# =============================================================================

stats: ## Show resource usage
	@echo "Container Resource Usage:"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

disk: ## Show disk usage
	@echo "Data Directory Disk Usage:"
	@du -h -d 1 data/ 2>/dev/null || echo "No data directory found"

# =============================================================================
# Quick Smoke Test
# =============================================================================

smoke-test: ## Run quick smoke test
	@echo "Running smoke test..."
	@echo ""
	@echo "1. Checking services..."
	@make health
	@echo ""
	@echo "2. Testing Orchestrator API..."
	@curl -X POST http://localhost:8000/ask \
		-H "Content-Type: application/json" \
		-d '{"question": "Hello, are you working?"}' \
		2>/dev/null || echo "✗ Orchestrator API failed"
	@echo ""
	@echo "3. Testing Qdrant..."
	@curl -sf http://localhost:6333/collections > /dev/null && echo "✓ Qdrant accessible" || echo "✗ Qdrant failed"
	@echo ""
	@echo "✓ Smoke test complete"

# =============================================================================
# Info
# =============================================================================

info: ## Show system information
	@echo "AI RAG System Information"
	@echo "========================="
	@echo ""
	@echo "Docker:"
	@docker --version
	@docker compose version
	@echo ""
	@echo "Services:"
	@make status
	@echo ""
	@echo "Data directories:"
	@ls -lh data/ 2>/dev/null || echo "  (no data yet)"
	@echo ""
	@echo "Environment:"
	@echo "  Collection: $(shell grep QDRANT_COLLECTION .env 2>/dev/null | cut -d '=' -f2 || echo 'not set')"
	@echo "  Orchestrator Model: $(shell grep ORCHESTRATOR_MODEL .env 2>/dev/null | cut -d '=' -f2 || echo 'not set')"
	@echo "  Worker Model: $(shell grep WORKER_MODEL .env 2>/dev/null | cut -d '=' -f2 || echo 'not set')"
