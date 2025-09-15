#!/bin/bash

# Production Deployment Script for AI Backend
# Usage: ./scripts/deploy.sh [environment] [action]
# Examples:
#   ./scripts/deploy.sh staging deploy
#   ./scripts/deploy.sh production deploy
#   ./scripts/deploy.sh production rollback

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-staging}"
ACTION="${2:-deploy}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Check if docker-compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi

    # Check if environment files exist
    if [[ ! -f "$PROJECT_ROOT/.env.$ENVIRONMENT" ]]; then
        log_error "Environment file .env.$ENVIRONMENT not found!"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Backup current deployment (production only)
backup_deployment() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "Creating backup of current deployment..."

        # Create backup directory with timestamp
        BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"

        # Backup database
        docker-compose -f docker-compose.production.yml exec -T postgres pg_dump -U ai_user ai_backend > "$BACKUP_DIR/database_backup.sql" || true

        # Backup docker images
        docker save $(docker-compose -f docker-compose.production.yml config --services | head -1) > "$BACKUP_DIR/app_image_backup.tar" || true

        log_success "Backup created at $BACKUP_DIR"
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks for $ENVIRONMENT..."

    # Check if required environment variables are set
    if [[ "$ENVIRONMENT" == "production" ]]; then
        required_vars=(
            "DB_PASSWORD"
            "OPENAI_API_KEY"
            "JWT_SECRET"
            "API_KEY_HASH_SALT"
            "SENTRY_DSN"
        )
    else
        required_vars=(
            "DB_PASSWORD"
            "OPENAI_API_KEY"
            "JWT_SECRET"
            "API_KEY_HASH_SALT"
        )
    fi

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done

    log_success "Pre-deployment checks passed"
}

# Build and deploy
deploy() {
    log_info "Starting deployment to $ENVIRONMENT..."

    cd "$PROJECT_ROOT"

    # Build images
    log_info "Building Docker images..."
    docker-compose -f "docker-compose.$ENVIRONMENT.yml" build --no-cache

    # Run database migrations (if needed)
    log_info "Running database migrations..."
    docker-compose -f "docker-compose.$ENVIRONMENT.yml" up -d postgres redis
    sleep 10

    # Start all services
    log_info "Starting all services..."
    docker-compose -f "docker-compose.$ENVIRONMENT.yml" up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30

    # Health check
    health_check

    log_success "Deployment to $ENVIRONMENT completed successfully!"
}

# Health check
health_check() {
    log_info "Running health checks..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
            log_success "Health check passed!"
            return 0
        fi

        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
        sleep 10
        ((attempt++))
    done

    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Rollback deployment
rollback() {
    log_warning "Rolling back $ENVIRONMENT deployment..."

    cd "$PROJECT_ROOT"

    # Stop current services
    docker-compose -f "docker-compose.$ENVIRONMENT.yml" down

    # Find latest backup
    LATEST_BACKUP=$(ls -t "$PROJECT_ROOT/backups" | head -1)

    if [[ -z "$LATEST_BACKUP" ]]; then
        log_error "No backup found for rollback"
        exit 1
    fi

    log_info "Rolling back to backup: $LATEST_BACKUP"

    # Restore database backup
    if [[ -f "$PROJECT_ROOT/backups/$LATEST_BACKUP/database_backup.sql" ]]; then
        docker-compose -f "docker-compose.$ENVIRONMENT.yml" up -d postgres
        sleep 10
        cat "$PROJECT_ROOT/backups/$LATEST_BACKUP/database_backup.sql" | docker-compose -f "docker-compose.$ENVIRONMENT.yml" exec -T postgres psql -U ai_user -d ai_backend
    fi

    # Restore docker image
    if [[ -f "$PROJECT_ROOT/backups/$LATEST_BACKUP/app_image_backup.tar" ]]; then
        docker load < "$PROJECT_ROOT/backups/$LATEST_BACKUP/app_image_backup.tar"
    fi

    # Start services
    docker-compose -f "docker-compose.$ENVIRONMENT.yml" up -d

    log_success "Rollback completed!"
}

# Show status
show_status() {
    log_info "Showing $ENVIRONMENT deployment status..."

    cd "$PROJECT_ROOT"
    docker-compose -f "docker-compose.$ENVIRONMENT.yml" ps

    log_info "Service logs (last 20 lines):"
    docker-compose -f "docker-compose.$ENVIRONMENT.yml" logs --tail=20 ai-backend
}

# Cleanup old backups (keep last 5)
cleanup_backups() {
    log_info "Cleaning up old backups..."

    if [[ -d "$PROJECT_ROOT/backups" ]]; then
        # Keep only the 5 most recent backups
        ls -t "$PROJECT_ROOT/backups" | tail -n +6 | xargs -I {} rm -rf "$PROJECT_ROOT/backups/{}" || true
        log_success "Backup cleanup completed"
    fi
}

# Main execution
main() {
    validate_environment
    check_prerequisites

    case "$ACTION" in
        "deploy")
            pre_deployment_checks
            backup_deployment
            deploy
            cleanup_backups
            ;;
        "rollback")
            rollback
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        *)
            log_error "Invalid action: $ACTION. Valid actions: deploy, rollback, status, health"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"