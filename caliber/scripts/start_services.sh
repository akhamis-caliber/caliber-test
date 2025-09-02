#!/bin/bash

# Caliber Services Startup Script
# This script starts all required services for the Caliber application

set -e

echo "🚀 Starting Caliber Services"
echo "=============================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

# Navigate to project directory
cd "$(dirname "$0")/.."

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from .env.example"
    cp .env.example .env
    echo "⚠️  Please update .env with your actual API keys"
fi

# Create storage directory
mkdir -p storage

echo "🔧 Building and starting services..."

# Use docker compose if available, fallback to docker-compose
if command -v docker compose &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Start services
$DOCKER_COMPOSE up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service status..."

# Check if services are running
if $DOCKER_COMPOSE ps | grep -q "Up"; then
    echo "✅ Services are starting up"
    
    # Wait for backend to be ready
    echo "⏳ Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
            echo "✅ Backend is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ Backend failed to start within 30 seconds"
            $DOCKER_COMPOSE logs backend
            exit 1
        fi
        sleep 1
    done
    
    # Wait for frontend to be ready
    echo "⏳ Waiting for frontend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo "✅ Frontend is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ Frontend failed to start within 30 seconds"
            $DOCKER_COMPOSE logs frontend
            exit 1
        fi
        sleep 1
    done
    
    echo ""
    echo "🎉 Caliber is now running!"
    echo "=========================="
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "📋 Service Status:"
    $DOCKER_COMPOSE ps
    echo ""
    echo "📖 To view logs: $DOCKER_COMPOSE logs -f [service_name]"
    echo "🛑 To stop: $DOCKER_COMPOSE down"
    
else
    echo "❌ Services failed to start"
    echo "📋 Service Status:"
    $DOCKER_COMPOSE ps
    echo ""
    echo "📖 Backend logs:"
    $DOCKER_COMPOSE logs backend
    echo ""
    echo "📖 Frontend logs:"
    $DOCKER_COMPOSE logs frontend
    exit 1
fi