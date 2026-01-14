#!/usr/bin/env bash
# =============================================================================
# cURL API Examples
# =============================================================================
# Collection of cURL commands for testing the AI RAG API

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Base URLs
ORCHESTRATOR_URL="http://localhost:8000"
WORKER_URL="http://localhost:8001"

echo -e "${BLUE}AI RAG - cURL Examples${NC}"
echo "========================================"

# =============================================================================
# Health Checks
# =============================================================================

echo -e "\n${GREEN}1. Health Check - Orchestrator${NC}"
curl -s "$ORCHESTRATOR_URL/health" | jq .

echo -e "\n${GREEN}2. Health Check - Worker${NC}"
curl -s "$WORKER_URL/health" | jq .

# =============================================================================
# Basic Query
# =============================================================================

echo -e "\n${GREEN}3. Basic Query (Non-Streaming)${NC}"
curl -s -X POST "$ORCHESTRATOR_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the per diem rate for Denver?",
    "stream": false
  }' | jq .

# =============================================================================
# Streaming Query
# =============================================================================

echo -e "\n${GREEN}4. Streaming Query (SSE)${NC}"
curl -s -X POST "$ORCHESTRATOR_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the travel policies?",
    "stream": true
  }'

# =============================================================================
# Intent Classification
# =============================================================================

echo -e "\n${GREEN}5. Classify Intent${NC}"
curl -s -X POST "$ORCHESTRATOR_URL/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the per diem rate for Seattle?"
  }' | jq .

# =============================================================================
# Multiple Questions
# =============================================================================

echo -e "\n${GREEN}6. Multiple Questions${NC}"

questions=(
  "What is the per diem rate for Denver?"
  "What is the per diem rate for Seattle?"
  "What are the travel policies?"
)

for question in "${questions[@]}"; do
  echo -e "\nQuestion: $question"
  curl -s -X POST "$ORCHESTRATOR_URL/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$question\", \"stream\": false}" \
    | jq -r '.answer'
done

# =============================================================================
# Worker Direct Access (Testing)
# =============================================================================

echo -e "\n${GREEN}7. Worker - RAG Search${NC}"
curl -s -X POST "$WORKER_URL/rag_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "travel policies",
    "top_k": 5
  }' | jq .

echo -e "\n${GREEN}8. Worker - Structured Lookup${NC}"
curl -s -X POST "$WORKER_URL/structured_lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "location_rate",
    "entity": "Denver"
  }' | jq .

# =============================================================================
# Error Handling
# =============================================================================

echo -e "\n${GREEN}9. Error Handling - Invalid Request${NC}"
curl -s -X POST "$ORCHESTRATOR_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "invalid_field": "test"
  }' | jq .

# =============================================================================
# Rate Limiting Test
# =============================================================================

echo -e "\n${GREEN}10. Rate Limiting Test (10 rapid requests)${NC}"
for i in {1..10}; do
  echo -n "Request $i: "
  response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$ORCHESTRATOR_URL/ask" \
    -H "Content-Type: application/json" \
    -d '{"question": "test", "stream": false}')
  echo "HTTP $response"
done

# =============================================================================
# Streaming with Processing
# =============================================================================

echo -e "\n${GREEN}11. Streaming with Line-by-Line Processing${NC}"
curl -s -X POST "$ORCHESTRATOR_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the mileage rate?",
    "stream": true
  }' | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
      echo "$line" | sed 's/data: //' | jq -r '.content // empty'
    fi
  done

echo -e "\n${BLUE}Examples complete!${NC}"
