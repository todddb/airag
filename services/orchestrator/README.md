# Orchestrator Service

The intelligent orchestrator that understands user intent and coordinates query execution.

## What This Service Does

1. **Classifies Intent** - Understands what users are asking using LLM (NO REGEX!)
2. **Plans Queries** - Decides the best execution strategy
3. **Validates Responses** - Ensures worker responses are high-quality
4. **Streams Thinking** - Shows AI reasoning process to users

## Architecture

```
User Question → app.py (FastAPI)
                  ↓
            orchestrator.py (Main Logic)
                  ↓
     ┌────────────┼────────────┐
     ↓            ↓            ↓
intent_classifier query_planner response_validator
     ↓            ↓            ↓
  [Analyzes]  [Plans]     [Validates]
     ↓            ↓            ↓
     └────────────┴────────────┘
                  ↓
          [Calls Worker API]
                  ↓
        streaming_handler (SSE)
```

## Key Innovation: No Regex!

### Old Way (Brittle)
```python
if re.search(r'\bper diem\b', question):
    # 50+ lines of patterns
```

### New Way (Intelligent)
```python
classification = await classifier.classify(question)
# Returns: {intent: "structured_lookup", confidence: 0.92, ...}
```

## Components

### intent_classifier.py
- LLM-based intent understanding
- Fuzzy parameter extraction
- Confidence scoring
- **323 lines, 0 regex patterns**

### query_planner.py
- Execution strategy selection
- Multi-step query support
- Dependency management
- **302 lines**

### response_validator.py
- Quality scoring (relevance, completeness, citations)
- Answer improvement suggestions
- Validation threshold: 0.7
- **301 lines**

### streaming_handler.py
- SSE event formatting
- Thinking process visualization
- Progress indicators
- **269 lines**

## Running

```bash
# Via Docker Compose (from project root)
docker compose up orchestrator-api

# Direct (for development)
cd /home/todddb/airag/services/orchestrator
pip install -r requirements.txt
python app.py
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `POST /ask` - Main query endpoint (streaming or JSON)
- `POST /classify` - Debug intent classification
- `POST /validate` - Debug response validation

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Ask a question (non-streaming)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the rate for Denver?", "stream": false}'

# Ask with streaming
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the rate for Denver?", "stream": true}'
```

## Configuration

Set via environment variables (see .env.example):

- `ORCHESTRATOR_OLLAMA_URL` - Ollama service URL
- `WORKER_API_URL` - Worker service URL
- `ORCHESTRATOR_MODEL` - LLM model (default: qwen2.5:14b)
- `STREAMING_ENABLED` - Enable SSE streaming
- `CONFIDENCE_THRESHOLD` - Minimum confidence (default: 0.7)

## Dependencies

- FastAPI - Web framework
- Ollama - LLM client
- SSE-Starlette - Server-Sent Events
- Pydantic - Data validation
- Loguru - Logging

See requirements.txt for full list.

---

**Part of AI RAG Batch 2**  
**Status**: Complete ✅  
**Next**: Worker Service (Batch 3)
