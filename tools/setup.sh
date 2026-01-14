#!/usr/bin/env bash
# =============================================================================
# AI RAG Setup Script
# =============================================================================
# Easy setup for the AI RAG system
#
# Usage:
#   ./setup.sh                  Interactive setup
#   ./setup.sh --quick          Quick setup with defaults
#   ./setup.sh --dev            Development setup

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# =============================================================================
# Checks
# =============================================================================

check_requirements() {
    print_header "Checking Requirements"
    
    local all_good=true
    
    # Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker $docker_version"
    else
        print_error "Docker not found"
        all_good=false
    fi
    
    # Docker Compose
    if docker compose version &> /dev/null 2>&1; then
        local compose_version=$(docker compose version | cut -d' ' -f4)
        print_success "Docker Compose $compose_version"
    else
        print_error "Docker Compose not found"
        all_good=false
    fi
    
    # jq (optional but recommended)
    if command -v jq &> /dev/null; then
        print_success "jq installed"
    else
        print_warning "jq not found (optional, recommended for JSON parsing)"
    fi
    
    # curl
    if command -v curl &> /dev/null; then
        print_success "curl installed"
    else
        print_error "curl not found"
        all_good=false
    fi
    
    if [ "$all_good" = false ]; then
        echo
        print_error "Missing required dependencies"
        echo
        echo "Please install:"
        echo "  - Docker: https://docs.docker.com/get-docker/"
        echo "  - Docker Compose: https://docs.docker.com/compose/install/"
        echo "  - curl: sudo apt-get install curl"
        echo
        exit 1
    fi
    
    print_success "All requirements met"
}

check_ports() {
    print_header "Checking Ports"
    
    local ports=(8000 8001 8080 6333 11434 11435)
    local port_names=("Orchestrator" "Worker" "Frontend" "Qdrant" "Orchestrator-Ollama" "Worker-Ollama")
    local all_good=true
    
    for i in "${!ports[@]}"; do
        local port=${ports[$i]}
        local name=${port_names[$i]}
        
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_warning "Port $port ($name) already in use"
            all_good=false
        else
            print_success "Port $port ($name) available"
        fi
    done
    
    if [ "$all_good" = false ]; then
        echo
        print_warning "Some ports are in use. Services may fail to start."
        read -p "Continue anyway? (y/n): " continue
        if [ "$continue" != "y" ]; then
            exit 1
        fi
    fi
}

# =============================================================================
# Configuration
# =============================================================================

configure_env() {
    print_header "Configuring Environment"
    
    cd "$PROJECT_ROOT"
    
    if [ -f .env ]; then
        print_warning ".env file already exists"
        read -p "Overwrite? (y/n): " overwrite
        if [ "$overwrite" != "y" ]; then
            print_info "Keeping existing .env"
            return
        fi
    fi
    
    print_info "Creating .env from template..."
    cp .env.example .env
    
    # Detect GPU
    if command -v nvidia-smi &> /dev/null; then
        print_success "NVIDIA GPU detected"
        print_info "GPU acceleration will be enabled"
    else
        print_warning "No NVIDIA GPU detected"
        print_info "Using CPU (slower performance)"
        # Update .env to disable GPU
        sed -i 's/ENABLE_GPU=true/ENABLE_GPU=false/' .env
    fi
    
    print_success "Environment configured"
}

# =============================================================================
# Setup
# =============================================================================

pull_images() {
    print_header "Pulling Base Images"
    
    cd "$PROJECT_ROOT"
    
    print_info "This may take a few minutes..."
    docker compose pull
    
    print_success "Base images pulled"
}

build_images() {
    print_header "Building Services"
    
    cd "$PROJECT_ROOT"
    
    print_info "Building Docker images..."
    print_info "This may take 5-10 minutes on first run..."
    docker compose build
    
    print_success "Services built"
}

pull_models() {
    print_header "Pulling LLM Models"
    
    cd "$PROJECT_ROOT"
    
    print_info "Starting Ollama services..."
    docker compose up -d orchestrator-ollama worker-ollama
    
    sleep 5
    
    print_info "Pulling orchestrator model (qwen2.5:14b)..."
    docker compose exec orchestrator-ollama ollama pull qwen2.5:14b
    
    print_info "Pulling worker model (qwen2.5:32b)..."
    docker compose exec worker-ollama ollama pull qwen2.5:32b
    
    print_success "Models pulled"
    
    docker compose stop orchestrator-ollama worker-ollama
}

