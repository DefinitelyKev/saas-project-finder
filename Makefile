.PHONY: help install dev build test lint format clean docker-build docker-up docker-down

help: ## Show this help message
	@echo "AI Backend - Make Commands"
	@echo "=========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run development server
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

build: ## Build the application
	docker build -f docker/Dockerfile -t ai-backend .

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=src --cov-report=html --cov-report=term

lint: ## Run linting
	black src/ --check
	isort src/ --check-only
	mypy src/
	pyright src/

typecheck: ## Run type checking only
	pyright src/

format: ## Format code
	black src/
	isort src/

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov/
	rm -rf .coverage

# Docker commands
docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start all services
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## View logs
	docker-compose logs -f ai-backend

docker-shell: ## Open shell in container
	docker-compose exec ai-backend bash

# Database commands
db-upgrade: ## Run database migrations
	alembic upgrade head

db-downgrade: ## Rollback database migrations
	alembic downgrade -1

db-reset: ## Reset database (dangerous!)
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 5
	alembic upgrade head

# Development helpers
create-tenant: ## Create a test tenant
	python scripts/create_tenant.py

seed-agents: ## Seed agents in database
	python scripts/seed_agents.py

# Production commands
prod-build: ## Build for production
	docker build -f docker/Dockerfile -t ai-backend:prod .

prod-up: ## Start production services
	docker-compose -f docker-compose.prod.yml up -d