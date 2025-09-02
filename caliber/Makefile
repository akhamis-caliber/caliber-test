# Caliber - AI-Powered Inventory Scoring
# Docker Compose Management

.PHONY: help build up down restart logs clean test frontend backend mongodb redis worker

# Default target
help:
	@echo "Caliber Docker Management Commands:"
	@echo ""
	@echo "🚀 Getting Started:"
	@echo "  make build      - Build all Docker images"
	@echo "  make up         - Start all services (MongoDB, Redis, Backend, Frontend)"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo ""
	@echo "📊 Service Management:"
	@echo "  make frontend   - Start only frontend service"
	@echo "  make backend    - Start only backend service"
	@echo "  make mongodb    - Start only MongoDB service"
	@echo "  make redis      - Start only Redis service"
	@echo "  make worker     - Start only background worker service"
	@echo ""
	@echo "🔍 Monitoring & Debugging:"
	@echo "  make logs       - Show logs from all services"
	@echo "  make status     - Show status of all services"
	@echo "  make ps         - Show running containers"
	@echo ""
	@echo "🧪 Testing & Development:"
	@echo "  make test       - Run backend API tests"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-frontend - Open shell in frontend container"
	@echo "  make shell-mongo    - Open MongoDB shell"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean      - Remove all containers and volumes"
	@echo "  make clean-build - Clean and rebuild everything"
	@echo ""
	@echo "📋 Application URLs:"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  MongoDB:   mongodb://localhost:27017"
	@echo "  Redis:     redis://localhost:6379"

# Build all Docker images
build:
	@echo "🔨 Building Docker images..."
	docker-compose build --no-cache

# Start all services
up:
	@echo "🚀 Starting all Caliber services..."
	docker-compose up -d
	@echo "✅ All services started!"
	@echo ""
	@echo "📋 Service URLs:"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo ""
	@echo "🔍 Check status with: make status"

# Start services in foreground (with logs)
up-logs:
	@echo "🚀 Starting all services with logs..."
	docker-compose up

# Stop all services
down:
	@echo "🛑 Stopping all services..."
	docker-compose down

# Restart all services
restart:
	@echo "🔄 Restarting all services..."
	docker-compose restart

# Individual service commands
frontend:
	@echo "🎨 Starting frontend service..."
	docker-compose up -d frontend

backend:
	@echo "⚡ Starting backend service..."
	docker-compose up -d backend mongodb redis

mongodb:
	@echo "🗄️  Starting MongoDB service..."
	docker-compose up -d mongodb

redis:
	@echo "🔴 Starting Redis service..."
	docker-compose up -d redis

worker:
	@echo "👷 Starting background worker service..."
	docker-compose up -d worker

# Monitoring and debugging
logs:
	@echo "📋 Showing logs from all services..."
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-mongodb:
	docker-compose logs -f mongodb

status:
	@echo "📊 Service Status:"
	docker-compose ps

ps:
	@echo "🐳 Running containers:"
	docker-compose ps

# Development and testing
test:
	@echo "🧪 Running backend API tests..."
	cd backend && python -m pytest tests/ -v

shell-backend:
	@echo "🐚 Opening backend container shell..."
	docker-compose exec backend /bin/bash

shell-frontend:
	@echo "🐚 Opening frontend container shell..."
	docker-compose exec frontend /bin/sh

shell-mongo:
	@echo "🍃 Opening MongoDB shell..."
	docker-compose exec mongodb mongosh -u caliber -p caliber123 --authenticationDatabase admin caliber

# Cleanup commands
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker-compose down -v
	docker-compose rm -f
	docker volume prune -f

clean-build:
	@echo "🧹 Clean build - removing everything and rebuilding..."
	docker-compose down -v
	docker-compose rm -f
	docker system prune -f
	docker volume prune -f
	$(MAKE) build
	$(MAKE) up

# Environment setup
setup:
	@echo "⚙️  Setting up Caliber environment..."
	cp .env.example .env
	@echo "✅ Environment file created. Please update .env with your configuration."
	@echo ""
	@echo "🔧 To start the application:"
	@echo "  make build"
	@echo "  make up"

# Production build
build-prod:
	@echo "🏗️  Building production images..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Quick development start
dev:
	@echo "🚀 Starting development environment..."
	$(MAKE) build
	$(MAKE) up
	@echo ""
	@echo "🎉 Development environment is ready!"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"

# Health check
health:
	@echo "🏥 Checking service health..."
	@curl -f http://localhost:8000/api/healthz || echo "❌ Backend health check failed"
	@curl -f http://localhost:3000 || echo "❌ Frontend health check failed"