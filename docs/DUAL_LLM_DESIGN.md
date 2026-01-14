# Dual-LLM Architecture Design

**AI RAG System Design Document**

This document explains the dual-LLM orchestrator-worker architecture that powers the AI RAG system. This design solves the fundamental problem of rigid, regex-based query handling by using two specialized LLMs working in concert.

## Table of Contents

- [The Problem](#the-problem)
- [Why Dual-LLM?](#why-dual-llm)
- [Architecture Overview](#architecture-overview)
- [Component Deep-Dive](#component-deep-dive)
- [Communication Protocol](#communication-protocol)
- [Example Flows](#example-flows)
- [Benefits & Trade-offs](#benefits--trade-offs)
- [Performance Characteristics](#performance-characteristics)
- [Implementation Details](#implementation-details)

## The Problem

Traditional RAG systems face a fundamental challenge: **how do you handle diverse query types without writing extensive hardcoded rules?**

### Traditional Approach (Regex Hell)

```python
# Example from the original BYU policy system
if re.search(r'\b(?:per\s*diem|perdiem|daily\s+allowance)\b', question, re.I):
    # 50+ lines of regex to extract city/state
    match = re.search(r'for\s+([^,\?]+)(?:,\s*([A-Z]{2}))?', question, re.I)
    if match:
        city = match.group(1).strip().title()
        state = match.group(2).upper() if match.group(2) else None
        # Exact matching only - fails on variations
        # "Denver" (no state) ✗
        # "Arapahoe County" ✗
        # "denver, co" (lowercase) ✗
```

**Problems:**
1. Brittle - breaks on natural language variations
2. Doesn't scale - each query type needs extensive patterns
3. Hard to maintain - regex debugging is painful
4. No fuzzy matching - fails on typos, abbreviations, counties
5. Can't learn - must manually add patterns for new cases

### What We Need

✅ Natural language understanding (not pattern matching)  
✅ Fuzzy entity resolution (Denver → Denver, CO)  
✅ Self-validation (did I answer correctly?)  
✅ Extensible (easy to add new query types)  
✅ Deterministic where needed (structured data lookups)  
✅ Flexible where beneficial (open-ended questions)

## Why Dual-LLM?

We use **two specialized LLMs** instead of one monolithic model:

### Orchestrator LLM (The Planner)
**Model**: Lighter, faster (e.g., qwen2.5:14b, llama3:8b)  
**Role**: Strategic thinking and validation  
**Tasks**:
- Understand user intent
- Extract entities and parameters
- Plan query strategy
- Validate worker responses
- Stream thinking process to UI

**Why separate?** Intent classification needs speed more than knowledge. A 14B model can classify intent just as well as a 32B model, but 2x faster.

### Worker LLM (The Executor)
**Model**: Larger, smarter (e.g., qwen2.5:32b, qwen2.5:72b)  
**Role**: Knowledge work and generation  
**Tasks**:
- Execute RAG searches
- Perform structured lookups
- Build context from documents
- Generate final answers
- Provide citations

**Why separate?** Answer generation needs deep reasoning and broad knowledge. A larger model produces better, more accurate answers.

### Why Not Single LLM?

| Aspect | Single LLM | Dual LLM |
|--------|-----------|----------|
| **Speed** | Slower (always uses large model) | Faster (light model for planning) |
| **Cost** | Higher (large model for everything) | Lower (only use large when needed) |
| **Separation of Concerns** | Blurred responsibilities | Clear roles |
| **Validation** | Self-validation (less reliable) | External validation (more reliable) |
| **Scalability** | Monolithic | Microservices |
| **Debugging** | Harder (black box) | Easier (inspect each step) |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Web UI with SSE Streaming)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP POST /ask
                             │ {"question": "What is the rate for Denver?"}
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator API (Port 8000)                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                   Orchestrator LLM                          │ │
│ │                   (qwen2.5:14b)                             │ │
│ │                                                             │ │
│ │  Step 1: Intent Classification                             │ │
│ │  ┌──────────────────────────────────────────────────────┐  │ │
│ │  │ Input: "What is the rate for Denver?"                │  │ │
│ │  │                                                       │  │ │
│ │  │ Analysis:                                            │  │ │
│ │  │ - Intent: structured_lookup                         │  │ │
│ │  │ - Entity type: location_rate                        │  │ │
│ │  │ - Extracted: {location: "Denver, CO"}               │  │ │
│ │  │ - Confidence: 0.92                                  │  │ │
│ │  │                                                       │  │ │
│ │  │ Decision: Query worker for table lookup             │  │ │
│ │  └──────────────────────────────────────────────────────┘  │ │
│ │                                                             │ │
│ │  [Streams thinking to UI via SSE]                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP POST to Worker API
                             │ {"task": "structured_lookup", 
                             │  "params": {"location": "Denver, CO"}}
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Worker API (Port 8001)                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                      Worker LLM                             │ │
│ │                    (qwen2.5:32b)                            │ │
│ │                                                             │ │
│ │  Step 2: Task Execution                                    │ │
│ │  ┌──────────────────────────────────────────────────────┐  │ │
│ │  │ Task: structured_lookup                              │  │ │
│ │  │                                                       │  │ │
│ │  │ Fuzzy Matching:                                      │  │ │
│ │  │ - Input: "Denver"                                    │  │ │
│ │  │ - Normalized: "Denver, CO"                           │  │ │
│ │  │ - Searched Qdrant with filters                       │  │ │
│ │  │                                                       │  │ │
│ │  │ Result: Found entry                                  │  │ │
│ │  │ - Rate: $91                                          │  │ │
│ │  │ - Source: rates_table                                │  │ │
│ │  │ - URL: https://example.com/rates                     │  │ │
│ │  └──────────────────────────────────────────────────────┘  │ │
│ └─────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Returns structured result
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator API (Port 8000)                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │  Step 3: Response Validation                               │ │
│ │  ┌──────────────────────────────────────────────────────┐  │ │
│ │  │ Validation Checks:                                   │  │ │
│ │  │ ✓ Did worker find data?          Yes                │  │ │
│ │  │ ✓ Does it answer the question?   Yes (rate)         │  │ │
│ │  │ ✓ Is location correct?           Yes (Denver, CO)   │  │ │
│ │  │ ✓ Has source citation?           Yes (URL present)  │  │ │
│ │  │ ✓ Is format appropriate?         Yes                │  │ │
│ │  │                                                       │  │ │
│ │  │ Final Answer:                                        │  │ │
│ │  │ "The daily rate for Denver, CO is $91."             │  │ │
│ │  │                                                       │  │ │
│ │  │ [Streams final answer to UI]                        │  │ │
│ │  └──────────────────────────────────────────────────────┘  │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Component Deep-Dive

### 1. Orchestrator API

**Technology**: FastAPI (Python 3.11+)  
**Port**: 8000  
**LLM**: Lighter model (14B parameters)

**Responsibilities:**

#### Intent Classification
```python
def classify_intent(question: str) -> Classification:
    """
    Classifies user intent using orchestrator LLM.
    
    Returns:
        - intent_type: "structured_lookup" | "general_rag" | "clarification"
        - entity_type: "location_rate" | "policy" | "deadline" | etc.
        - extracted_params: dict of extracted entities
        - confidence: 0.0 to 1.0
    """
```

Intent types:
- `structured_lookup`: Query structured data (tables, databases)
- `general_rag`: Open-ended question requiring RAG
- `clarification_needed`: Ambiguous, needs more info
- `multi_step`: Requires multiple queries
- `comparison`: Compare multiple entities

#### Query Planning
```python
def plan_query(classification: Classification) -> QueryPlan:
    """
    Plans how to execute the query based on intent.
    
    For structured lookups:
        - Single worker call with parameters
    
    For general RAG:
        - Vector search + context building
    
    For multi-step:
        - Series of worker calls with dependencies
    """
```

#### Response Validation
```python
def validate_response(
    question: str,
    worker_response: dict,
    plan: QueryPlan
) -> ValidationResult:
    """
    Validates worker response against original question.
    
    Checks:
        1. Did worker find data?
        2. Does answer address the question?
        3. Are citations present?
        4. Is format appropriate?
        5. Are extracted entities correct?
    
    Returns:
        - is_valid: bool
        - issues: List[str]  (if any)
        - final_answer: str  (formatted)
    """
```

#### Streaming Handler
```python
def stream_thinking_process(steps: Iterator[ThinkingStep]):
    """
    Streams AI thinking process to frontend via SSE.
    
    Events:
        - thought: Orchestrator reasoning
        - action: What it's about to do
        - observation: What it learned
        - validation: Checking response quality
        - final_answer: The answer
    """
```

### 2. Worker API

**Technology**: FastAPI (Python 3.11+)  
**Port**: 8001  
**LLM**: Larger model (32B parameters)

**Responsibilities:**

#### RAG Engine
```python
def execute_rag_search(
    question: str,
    top_k: int = 8
) -> RAGResult:
    """
    Performs semantic search and generates answer.
    
    Steps:
        1. Embed question
        2. Search Qdrant for similar chunks
        3. Build context from top-k results
        4. Generate answer using worker LLM
        5. Extract citations
    """
```

#### Structured Lookup
```python
def structured_lookup(
    entity_type: str,
    params: dict
) -> LookupResult:
    """
    Performs structured data lookup with fuzzy matching.
    
    For location_rate:
        1. Normalize location (handle abbreviations, counties)
        2. Try exact match in Qdrant
        3. Try fuzzy match if exact fails
        4. Try state default if fuzzy fails
        5. Return structured data + source
    
    For other entity types:
        - Similar fuzzy matching logic
        - Type-specific normalization
    """
```

#### Context Builder
```python
def build_context(
    chunks: List[Chunk],
    max_tokens: int = 8000
) -> str:
    """
    Builds context from retrieved chunks.
    
    Steps:
        1. Deduplicate similar chunks
        2. Rank by relevance
        3. Truncate to fit token limit
        4. Format with source attribution
    """
```

### 3. Qdrant Vector Database

**Technology**: Qdrant (Rust-based vector DB)  
**Port**: 6333  

**Collections:**
- `documents`: Main document chunks
- Each point has:
  - Vector (384-dim embedding)
  - Payload (text, metadata, url, etc.)
  - Optional: Structured data fields

**Query Types:**
```python
# Semantic search
results = qdrant.search(
    collection_name="documents",
    query_vector=embed(question),
    limit=8
)

# Filtered search (structured data)
results = qdrant.search(
    collection_name="documents",
    query_vector=embed(question),
    query_filter=Filter(
        must=[
            FieldCondition(key="type", match="rate_table"),
            FieldCondition(key="location", match="Denver, CO")
        ]
    )
)
```

## Communication Protocol

### Request/Response Format

#### Orchestrator → Worker

```json
{
  "task_type": "structured_lookup" | "rag_search" | "fuzzy_match",
  "params": {
    "entity_type": "location_rate",
    "location": "Denver, CO",
    "context": "looking for daily rate"
  },
  "config": {
    "top_k": 8,
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "trace_id": "uuid-for-logging"
}
```

#### Worker → Orchestrator

```json
{
  "success": true,
  "result": {
    "data": {
      "location": "Denver, CO",
      "rate": 91,
      "currency": "USD",
      "period": "daily"
    },
    "confidence": 0.95,
    "source": {
      "url": "https://example.com/rates",
      "title": "Rate Table 2025-2026",
      "retrieved_at": "2025-01-14T02:00:00Z"
    }
  },
  "trace_id": "uuid-for-logging"
}
```

#### Orchestrator → Frontend (SSE)

```
event: thought
data: {"step": 1, "content": "User is asking about rates for Denver"}

event: action
data: {"step": 2, "content": "Querying worker for structured lookup"}

event: observation
data: {"step": 3, "content": "Worker found rate: $91"}

event: validation
data: {"step": 4, "content": "Response valid, includes source"}

event: final_answer
data: {"answer": "The daily rate for Denver, CO is $91.", "citations": [...]}
```

## Example Flows

### Flow 1: Structured Lookup (Per Diem)

**User**: *"What is the per diem for Arapahoe County, Colorado?"*

```
┌─ Orchestrator ─────────────────────────────────────┐
│ Thought: User wants per diem rate for a location  │
│ Classification:                                    │
│   - Intent: structured_lookup                      │
│   - Entity: location_rate                          │
│   - Location: "Arapahoe County, Colorado"          │
│   - Confidence: 0.94                               │
│                                                     │
│ Plan: Query worker with location                   │
└────────────────────────────────────────────────────┘
           │
           ▼
┌─ Worker ───────────────────────────────────────────┐
│ Fuzzy Matching:                                    │
│ 1. Input: "Arapahoe County, Colorado"              │
│ 2. Check aliases: Arapahoe County → Aurora, CO     │
│ 3. Search Qdrant with filters:                     │
│    - type: rate_table                              │
│    - location: Aurora, CO                          │
│ 4. Found: $91/day                                  │
│                                                     │
│ Return: {rate: 91, location: "Aurora, CO", ...}    │
└────────────────────────────────────────────────────┘
           │
           ▼
┌─ Orchestrator ─────────────────────────────────────┐
│ Validation:                                        │
│ ✓ Worker found data                                │
│ ✓ Answer addresses "per diem for Arapahoe County" │
│ ✓ Includes source citation                         │
│ ✓ Format is appropriate                            │
│                                                     │
│ Final: "The daily per diem rate for Arapahoe      │
│        County (Aurora), CO is $91."                │
└────────────────────────────────────────────────────┘
```

### Flow 2: General RAG Query

**User**: *"What are the documentation standards?"*

```
┌─ Orchestrator ─────────────────────────────────────┐
│ Thought: Open-ended question about policies        │
│ Classification:                                    │
│   - Intent: general_rag                            │
│   - Topic: documentation_standards                 │
│   - Confidence: 0.88                               │
│                                                     │
│ Plan: RAG search + answer generation               │
└────────────────────────────────────────────────────┘
           │
           ▼
┌─ Worker ───────────────────────────────────────────┐
│ RAG Execution:                                     │
│ 1. Embed: "documentation standards"                │
│ 2. Search Qdrant: top 8 chunks                     │
│ 3. Build context: ~3000 tokens                     │
│ 4. Generate answer using LLM                       │
│ 5. Extract citations                               │
│                                                     │
│ Return: {answer: "...", citations: [...]}          │
└────────────────────────────────────────────────────┘
           │
           ▼
┌─ Orchestrator ─────────────────────────────────────┐
│ Validation:                                        │
│ ✓ Answer is coherent                               │
│ ✓ Addresses documentation standards                │
│ ✓ Has multiple citations                           │
│ ✓ Appropriate length                               │
│                                                     │
│ Final: [Generated answer with citations]           │
└────────────────────────────────────────────────────┘
```

### Flow 3: Ambiguous Query (Needs Clarification)

**User**: *"What's the rate?"*

```
┌─ Orchestrator ─────────────────────────────────────┐
│ Thought: Query is ambiguous - what rate?           │
│ Classification:                                    │
│   - Intent: clarification_needed                   │
│   - Missing: rate_type, location                   │
│   - Confidence: 0.71                               │
│                                                     │
│ Plan: Ask for clarification                        │
│                                                     │
│ Response: "I'd be happy to help with rates! Could  │
│            you specify which type of rate you're   │
│            looking for (e.g., per diem, mileage)   │
│            and the location?"                      │
└────────────────────────────────────────────────────┘
```

## Benefits & Trade-offs

### Benefits

✅ **No Regex Required**
- Natural language understanding replaces pattern matching
- Handles variations automatically
- Learns from context

✅ **Fuzzy Matching Built-in**
- "Denver" → "Denver, CO"
- "Arapahoe County" → "Aurora, CO"
- Handles typos and abbreviations

✅ **Self-Validating**
- Orchestrator checks worker responses
- Ensures answers are complete and accurate
- Catches hallucinations

✅ **Scalable**
- Add new query types without code changes
- Just define intent in orchestrator prompt
- Worker handles execution automatically

✅ **Debuggable**
- Each step is logged and visible
- UI shows thinking process
- Easy to identify where things go wrong

✅ **Optimized Performance**
- Light model for fast classification
- Heavy model only when needed
- Parallel processing possible

### Trade-offs

⚠️ **Increased Latency**
- Two LLM calls vs. one
- ~500ms orchestrator + ~2s worker = ~2.5s total
- Mitigated by streaming (perceived as faster)

⚠️ **More Complex**
- Two services to manage
- More moving parts
- Requires understanding of both roles

⚠️ **Higher Resource Usage**
- Two LLMs loaded simultaneously
- ~30GB VRAM for dual 32B models
- More CPU/RAM overhead

⚠️ **Potential Consistency Issues**
- Orchestrator and worker must stay in sync
- Version mismatches can cause problems
- Need good error handling

## Performance Characteristics

### Latency Breakdown

```
Total: ~2.5 seconds (with streaming)

Orchestrator Classification:  500ms
├─ LLM inference:              400ms
└─ Processing:                 100ms

Worker Execution:              2000ms
├─ Vector search:              50ms
├─ Context building:           100ms
├─ LLM inference:              1800ms
└─ Post-processing:            50ms
```

### Optimization Strategies

1. **Caching**
   - Cache intent classification for similar questions
   - Cache worker responses for common queries
   - Reduces repeat latency to ~100ms

2. **Parallel Processing**
   - Multiple worker instances
   - Load balancing across GPUs
   - 10x throughput increase

3. **Model Selection**
   - Use quantized models (Q4_K_M) for 2x speedup
   - Trade minimal quality for performance
   - Still better than regex approach

4. **Streaming**
   - Start showing orchestrator thinking immediately
   - User sees progress, feels faster
   - Reduces perceived latency by 50%

## Implementation Details

### Model Loading

```python
# Orchestrator (14B model, ~9GB VRAM)
orchestrator_llm = OllamaClient(
    base_url="http://orchestrator-ollama:11434",
    model="qwen2.5:14b",
    temperature=0.3  # Lower for consistency
)

# Worker (32B model, ~20GB VRAM)
worker_llm = OllamaClient(
    base_url="http://worker-ollama:11434",
    model="qwen2.5:32b",
    temperature=0.7  # Higher for creativity
)
```

### Prompting Strategy

**Orchestrator System Prompt:**
```
You are an AI orchestrator that classifies user intents and validates responses.

Your job:
1. Classify the intent of user questions
2. Extract relevant parameters
3. Validate worker responses

Respond in JSON format:
{
  "intent": "structured_lookup" | "general_rag" | "clarification_needed",
  "entity_type": "location_rate" | "policy" | etc.,
  "params": {...},
  "confidence": 0.0 to 1.0
}
```

**Worker System Prompt:**
```
You are an AI assistant that executes tasks and answers questions.

Given a task and parameters, perform the requested operation:
- structured_lookup: Find data in tables/databases
- rag_search: Search documents and generate answers
- fuzzy_match: Normalize and match entities

Always provide sources and be precise.
```

### Error Handling

```python
def orchestrate_query(question: str) -> Response:
    try:
        # Step 1: Classify
        classification = orchestrator.classify(question)
        
        if classification.confidence < 0.7:
            return ask_for_clarification(question)
        
        # Step 2: Execute
        result = worker.execute(
            task_type=classification.intent,
            params=classification.params
        )
        
        # Step 3: Validate
        validation = orchestrator.validate(question, result)
        
        if not validation.is_valid:
            # Retry with different strategy
            return retry_with_fallback(question)
        
        return format_response(validation.final_answer)
        
    except WorkerTimeoutError:
        return fallback_to_simple_rag(question)
    except ValidationError as e:
        return ask_for_clarification(question, hint=str(e))
```

## Conclusion

The dual-LLM architecture solves the fundamental problem of rigid query handling by combining:

1. **Fast intent classification** (orchestrator)
2. **Deep knowledge execution** (worker)
3. **Self-validation** (orchestrator reviews worker)
4. **Streaming UX** (visible AI thinking)

This creates a system that is:
- More flexible than regex
- More accurate than single-LLM
- More debuggable than black-box
- More scalable than monolithic

The trade-off in latency and complexity is worth it for the dramatic improvement in query handling capability.

---

**Next**: See actual implementation in Batch 2 (Orchestrator) and Batch 3 (Worker)
