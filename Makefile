.PHONY: all setup dev build test lint clean docs migrate seed

# Configuration
DOCKER_COMPOSE := docker-compose
BACKEND_CONTAINER := backend
FRONTEND_CONTAINER := web
AI_CONTAINER := ai-service

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
all: setup build test

# Setup development environment
setup: .env
	@echo "$(GREEN)🔧 Setting up DSBA LMS development environment...$(NC)"
	@cp .env.example .env
	@$(MAKE) install-deps
	@echo "$(GREEN)✅ Setup complete! Run 'make dev' to start development.$(NC)"

# Install dependencies
install-deps:
	@echo "$(GREEN)📦 Installing dependencies...$(NC)"
	@cd backend && pip install -r requirements.txt
	@cd web && npm install
	@cd ai-service && pip install -r requirements.txt

# Development environment
dev:
	@echo "$(GREEN)🚀 Starting DSBA LMS development environment...$(NC)"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "AI Service: http://localhost:8001"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "$(YELLOW)Press Ctrl+C to stop all services$(NC)"
	@$(DOCKER_COMPOSE) up --build

# Build services
build:
	@echo "$(GREEN)🔨 Building all services...$(NC)"
	@$(DOCKER_COMPOSE) build --parallel

# Start services
up:
	@echo "$(GREEN)🎯 Starting all services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@$(MAKE) wait-healthy

# Stop services
down:
	@echo "$(GREEN)🛑 Stopping all services...$(NC)"
	@$(DOCKER_COMPOSE) down

# Restart services
restart:
	@echo "$(GREEN)🔄 Restarting all services...$(NC)"
	@$(DOCKER_COMPOSE) restart

# Database operations
migrate:
	@echo "$(GREEN)🗄️  Running database migrations...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) alembic upgrade head

seed:
	@echo "$(GREEN)🌱 Seeding database with demo data...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) python -m scripts.seed_demo

reset-db:
	@echo "$(YELLOW)⚠️  This will reset the entire database!$(NC)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(DOCKER_COMPOSE) down -v; \
		$(DOCKER_COMPOSE) up -d postgres redis; \
		$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) alembic upgrade head; \
		$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) python -m scripts.seed_demo; \
		echo "$(GREEN)✅ Database reset complete!$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

# Testing
test:
	@echo "$(GREEN)🧪 Running all tests...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest tests/ -v
	@echo "$(GREEN)✅ Backend tests passed!$(NC)"

test-backend:
	@echo "$(GREEN)🐍 Running backend tests...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest tests/ -v --cov=app

test-frontend:
	@echo "$(GREEN)⚛️  Running frontend tests...$(NC)"
	@$(DOCKER_COMPOSE) exec $(FRONTEND_CONTAINER) npm test -- --watchAll=false

test-ai:
	@echo "$(GREEN)🤖 Running AI service tests...$(NC)"
	@$(DOCKER_COMPOSE) exec $(AI_CONTAINER) pytest tests/ -v

test-cov:
	@echo "$(GREEN)📊 Generating test coverage report...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest tests/ --cov=app --cov-report=html
	@echo "$(GREEN)📄 Coverage report generated at backend/htmlcov/index.html$(NC)"

# Linting and formatting
lint:
	@echo "$(GREEN)👮 Linting code...$(NC)"
	@echo "$(YELLOW)Backend Python linting...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) flake8 app/ tests/ --max-line-length=88
	@echo "$(YELLOW)Frontend TypeScript/JavaScript linting...$(NC)"
	@$(DOCKER_COMPOSE) exec $(FRONTEND_CONTAINER) npm run lint
	@echo "$(GREEN)✅ Linting completed!$(NC)"

format:
	@echo "$(GREEN)🎨 Formatting code...$(NC)"
	@echo "$(YELLOW)Backend Python formatting...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) black app/ tests/
	@echo "$(YELLOW)Frontend formatting...$(NC)"
	@$(DOCKER_COMPOSE) exec $(FRONTEND_CONTAINER) npm run format
	@echo "$(GREEN)✅ Formatting completed!$(NC)"

# Logs
logs:
	@echo "$(GREEN)📋 Showing all service logs...$(NC)"
	@$(DOCKER_COMPOSE) logs -f

logs-backend:
	@echo "$(GREEN)🐍 Backend service logs...$(NC)"
	@$(DOCKER_COMPOSE) logs -f backend

logs-frontend:
	@echo "$(GREEN)⚛️  Frontend service logs...$(NC)"
	@$(DOCKER_COMPOSE) logs -f web

