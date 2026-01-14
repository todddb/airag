# Quick Start Guide - AI RAG System

## What You Have Now (Batch 1 Complete)

✅ **docker-compose.yml** - All 7 services configured and ready  
✅ **.env.example** - Complete configuration template (285 lines!)  
✅ **README.md** - Comprehensive documentation  
✅ **docs/DUAL_LLM_DESIGN.md** - Architecture explanation (913 lines!)  
✅ **Makefile** - 30+ helpful commands  
✅ **LICENSE** - MIT license  
✅ **.gitignore** - Proper exclusions  

## What's Different from Your BYU Policy System

| Feature | Old (policy) | New (airag) |
|---------|--------------|-------------|
| **Path** | ~/policy | ~/airag |
| **CLI** | policyctl | airagctl (Batch 6) |
| **Query Handling** | 50+ regex patterns | Dual-LLM orchestration |
| **Architecture** | Monolithic API | Microservices (7 containers) |
| **Per Diem** | Hardcoded rules | LLM fuzzy matching |
| **UI Feedback** | Static responses | Streaming with thinking |
| **GPU** | Single Ollama | Two Ollama instances |
| **Focus** | BYU-specific | Generalized |

## Why Dual-LLM Architecture?

```
Your Old Problem:
  "What is the rate for Denver?" 
  ✗ Regex fails (no exact pattern)
  ✗ "Arapahoe County" fails (not in regex)
  ✗ "denver co" fails (case sensitive)

New Solution:
  Orchestrator LLM: "User wants location rate"
      ↓ (classifies intent)
  Worker LLM: Fuzzy matches "Denver" → "Denver, CO"
      ↓ (finds in table)
  Orchestrator: Validates response
      ↓
  Answer: "The rate for Denver, CO is $91"
  
  ✓ No regex needed
  ✓ Handles variations
  ✓ Self-validates
```

## Next Steps

### Option 1: Review Everything (Recommended)
```bash
cd /home/todddb/airag

# Read the overview
less README.md

# Understand the architecture
less docs/DUAL_LLM_DESIGN.md

# Check the configuration
less .env.example

# See available commands
make help
```

### Option 2: Configure and Test
```bash
cd /home/todddb/airag

# Create your config
cp .env.example .env

# Edit for your GPU
nano .env
# Set: GPU_ENABLED=true, GPU_DEVICE_IDS=0

# Validate docker-compose
docker compose config

# When Batches 2-8 are done:
# docker compose up -d
# make logs
```

### Option 3: Continue Building
Ready for the next batch? Say:

```
Please create Batch 2 of the AI RAG project as described in CREATE_IN_CONVERSATION.md.

Create the Orchestrator service files:
1. services/orchestrator/Dockerfile
2. services/orchestrator/requirements.txt
3. services/orchestrator/app.py (FastAPI with SSE streaming)
4. services/orchestrator/orchestrator.py (main orchestration logic)
5. services/orchestrator/lib/intent_classifier.py
6. services/orchestrator/lib/query_planner.py
7. services/orchestrator/lib/response_validator.py
8. services/orchestrator/lib/streaming_handler.py
9. services/orchestrator/lib/__init__.py

Place in /home/todddb/airag/services/orchestrator/
```

## What Each Batch Adds

- **Batch 1** ✅ Foundation (you are here)
- **Batch 2** ⬜ Orchestrator - Intent classification, planning, validation
- **Batch 3** ⬜ Worker - RAG engine, structured lookups, fuzzy matching
- **Batch 4** ⬜ Crawler - Web crawling, document parsing (no BYU code)
- **Batch 5** ⬜ Frontend - Streaming UI, thinking display
- **Batch 6** ⬜ Tools - airagctl CLI, tests, benchmarks
- **Batch 7** ⬜ Documentation - Complete guides
- **Batch 8** ⬜ Examples - Tutorials and sample data

## Key Files to Read

1. **README.md** - Start here, comprehensive overview
2. **docs/DUAL_LLM_DESIGN.md** - Understand why dual-LLM
3. **.env.example** - See all 100+ configuration options
4. **docker-compose.yml** - Understand the services
5. **Makefile** - Learn the available commands

## Your Hardware (RTX 5090)

Perfect for this system!

```
Orchestrator LLM (14B):  ~9GB VRAM
Worker LLM (32B):       ~20GB VRAM
Total:                  ~30GB VRAM
Your GPU:                32GB VRAM ✓

Fits comfortably with headroom for embeddings!
```

## Questions?

**Q: Can I start the system now?**  
A: Not yet! You need Batches 2-5 for the actual service implementations. Batch 1 just has the configuration.

**Q: How long will all batches take?**  
A: About 7 more requests (one per batch). Each batch takes ~5 minutes to generate.

**Q: Can I customize this?**  
A: Absolutely! It's designed to be generalized and extensible. Add your own parsers, query types, etc.

**Q: Will this work on my Dell Pro Max with GB10 (ARM)?**  
A: Yes! The .env.example has ARM configuration notes. Just uncomment the ARM section.

**Q: What if I have less VRAM?**  
A: Use smaller models. Edit .env:
   - ORCHESTRATOR_MODEL=llama3:8b (6GB)
   - WORKER_MODEL=qwen2.5:14b (9GB)

## Project Status

```
Batch 1: ████████░░░░░░░░░░░░░░ 12.5% Complete
Overall: ░░░░░░░░░░░░░░░░░░░░░░ ~1,800 lines / ~12,000 total
```

Ready to continue? Ask for Batch 2!

---

**Created**: 2025-01-14  
**Location**: /home/todddb/airag/  
**Status**: Foundation Complete, Ready for Implementation
