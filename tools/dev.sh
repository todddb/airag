#!/usr/bin/env bash
# =============================================================================
# Development Helper Script
# =============================================================================
# Streamlines development workflow

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# =============================================================================
# Development Mode
# =============================================================================

start_dev() {
    print_header "Starting Development Environment"
    
    cd "$PROJECT_ROOT"
    
    # Check if dev compose exists
    if [ ! -f docker-compose.dev.yml ]; then
        print_info "Creating dev compose file..."
        cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

# Development overrides
services:
  orchestrator-api:
    environment:
      - DEV_MODE=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./services/orchestrator:/app
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload

  worker-api:
    environment:
      - DEV_MODE=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./services/worker:/app
    command: uvicorn app:app --host 0.0.0.0 --port 8001 --reload

  frontend:
    volumes:
      - ./services/frontend:/usr/share/nginx/html:ro
EOF
    fi
    
    print_info "Starting services with hot reload..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up
}

# =============================================================================
# Testing
# =============================================================================

run_tests() {
    print_header "Running Tests"
    
    cd "$PROJECT_ROOT"
    
    # Test orchestrator
    print_info "Testing Orchestrator API..."
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Orchestrator: OK"
    else
        echo "Orchestrator: FAIL"
    fi
    
    # Test worker
    print_info "Testing Worker API..."
    if curl -s http://localhost:8001/health > /dev/null; then
        print_success "Worker: OK"
    else
        echo "Worker: FAIL"
    fi
    
    # Test frontend
    print_info "Testing Frontend..."
    if curl -s http://localhost:8080/health > /dev/null; then
        print_success "Frontend: OK"
    else
        echo "Frontend: FAIL"
    fi
}

# =============================================================================
# Logs
# =============================================================================

watch_logs() {
    local service=$1
    
    cd "$PROJECT_ROOT"
    
    if [ -z "$service" ]; then
        docker compose logs -f
    else
        docker compose logs -f "$service"
    fi
}

# =============================================================================
# Rebuild
# =============================================================================

rebuild_service() {
    local service=$1
    
    if [ -z "$service" ]; then
        echo "Usage: $0 rebuild <service>"
        exit 1
    fi
    
    print_header "Rebuilding $service"
    
    cd "$PROJECT_ROOT"
    
    print_info "Stopping service..."
    docker compose stop "$service"
    
    print_info "Rebuilding..."
    docker compose build "$service"
    
    print_info "Starting service..."
    docker compose up -d "$service"
    
    print_success "Rebuild complete"
}

# =============================================================================
# Shell Access
# =============================================================================

shell() {
    local service=$1
    
    if [ -z "$service" ]; then
        echo "Available services:"
        docker compose ps --services
        echo
        echo "Usage: $0 shell <service>"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    docker compose exec "$service" /bin/bash
}

# =============================================================================
# Help
# =============================================================================

show_help() {
    cat << EOF
${CYAN}dev.sh${NC} - Development Helper

${YELLOW}Usage:${NC}
  ./dev.sh <command>

${YELLOW}Commands:${NC}
  start              Start in development mode (hot reload)
  test               Run health checks
  logs [service]     Watch logs (optional: specify service)
  rebuild <service>  Rebuild specific service
  shell <service>    Open shell in service container

${YELLOW}Examples:${NC}
  ./dev.sh start
  ./dev.sh logs orchestrator-api
  ./dev.sh rebuild worker-api
  ./dev.sh shell orchestrator-api

EOF
}

# =============================================================================
# Main
# =============================================================================

main() {
    if [ $# -eq 0 ]; then
        start_dev
        exit 0
    fi
    
    case "$1" in
        start)
            start_dev
            ;;
        test)
            run_tests
            ;;
        logs)
            watch_logs "$2"
            ;;
        rebuild)
            rebuild_service "$2"
            ;;
        shell)
            shell "$2"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
