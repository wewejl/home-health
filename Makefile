.PHONY: help install lint lint-fix test build docker-up docker-down docker-logs pre-commit-install test-backend test-frontend

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

lint:  ## Run all linters
	@echo "Running backend linters..."
	cd backend && black --check . && isort --check-only . && flake8 .
	@echo "Running frontend linters..."
	cd frontend && npm run lint

lint-fix:  ## Fix linting issues
	@echo "Fixing backend code..."
	cd backend && black . && isort .
	@echo "Fixing frontend code..."
	cd frontend && npm run lint:fix && npm run format

test:  ## Run all tests
	@echo "Running backend tests..."
	cd backend && pytest --cov=app --cov-report=term-missing || true
	@echo "Running frontend tests..."
	cd frontend && npm run test || true

test-backend:  ## Run backend tests only
	cd backend && pytest -v

test-frontend:  ## Run frontend tests only
	cd frontend && npm run test

build:  ## Build all projects
	@echo "Building frontend..."
	cd frontend && npm run build

docker-up:  ## Start Docker Compose services
	docker-compose up -d

docker-down:  ## Stop Docker Compose services
	docker-compose down

docker-logs:  ## Show Docker Compose logs
	docker-compose logs -f

pre-commit-install:  ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	pip install pre-commit
	pre-commit install
