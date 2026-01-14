# API Reference

Complete API documentation for all AI RAG services.

## Table of Contents

1. [Orchestrator API](#orchestrator-api)
2. [Worker API](#worker-api)
3. [Common Patterns](#common-patterns)
4. [Error Handling](#error-handling)

## Orchestrator API

Base URL: `http://localhost:8000`

### POST /ask

Main question answering endpoint.

**Request:**
```json
{
  "question": "What is the per diem rate for Denver?",
  "stream": true
}
```

**Response (Non-Streaming):**
```json
{
  "answer": "The daily rate for Denver, CO is $91.",
  "citations": [...],
  "confidence": 0.92
}
```

**Response (Streaming - SSE):**
```
event: thought
data: {"content": "Analyzing..."}

event: final_answer
data: {"content": "Answer", "data": {"citations": [...]}}
```

### GET /health

Health check.

**Response:**
```json
{
  "status": "healthy",
  "model": "qwen2.5:14b"
}
```

## Worker API

Base URL: `http://localhost:8001`

### POST /execute

Execute task (called by orchestrator).

**Request:**
```json
{
  "task_type": "structured_lookup",
  "question": "What is the rate for Denver?",
  "params": {"location": "Denver"}
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "answer": "The rate for Denver, CO is $91",
    "citations": [...]
  }
}
```

## Common Patterns

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={"question": "test", "stream": false}
)
print(response.json())
```

### cURL Example

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "stream": false}'
```

## Error Handling

All errors return:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

---

**Part of AI RAG Batch 7**  
**Status**: Complete ✅
