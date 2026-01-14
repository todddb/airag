#!/usr/bin/env bash
# =============================================================================
# API Endpoint Testing Script
# =============================================================================
# Tests all API endpoints to verify system is working

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_header() {
    echo
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# =============================================================================
# Test Functions
# =============================================================================

test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=$4
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        print_success "OK ($http_code)"
        return 0
    else
        print_error "FAIL ($http_code)"
        return 1
    fi
}

# =============================================================================
# Orchestrator Tests
# =============================================================================

test_orchestrator() {
    print_header "Testing Orchestrator API (Port 8000)"
    
    local base_url="http://localhost:8000"
    local passed=0
    local failed=0
    
    # Health check
    if test_endpoint "Health Check" "$base_url/health"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Root endpoint
    if test_endpoint "Root Endpoint" "$base_url/"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Classify endpoint
    local classify_data='{"question": "What is the per diem rate for Denver?"}'
    if test_endpoint "Classify Intent" "$base_url/classify" "POST" "$classify_data"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Ask endpoint (non-streaming)
    local ask_data='{"question": "Hello, how are you?", "stream": false}'
    if test_endpoint "Ask Question" "$base_url/ask" "POST" "$ask_data"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    echo
    echo "Orchestrator: $passed passed, $failed failed"
    return $failed
}

# =============================================================================
# Worker Tests
# =============================================================================

test_worker() {
    print_header "Testing Worker API (Port 8001)"
    
    local base_url="http://localhost:8001"
    local passed=0
    local failed=0
    
    # Health check
    if test_endpoint "Health Check" "$base_url/health"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Root endpoint
    if test_endpoint "Root Endpoint" "$base_url/"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    echo
    echo "Worker: $passed passed, $failed failed"
    return $failed
}

# =============================================================================
# Frontend Tests
# =============================================================================

test_frontend() {
    print_header "Testing Frontend (Port 8080)"
    
    local base_url="http://localhost:8080"
    local passed=0
    local failed=0
    
    # Health check
    if test_endpoint "Health Check" "$base_url/health"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Main page
    if test_endpoint "Main Page" "$base_url/"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # CSS file
    if test_endpoint "Styles CSS" "$base_url/css/styles.css"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # JS file
    if test_endpoint "App JS" "$base_url/js/app.js"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    echo
    echo "Frontend: $passed passed, $failed failed"
    return $failed
}

# =============================================================================
# Qdrant Tests
# =============================================================================

test_qdrant() {
    print_header "Testing Qdrant (Port 6333)"
    
    local base_url="http://localhost:6333"
    local passed=0
    local failed=0
    
    # Health check
    if test_endpoint "Health Check" "$base_url/health"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Collections list
    if test_endpoint "List Collections" "$base_url/collections"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    echo
    echo "Qdrant: $passed passed, $failed failed"
    return $failed
}

# =============================================================================
# Ollama Tests
# =============================================================================

test_ollama() {
    print_header "Testing Ollama Services"
    
    local passed=0
    local failed=0
    
    # Orchestrator Ollama
    if test_endpoint "Orchestrator Ollama" "http://localhost:11434/"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Worker Ollama
    if test_endpoint "Worker Ollama" "http://localhost:11435/"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    echo
    echo "Ollama: $passed passed, $failed failed"
    return $failed
}

# =============================================================================
# Integration Tests
# =============================================================================

test_integration() {
    print_header "Integration Tests"
    
    local passed=0
    local failed=0
    
    # Full question flow
    echo -n "Testing full question flow... "
    
    local question='{"question": "What is 2+2?", "stream": false}'
    response=$(curl -s -X POST http://localhost:8000/ask \
        -H "Content-Type: application/json" \
        -d "$question")
    
    if echo "$response" | jq -e '.answer' > /dev/null 2>&1; then
        print_success "OK"
        ((passed++))
        
        # Show answer
        answer=$(echo "$response" | jq -r '.answer')
        print_info "Answer: ${answer:0:100}..."
    else
        print_error "FAIL"
        ((failed++))
    fi
    
    echo
    echo "Integration: $passed passed, $failed failed"
    return $failed
}

# =============================================================================
# Summary
# =============================================================================

print_summary() {
    local total_failed=$1
    
    print_header "Test Summary"
    
    if [ "$total_failed" -eq 0 ]; then
        print_success "All tests passed!"
        echo
        print_info "System is fully operational"
        echo
        echo "URLs:"
        echo "  Frontend:      http://localhost:8080"
        echo "  Orchestrator:  http://localhost:8000"
        echo "  Worker:        http://localhost:8001"
        echo "  Qdrant:        http://localhost:6333"
        return 0
    else
        print_error "$total_failed test(s) failed"
        echo
        print_info "Check that all services are running:"
        echo "  ./tools/airagctl status"
        return 1
    fi
}

# =============================================================================
# Main
# =============================================================================

main() {
    print_header "AI RAG Endpoint Testing"
    
    local total_failed=0
    
    # Run all tests
    test_orchestrator || ((total_failed+=$?))
    test_worker || ((total_failed+=$?))
    test_frontend || ((total_failed+=$?))
    test_qdrant || ((total_failed+=$?))
    test_ollama || ((total_failed+=$?))
    test_integration || ((total_failed+=$?))
    
    # Summary
    print_summary $total_failed
    
    exit $total_failed
}

# Check for dependencies
if ! command -v curl &> /dev/null; then
    print_error "curl not found"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    print_error "jq not found (optional but recommended)"
fi

main "$@"
