# MojDom API Python - Makefile

.PHONY: help install test run start stop clean docker-up docker-down

help: ## Show this help message
	@echo "MojDom API Python - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

run: ## Run the application
	python run.py

stop: ## Stop the application (Ctrl+C)

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

docker-up: ## Start with Docker Compose
	docker-compose up -d

docker-down: ## Stop Docker Compose
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-build: ## Build Docker image
	docker-compose build

dev: ## Start in development mode
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

check: ## Check code quality
	python -m flake8 app/ --max-line-length=100
	python -m mypy app/ --ignore-missing-imports

format: ## Format code
	python -m black app/
	python -m isort app/


# Default target
.DEFAULT_GOAL := help

