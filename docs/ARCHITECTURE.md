# Architecture

Comprehensive system architecture documentation.

See [DUAL_LLM_DESIGN.md](DUAL_LLM_DESIGN.md) for detailed architecture explanation.

## Overview

AI RAG uses a dual-LLM architecture:
- **Orchestrator (14B)**: Fast routing and classification
- **Worker (32B)**: Deep reasoning and generation

## Components

| Component | Purpose | Port |
|-----------|---------|------|
| Frontend | Web UI | 8080 |
| Orchestrator | Smart routing | 8000 |
| Worker | RAG execution | 8001 |
| Qdrant | Vector DB | 6333 |
| Ollama (×2) | LLM serving | 11434, 11435 |

## Key Innovations

1. **No Regex**: LLM-based intent and fuzzy matching
2. **Dual-LLM**: Speed + quality
3. **SSE Streaming**: Real-time thinking display
4. **Vector Search**: Semantic understanding

For full details, see [DUAL_LLM_DESIGN.md](DUAL_LLM_DESIGN.md).
