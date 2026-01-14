# Development Guide

Guide for developers working on AI RAG.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- Text editor (VS Code recommended)

### Setup

```bash
# Clone
git clone https://github.com/your-org/airag.git
cd airag

# Setup development environment
./tools/setup.sh --dev

# Start in dev mode
./tools/dev.sh start
```

## Project Structure

```
airag/
├── services/              # Microservices
│   ├── orchestrator/     # Intent classification
│   ├── worker/           # RAG execution
│   ├── crawler/          # Content ingestion
│   └── frontend/         # Web UI
├── tools/                # CLI tools
├── docs/                 # Documentation
├── examples/             # Example code
├── docker-compose.yml    # Main compose file
└── .env.example         # Configuration template
```

## Development Workflow

### 1. Make Changes

```bash
# Edit code
vim services/orchestrator/app.py

# Changes auto-reload (thanks to dev mode!)
```

### 2. Test Locally

```bash
# Test endpoint
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'

# Run test suite
./tools/test-endpoints.sh
```

### 3. View Logs

```bash
# All services
./tools/dev.sh logs

# Specific service
./tools/dev.sh logs orchestrator-api
```

### 4. Rebuild if Needed

```bash
# Rebuild single service
./tools/dev.sh rebuild orchestrator-api

# Rebuild all
docker-compose build
```

## Code Style

### Python

Follow PEP 8:

```python
# Good
def process_question(question: str) -> dict:
    """Process user question."""
    result = classify_intent(question)
    return result

# Bad
def ProcessQuestion(q):
    r=classify_intent(q)
    return r
```

### JavaScript

Use modern ES6+:

```javascript
// Good
const askQuestion = async (question) => {
    const response = await fetch('/api/ask', {
        method: 'POST',
        body: JSON.stringify({question})
    });
    return response.json();
};

// Bad
function askQuestion(question) {
    return fetch('/api/ask', {
        method: 'POST',
        body: JSON.stringify({question: question})
    }).then(function(response) {
        return response.json();
    });
}
```

## Testing

### Manual Testing

```bash
# Start services
./tools/dev.sh start

# Test in browser
open http://localhost:8080

# Test API
curl http://localhost:8000/ask
```

### Automated Testing

```bash
# Run endpoint tests
./tools/test-endpoints.sh
```

## Common Tasks

### Adding a New Intent Type

1. Edit `services/orchestrator/lib/intent_classifier.py`:

```python
class IntentType(str, Enum):
    # ... existing types ...
    NEW_TYPE = "new_type"  # Add new type
```

2. Update orchestrator to handle it:

```python
if classification.intent_type == IntentType.NEW_TYPE:
    # Handle new intent
    pass
```

3. Test:

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"question": "test new intent"}'
```

### Adding a New Parser

1. Create parser in `services/crawler/parsers/`:

```python
from .base import BaseParser

class NewParser(BaseParser):
    def parse(self, content, url):
        # Extract content
        text = extract_text(content)
        
        # Create document
        return self._create_document(
            text=text,
            title="Title",
            url=url,
            doc_type="new_type"
        )
```

2. Register in `__init__.py`:

```python
from .new_parser import NewParser

__all__ = ["NewParser", ...]
```

3. Use in crawler:

```python
from parsers import NewParser

parser = NewParser()
doc = parser.parse(content, url)
```

## Debugging

### Python Debugging

Add breakpoint:

```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger.

### Viewing Database

```bash
# Qdrant UI
open http://localhost:6333/dashboard

# Query directly
curl http://localhost:6333/collections/documents
```

### Checking Logs

```bash
# Real-time logs
docker-compose logs -f orchestrator-api

# Last 100 lines
docker-compose logs --tail=100 worker-api
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Git Workflow

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/new-feature

# Make changes
vim services/orchestrator/app.py

# Commit
git add .
git commit -m "Add new feature"

# Push
git push origin feature/new-feature

# Create PR on GitHub
```

---

**Part of AI RAG Batch 7**  
**Status**: Complete ✅
