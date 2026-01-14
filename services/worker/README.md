# Worker Service

The intelligent worker that executes RAG searches and structured lookups with fuzzy matching.

## What This Service Does

1. **RAG Search** - Semantic vector search + answer generation
2. **Structured Lookup** - Fuzzy matching for tables/databases (NO REGEX!)
3. **Context Building** - Assembles chunks with citations
4. **Embeddings** - Converts text to vectors for search

## The Fuzzy Matching Solution

### Problem (Your Old System)
```python
# Regex hell - breaks on variations
if re.search(r'\bper diem\b', question):
    match = re.search(r'for\s+([^,]+),?\s*([A-Z]{2})?', question)
    # ✗ "Denver" → FAILS
    # ✗ "Arapahoe County" → FAILS  
    # ✗ "denver co" → FAILS
```

### Solution (This System)
```python
# Intelligent fuzzy matching
result = await structured_lookup.lookup(
    entity_type="location_rate",
    params={"location": "Denver"}
)
# ✓ "Denver" → "Denver, CO"
# ✓ "Arapahoe County" → "Aurora, CO"
# ✓ "denver co" → "Denver, CO"
# ✓ "Denvor" (typo) → "Denver, CO"
```

## Components

### rag_engine.py (351 lines)
- Vector search in Qdrant
- Context building from chunks
- LLM answer generation
- Hybrid search support

### structured_lookup.py (452 lines) ⭐
- **THE SOLUTION TO YOUR PROBLEM**
- Fuzzy matching with rapidfuzz
- Location normalization
- Alias resolution (counties → cities)
- Multi-level fallbacks
- **0 regex patterns!**

### context_builder.py (288 lines)
- Assembles chunks into context
- Deduplication
- Token-aware truncation
- Citation formatting

### embeddings.py (236 lines)
- sentence-transformers integration
- Batch processing
- 384-dimensional embeddings
- ~1000 texts/second

## Fuzzy Matching Examples

```python
# Exact match
"Denver, CO" → "Denver, CO" (confidence: 0.95)

# Missing state
"Denver" → "Denver, CO" (confidence: 0.88)

# County name
"Arapahoe County" → "Aurora, CO" (confidence: 0.95)
# Note: Uses alias mapping

# Typo
"Denvor, CO" → "Denver, CO" (confidence: 0.86)

# Case insensitive
"denver, co" → "Denver, CO" (confidence: 0.95)

# Abbreviation
"Salt Lake" → "Salt Lake City, UT" (confidence: 0.90)
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `POST /execute` - Main execution (called by orchestrator)
- `POST /rag_search` - Direct RAG search
- `POST /structured_lookup` - Direct lookup

## Configuration

Set via environment variables:

- `WORKER_OLLAMA_URL` - Ollama service URL
- `QDRANT_URL` - Qdrant vector database URL
- `WORKER_MODEL` - LLM model (default: qwen2.5:32b)
- `EMBEDDING_MODEL` - Embedding model (default: all-MiniLM-L6-v2)
- `QDRANT_COLLECTION` - Collection name

## Dependencies

- FastAPI - Web framework
- Qdrant - Vector database
- sentence-transformers - Embeddings
- rapidfuzz - Fuzzy matching (NOT regex!)
- Ollama - LLM client

## Testing

```bash
# Health check
curl http://localhost:8001/health

# RAG search
curl -X POST http://localhost:8001/rag_search \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the travel policies?", "top_k": 8}'

# Structured lookup
curl -X POST http://localhost:8001/structured_lookup \
  -H "Content-Type: application/json" \
  -d '{"entity_type": "location_rate", "entity": "Denver"}'
```

## How It Integrates

```
Orchestrator → Worker
POST /execute
{
  "task_type": "structured_lookup",
  "params": {"location": "Denver"}
}

Worker responds:
{
  "success": true,
  "result": {
    "answer": "The rate for Denver, CO is $91",
    "citations": [...],
    "confidence": 0.9
  }
}
```

---

**Part of AI RAG Batch 3**  
**Status**: Complete ✅  
**Next**: Crawler Service (Batch 4)
