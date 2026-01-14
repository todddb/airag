#!/usr/bin/env bash
# =============================================================================
# Backup & Restore Utility
# =============================================================================
# Backup and restore Qdrant vector database

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
BACKUP_DIR="$PROJECT_ROOT/backups"

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
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# =============================================================================
# Backup
# =============================================================================

create_backup() {
    print_header "Creating Backup"
    
    mkdir -p "$BACKUP_DIR"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/qdrant_backup_$timestamp.tar.gz"
    
    cd "$PROJECT_ROOT"
    
    print_info "Stopping Qdrant..."
    docker compose stop qdrant
    
    print_info "Creating backup archive..."
    docker run --rm \
        -v airag_qdrant_data:/data \
        -v "$BACKUP_DIR":/backup \
        alpine tar czf "/backup/qdrant_backup_$timestamp.tar.gz" -C /data .
    
    print_info "Starting Qdrant..."
    docker compose start qdrant
    
    print_success "Backup created: $backup_file"
    
    # Show backup size
    local size=$(du -h "$backup_file" | cut -f1)
    print_info "Size: $size"
}

# =============================================================================
# Restore
# =============================================================================

restore_backup() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        print_error "Backup file required"
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_header "Restoring Backup"
    print_info "File: $backup_file"
    
    echo
    echo "⚠️  WARNING: This will OVERWRITE current database!"
    read -p "Continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    cd "$PROJECT_ROOT"
    
    print_info "Stopping Qdrant..."
    docker compose stop qdrant
    
    print_info "Restoring data..."
    docker run --rm \
        -v airag_qdrant_data:/data \
        -v "$(dirname "$backup_file")":/backup \
        alpine sh -c "rm -rf /data/* && cd /data && tar xzf /backup/$(basename "$backup_file")"
    
    print_info "Starting Qdrant..."
    docker compose start qdrant
    
    print_success "Restore complete"
}

# =============================================================================
# List Backups
# =============================================================================

list_backups() {
    print_header "Available Backups"
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR")" ]; then
        print_info "No backups found"
        return
    fi
    
    echo
    echo "Location: $BACKUP_DIR"
    echo
    
    for backup in "$BACKUP_DIR"/*.tar.gz; do
        if [ -f "$backup" ]; then
            local filename=$(basename "$backup")
            local size=$(du -h "$backup" | cut -f1)
            local date=$(stat -c %y "$backup" 2>/dev/null || stat -f %Sm "$backup" 2>/dev/null)
            
            echo "  $filename"
            echo "    Size: $size"
            echo "    Date: $date"
            echo
        fi
    done
}

# =============================================================================
# Delete Old Backups
# =============================================================================

cleanup_backups() {
    local keep_count=${1:-5}
    
    print_header "Cleaning Up Old Backups"
    print_info "Keeping last $keep_count backups"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_info "No backups directory"
        return
    fi
    
    cd "$BACKUP_DIR"
    
    # Count backups
    local backup_count=$(ls -1 qdrant_backup_*.tar.gz 2>/dev/null | wc -l)
    
    if [ "$backup_count" -le "$keep_count" ]; then
        print_info "Only $backup_count backups found, nothing to delete"
        return
    fi
    
    # Delete old backups
    local to_delete=$((backup_count - keep_count))
    print_info "Deleting $to_delete old backup(s)..."
    
    ls -1t qdrant_backup_*.tar.gz | tail -n "$to_delete" | xargs rm -f
    
    print_success "Cleanup complete"
}

# =============================================================================
# Export Collection
# =============================================================================

export_collection() {
    local collection_name=${1:-documents}
    
    print_header "Exporting Collection: $collection_name"
    
    mkdir -p "$BACKUP_DIR"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local export_file="$BACKUP_DIR/${collection_name}_export_$timestamp.json"
    
    print_info "Exporting collection data..."
    
    # Use Qdrant API to export
    curl -X POST "http://localhost:6333/collections/$collection_name/points/scroll" \
        -H "Content-Type: application/json" \
        -d '{"limit": 10000, "with_payload": true, "with_vector": true}' \
        > "$export_file"
    
    if [ $? -eq 0 ]; then
        print_success "Export created: $export_file"
        local size=$(du -h "$export_file" | cut -f1)
        print_info "Size: $size"
    else
        print_error "Export failed"
        exit 1
    fi
}

# =============================================================================
# Help
# =============================================================================

show_help() {
    cat << EOF
${CYAN}backup.sh${NC} - Backup & Restore Utility

${YELLOW}Usage:${NC}
  ./backup.sh <command> [options]

${YELLOW}Commands:${NC}
  create                    Create new backup
  restore <file>            Restore from backup
  list                      List available backups
  cleanup [keep_count]      Delete old backups (default: keep 5)
  export [collection]       Export collection as JSON

${YELLOW}Examples:${NC}
  ./backup.sh create
  ./backup.sh list
  ./backup.sh restore backups/qdrant_backup_20250113_120000.tar.gz
  ./backup.sh cleanup 10
  ./backup.sh export documents

${YELLOW}Backup Location:${NC}
  $BACKUP_DIR

EOF
}

# =============================================================================
# Main
# =============================================================================

main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    case "$1" in
        create|backup)
            create_backup
            ;;
        restore)
            restore_backup "$2"
            ;;
        list|ls)
            list_backups
            ;;
        cleanup|clean)
            cleanup_backups "$2"
            ;;
        export)
            export_collection "$2"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