setup_tools() {
    print_header "Setting Up Tools"
    
    # Make scripts executable
    chmod +x "$SCRIPT_DIR"/airagctl
    chmod +x "$SCRIPT_DIR"/dev.sh
    chmod +x "$SCRIPT_DIR"/backup.sh
    chmod +x "$SCRIPT_DIR"/test-endpoints.sh
    
    print_success "Tools configured"
    
    # Add to PATH suggestion
    echo
    print_info "To use 'airagctl' from anywhere, add to your PATH:"
    echo "  export PATH=\"\$PATH:$SCRIPT_DIR\""
    echo
    print_info "Or create a symlink:"
    echo "  sudo ln -s $SCRIPT_DIR/airagctl /usr/local/bin/airagctl"
}

# =============================================================================
# Main Setup
# =============================================================================

quick_setup() {
    print_header "AI RAG Quick Setup"
    
    check_requirements
    configure_env
    pull_images
    build_images
    setup_tools
    
    print_header "Setup Complete!"
    print_success "AI RAG is ready to use"
    echo
    print_info "Next steps:"
    echo "  1. Start services:  ./tools/airagctl start"
    echo "  2. Crawl content:   ./tools/airagctl crawl https://example.com"
    echo "  3. Open frontend:   http://localhost:8080"
    echo
    print_info "For help:  ./tools/airagctl help"
}

full_setup() {
    print_header "AI RAG Full Setup"
    
    check_requirements
    check_ports
    configure_env
    pull_images
    build_images
    
    # Ask about pulling models
    echo
    read -p "Pull LLM models now? (requires ~20GB, takes 10-30 min) (y/n): " pull_models_now
    if [ "$pull_models_now" = "y" ]; then
        pull_models
    else
        print_info "You can pull models later with: ./tools/airagctl start"
    fi
    
    setup_tools
    
    print_header "Setup Complete!"
    print_success "AI RAG is ready to use"
    echo
    print_info "Next steps:"
    echo "  1. Start services:  ./tools/airagctl start"
    echo "  2. Crawl content:   ./tools/airagctl crawl https://example.com"
    echo "  3. Open frontend:   http://localhost:8080"
    echo
    print_info "For help:  ./tools/airagctl help"
}

dev_setup() {
    print_header "AI RAG Development Setup"
    
    check_requirements
    configure_env
    
    # Enable dev mode in .env
    if [ -f "$PROJECT_ROOT/.env" ]; then
        echo "DEV_MODE=true" >> "$PROJECT_ROOT/.env"
    fi
    
    build_images
    setup_tools
    
    print_header "Dev Setup Complete!"
    print_success "Development environment ready"
    echo
    print_info "Start in dev mode:"
    echo "  ./tools/dev.sh"
    echo
    print_info "Or use:"
    echo "  ./tools/airagctl dev"
}

interactive_setup() {
    print_header "AI RAG Interactive Setup"
    
    echo
    echo "Welcome to AI RAG setup!"
    echo
    echo "This wizard will help you set up the AI RAG system."
    echo
    
    check_requirements
    
    echo
    echo "Setup options:"
    echo "  1) Full setup (recommended for first time)"
    echo "  2) Quick setup (skip optional steps)"
    echo "  3) Development setup"
    echo "  4) Exit"
    echo
    read -p "Choose option (1-4): " option
    
    case $option in
        1)
            full_setup
            ;;
        2)
            quick_setup
            ;;
        3)
            dev_setup
            ;;
        4)
            print_info "Setup cancelled"
            exit 0
            ;;
        *)
            print_error "Invalid option"
            exit 1
            ;;
    esac
}

# =============================================================================
# Main
# =============================================================================

main() {
    cd "$PROJECT_ROOT"
    
    if [ $# -eq 0 ]; then
        interactive_setup
    else
        case "$1" in
            --quick)
                quick_setup
                ;;
            --dev)
                dev_setup
                ;;
            --full)
                full_setup
                ;;
            --help|-h)
                echo "Usage: $0 [--quick|--dev|--full]"
                echo
                echo "  (no args)    Interactive setup"
                echo "  --quick      Quick setup with defaults"
                echo "  --dev        Development setup"
                echo "  --full       Full setup (asks questions)"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage"
                exit 1
                ;;
        esac
    fi
}

main "$@"