logs-ai:
	@echo "$(GREEN)🤖 AI service logs...$(NC)"
	@$(DOCKER_COMPOSE) logs -f ai-service

# Health checks
health:
	@echo "$(GREEN)🏥 Service health checks...$(NC)"
	@echo "Backend API: http://localhost:8000/health"
	@echo "Database: $(shell $(DOCKER_COMPOSE) exec postgres pg_isready -h localhost -U lmsadmin -d DSBA_lms > /dev/null 2>&1 && echo '✅ UP' || echo '❌ DOWN')"
	@echo "Redis: $(shell $(DOCKER_COMPOSE) exec redis redis-cli ping > /dev/null 2>&1 && echo '✅ UP' || echo '❌ DOWN')"

wait-healthy:
	@echo "$(GREEN)⏳ Waiting for services to be healthy...$(NC)"
	@sleep 10
	@echo "$(GREEN)✅ Services should now be ready!$(NC)"

# API Documentation
openapi:
	@echo "$(GREEN)📚 Generating OpenAPI documentation...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > docs/openapi.json
	@echo "$(GREEN)📄 OpenAPI spec generated at docs/openapi.json$(NC)"

# Documentation
docs:
	@echo "$(GREEN)📖 Building documentation...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) python -m scripts.generate_docs

# Environment setup
.env:
	@echo "$(GREEN)🔐 Setting up environment files...$(NC)"
	@cp backend/.env.example backend/.env
	@echo "$(GREEN)✅ Environment files configured!$(NC)"

# Cleanup
clean:
	@echo "$(GREEN)🧹 Cleaning up...$(NC)"
	@$(DOCKER_COMPOSE) down -v --remove-orphans
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@find web -name "node_modules" -type d -exec rm -rf {} +
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

# Development helpers
shell-backend:
	@echo "$(GREEN)🐍 Opening backend shell...$(NC)"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) /bin/bash

shell-frontend:
	@echo "$(GREEN)⚛️  Opening frontend shell...$(NC)"
	@$(DOCKER_COMPOSE) exec $(FRONTEND_CONTAINER) /bin/sh

shell-ai:
	@echo "$(GREEN)🤖 Opening AI service shell...$(NC)"
	@$(DOCKER_COMPOSE) exec $(AI_CONTAINER) /bin/bash

# Demo data
demo-users:
	@echo "$(GREEN)👥 Creating demo users...$(NC)"
	@echo "HOD: hod@lms.edu / ChangeMe#1"
	@echo "Teacher: teacher@lms.edu / ChangeMe#1"
	@echo "Student: student@lms.edu / ChangeMe#1"
	@echo "Coordinator: coordinator@lms.edu / ChangeMe#1"

demo-exams:
	@echo "$(GREEN)📝 Creating demo exams...$(NC)"
	@curl -X POST http://localhost:8000/exams/ -H "Content-Type: application/json" -d '{"title": "Demo Exam", "class_id": 1, "start_at": "2024-09-01T10:00:00Z", "end_at": "2024-09-01T11:30:00Z"}'
	@echo "$(GREEN)✅ Demo exam created!$(NC)"

# Help
help:
	@echo "$(GREEN)🔧 DSBA LMS Development Commands:$(NC)"
	@echo ""
	@echo "Setup:"
	@echo "  make setup            Setup development environment"
	@echo "  make dev              Start development environment"
	@echo ""
	@echo "Services:"
	@echo "  make up               Start all services"
	@echo "  make down             Stop all services"
	@echo "  make restart          Restart all services"
	@echo "  make build            Build all services"
	@echo ""
	@echo "Database:"
	@echo "  make migrate          Run database migrations"
	@echo "  make seed             Seed with demo data"
	@echo "  make reset-db         Reset database (CAUTION!)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-backend     Run backend tests"
	@echo "  make test-frontend    Run frontend tests"
	@echo "  make test-ai          Run AI service tests"
	@echo "  make test-cov         Generate coverage report"
	@echo ""
	@echo "Quality:"
	@echo "  make lint             Lint all code"
	@echo "  make format           Format all code"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs             Show all logs"
	@echo "  make logs-backend     Show backend logs"
	@echo "  make logs-frontend    Show frontend logs"
	@echo "  make health           Check service health"
	@echo ""
	@echo "Development:"
	@echo "  make shell-backend    Open backend shell"
	@echo "  make shell-frontend   Open frontend shell"
	@echo "  make demo-users       Show demo credentials"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Clean up everything"
	@echo "  make help             Show this help message"
	@echo ""
	@echo "$(GREEN)🎓 Happy coding with DSBA LMS!$(NC)"
