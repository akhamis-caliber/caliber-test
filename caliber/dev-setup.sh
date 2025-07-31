#!/bin/bash

# Caliber Development Setup Script
# This script provides quick commands for common development tasks

echo "🚀 Caliber Development Environment"
echo "=================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to start services
start_services() {
    echo "🐳 Starting Docker services..."
    docker-compose up -d postgres redis backend
    echo "✅ Services started"
    echo "📊 API available at: http://localhost:8000"
    echo "📚 Docs available at: http://localhost:8000/docs"
}

# Function to stop services
stop_services() {
    echo "🛑 Stopping Docker services..."
    docker-compose down
    echo "✅ Services stopped"
}

# Function to restart backend
restart_backend() {
    echo "🔄 Restarting backend..."
    docker-compose restart backend
    echo "✅ Backend restarted"
}

# Function to view logs
view_logs() {
    echo "📋 Viewing backend logs..."
    docker-compose logs -f backend
}

# Function to check status
check_status() {
    echo "📊 Service Status:"
    docker-compose ps
    echo ""
    echo "🏥 Health Check:"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
}

# Function to start workers
start_workers() {
    echo "👷 Starting background workers..."
    docker-compose up -d worker-scoring worker-maintenance scheduler flower
    echo "✅ Workers started"
    echo "📊 Flower monitor available at: http://localhost:5555"
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    cd ..
    python test_all_modules.py
    python test_storage.py
    python test_models.py
}

# Function to show help
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     - Start core services (postgres, redis, backend)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart backend service"
    echo "  logs      - View backend logs"
    echo "  status    - Check service status and health"
    echo "  workers   - Start background workers"
    echo "  test      - Run test suite"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start development environment"
    echo "  $0 status   # Check if everything is running"
    echo "  $0 logs     # View backend logs"
}

# Main script logic
case "$1" in
    "start")
        check_docker
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_backend
        ;;
    "logs")
        view_logs
        ;;
    "status")
        check_status
        ;;
    "workers")
        start_workers
        ;;
    "test")
        run_tests
        ;;
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac 