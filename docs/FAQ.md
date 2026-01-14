# Frequently Asked Questions (FAQ)

Common questions about AI RAG.

## General Questions

### What is AI RAG?

AI RAG is an intelligent question-answering system that combines:
- **Retrieval**: Finding relevant information
- **Augmentation**: Adding context
- **Generation**: Creating natural answers

### How is this different from ChatGPT?

- **Private**: Your data stays on your servers
- **Specialized**: Trained on your documents
- **Accurate**: Cites sources
- **Fast**: No API latency
- **Cost**: No per-query fees

### What's the "per diem problem"?

Your old BYU policy system used regex patterns that broke on variations:
- "Denver" (missing state) → FAIL
- "Arapahoe County" → FAIL
- "denver, co" (lowercase) → FAIL

AI RAG uses fuzzy matching instead - handles all variations naturally!

## Setup Questions

### What are the minimum requirements?

- **CPU**: 8 cores
- **RAM**: 32GB
- **Disk**: 100GB
- **GPU**: Optional (24GB+ VRAM for best performance)

### Do I need a GPU?

No, but it's highly recommended:
- **Without GPU**: Slow (~10-30s per query)
- **With GPU**: Fast (~1-5s per query)

### How long does setup take?

- **Installation**: 5-10 minutes
- **Pulling models**: 10-30 minutes (depends on internet speed)
- **Total**: ~30-40 minutes

### Can I run this on my laptop?

Yes, if you have:
- 32GB RAM
- 100GB free disk space
- Decent CPU (8+ cores)

Performance will be slower without GPU.

## Usage Questions

### How do I add content?

```bash
# Crawl a website
./tools/airagctl crawl https://docs.example.com

# Or crawl from file
./tools/airagctl crawl --file urls.txt
```

### How do I ask questions?

Three ways:

1. **Web UI**: http://localhost:8080
2. **CLI**: `./tools/airagctl ask "your question"`
3. **API**: `curl -X POST http://localhost:8000/ask`

### Can I use it for multiple domains?

Yes! Crawl multiple sites:

```bash
./tools/airagctl crawl https://docs1.example.com
./tools/airagctl crawl https://docs2.example.com
./tools/airagctl crawl https://docs3.example.com
```

### How do I reset everything?

```bash
# Reset database (keeps services running)
./tools/airagctl reset

# Or completely start over
docker-compose down -v
./tools/setup.sh --quick
```

## Technical Questions

### Why two LLMs?

**Dual-LLM architecture**:
- **Orchestrator** (14B): Fast classification
- **Worker** (32B): Detailed answers

This gives best balance of speed and quality.

### How does fuzzy matching work?

1. **Normalize**: "denver" → "Denver"
2. **Resolve aliases**: "Arapahoe County" → "Aurora, CO"
3. **Fuzzy match**: "Denvor" → "Denver, CO" (handles typos)
4. **Fallback**: Use state default if no match

All without regex!

### What's the difference from your old BYU system?

| Feature | BYU System | AI RAG |
|---------|-----------|---------|
| Intent detection | Regex (brittle) | LLM (flexible) |
| Fuzzy matching | None | Built-in |
| Search | Keyword | Semantic |
| Answers | Template-based | Generated |
| Extensibility | Hard | Easy |

### Can I use different models?

Yes! Edit `.env`:

```bash
# Smaller, faster
ORCHESTRATOR_MODEL=qwen2.5:7b
WORKER_MODEL=qwen2.5:14b

# Larger, smarter
ORCHESTRATOR_MODEL=qwen2.5:32b
WORKER_MODEL=qwen2.5:72b
```

## Troubleshooting

### Services won't start

```bash
# Check Docker
docker ps

# Check logs
./tools/airagctl logs

# Rebuild
docker-compose build --no-cache
./tools/airagctl restart
```

### Out of memory

```bash
# Use smaller models
ORCHESTRATOR_MODEL=qwen2.5:7b
WORKER_MODEL=qwen2.5:14b

# Or add swap
sudo fallocate -l 32G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Slow performance

**Without GPU**: Normal, try smaller models
**With GPU**: Check GPU usage with `nvidia-smi`

### Database issues

```bash
# Check Qdrant
curl http://localhost:6333/health

# Reset if needed
./tools/airagctl reset
```

### Port already in use

```bash
# Find what's using it
lsof -i :8000

# Kill or change port in .env
```

## Customization

### Can I customize the UI?

Yes! Edit `services/frontend/`:
- `index.html` - Structure
- `css/styles.css` - Styling
- `js/*.js` - Behavior

### Can I add authentication?

Not built-in yet. Recommended approach:
- Add nginx reverse proxy with basic auth
- Or use OAuth2 Proxy

### Can I change the models?

Yes! Supports any Ollama model:
- qwen2.5 (default)
- llama3
- mistral
- codellama
- etc.

## Best Practices

### How much content should I crawl?

Start small, then expand:
1. Crawl 10-20 pages
2. Test quality
3. Expand if good

Too much content can reduce quality!

### How often should I backup?

Recommended:
- **Daily**: Automated backup (cron)
- **Before major changes**: Manual backup
- **Keep**: Last 7-14 backups

### Should I run in production?

Yes, but:
- Use SSL/TLS
- Add authentication
- Monitor performance
- Set up backups
- Use systemd service

### How do I monitor it?

```bash
# Health checks
watch -n 60 './tools/airagctl health'

# Or add to monitoring (Prometheus, Grafana, etc.)
```

## Advanced

### Can I scale horizontally?

Partially:
- ✓ Orchestrator: Yes (stateless)
- ✓ Worker: Yes (stateless)
- ✓ Frontend: Yes (static)
- ✗ Ollama: No (GPU-bound)
- ✗ Qdrant: Needs cluster setup

### Can I use cloud models?

Yes, replace Ollama with:
- OpenAI API
- Anthropic API
- Cohere API

But you lose privacy benefits.

### Can I customize prompts?

Yes! Edit in service code:
- Orchestrator: `services/orchestrator/lib/intent_classifier.py`
- Worker: `services/worker/lib/rag_engine.py`

### Can I add new data sources?

Yes! Options:
1. Add parser in crawler
2. Direct Qdrant insertion
3. Custom ingestion script

## Getting Help

### Where can I get help?

1. Check this FAQ
2. Read docs: `/docs`
3. Check logs: `./tools/airagctl logs`
4. Test endpoints: `./tools/test-endpoints.sh`
5. Open GitHub issue

### How do I report bugs?

1. Check if already reported
2. Gather info:
   - Error message
   - Logs
   - Steps to reproduce
3. Open GitHub issue

### How can I contribute?

See `DEVELOPMENT.md` for guidelines!

---

**Part of AI RAG Batch 7**  
**Status**: Complete ✅
