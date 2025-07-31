#!/bin/bash

# Caliber Worker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Redis is running
check_redis() {
    print_status "Checking Redis connection..."
    if redis-cli ping > /dev/null 2>&1; then
        print_status "Redis is running"
    else
        print_error "Redis is not running. Please start Redis first."
        exit 1
    fi
}

# Start scoring workers
start_scoring_workers() {
    print_status "Starting scoring workers..."
    celery -A worker.celery worker \
        --loglevel=info \
        --queues=scoring \
        --concurrency=2 \
        --hostname=scoring@%h \
        --pidfile=/tmp/celery_scoring.pid \
        --logfile=logs/celery_scoring.log \
        --detach
}

# Start maintenance workers
start_maintenance_workers() {
    print_status "Starting maintenance workers..."
    celery -A worker.celery worker \
        --loglevel=info \
        --queues=maintenance,exports,monitoring \
        --concurrency=1 \
        --hostname=maintenance@%h \
        --pidfile=/tmp/celery_maintenance.pid \
        --logfile=logs/celery_maintenance.log \
        --detach
}

# Start beat scheduler
start_scheduler() {
    print_status "Starting beat scheduler..."
    celery -A worker.celery beat \
        --loglevel=info \
        --pidfile=/tmp/celery_beat.pid \
        --logfile=logs/celery_beat.log \
        --detach
}

# Start flower monitoring
start_flower() {
    print_status "Starting Flower monitoring..."
    celery -A worker.celery flower \
        --port=5555 \
        --pidfile=/tmp/celery_flower.pid \
        --logfile=logs/celery_flower.log \
        --detach
}

# Stop all workers
stop_workers() {
    print_status "Stopping all Celery processes..."
    
    # Stop workers
    if [ -f /tmp/celery_scoring.pid ]; then
        kill -TERM $(cat /tmp/celery_scoring.pid) 2>/dev/null || true
        rm -f /tmp/celery_scoring.pid
        print_status "Scoring workers stopped"
    fi
    
    if [ -f /tmp/celery_maintenance.pid ]; then
        kill -TERM $(cat /tmp/celery_maintenance.pid) 2>/dev/null || true
        rm -f /tmp/celery_maintenance.pid
        print_status "Maintenance workers stopped"
    fi
    
    if [ -f /tmp/celery_beat.pid ]; then
        kill -TERM $(cat /tmp/celery_beat.pid) 2>/dev/null || true
        rm -f /tmp/celery_beat.pid
        print_status "Beat scheduler stopped"
    fi
    
    if [ -f /tmp/celery_flower.pid ]; then
        kill -TERM $(cat /tmp/celery_flower.pid) 2>/dev/null || true
        rm -f /tmp/celery_flower.pid
        print_status "Flower monitoring stopped"
    fi
    
    # Force kill any remaining celery processes
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    pkill -f "celery.*flower" 2>/dev/null || true
    
    print_status "All Celery processes stopped"
}

# Check worker status
check_status() {
    print_status "Checking Celery worker status..."
    
    if [ -f /tmp/celery_scoring.pid ]; then
        if kill -0 $(cat /tmp/celery_scoring.pid) 2>/dev/null; then
            print_status "Scoring workers: RUNNING (PID: $(cat /tmp/celery_scoring.pid))"
        else
            print_warning "Scoring workers: NOT RUNNING (stale PID file)"
        fi
    else
        print_warning "Scoring workers: NOT RUNNING"
    fi
    
    if [ -f /tmp/celery_maintenance.pid ]; then
        if kill -0 $(cat /tmp/celery_maintenance.pid) 2>/dev/null; then
            print_status "Maintenance workers: RUNNING (PID: $(cat /tmp/celery_maintenance.pid))"
        else
            print_warning "Maintenance workers: NOT RUNNING (stale PID file)"
        fi
    else
        print_warning "Maintenance workers: NOT RUNNING"
    fi
    
    if [ -f /tmp/celery_beat.pid ]; then
        if kill -0 $(cat /tmp/celery_beat.pid) 2>/dev/null; then
            print_status "Beat scheduler: RUNNING (PID: $(cat /tmp/celery_beat.pid))"
        else
            print_warning "Beat scheduler: NOT RUNNING (stale PID file)"
        fi
    else
        print_warning "Beat scheduler: NOT RUNNING"
    fi
    
    if [ -f /tmp/celery_flower.pid ]; then
        if kill -0 $(cat /tmp/celery_flower.pid) 2>/dev/null; then
            print_status "Flower monitoring: RUNNING (PID: $(cat /tmp/celery_flower.pid))"
        else
            print_warning "Flower monitoring: NOT RUNNING (stale PID file)"
        fi
    else
        print_warning "Flower monitoring: NOT RUNNING"
    fi
}

# Show logs
show_logs() {
    local log_type=$1
    
    case $log_type in
        "scoring")
            if [ -f logs/celery_scoring.log ]; then
                tail -f logs/celery_scoring.log
            else
                print_error "Scoring worker log file not found"
            fi
            ;;
        "maintenance")
            if [ -f logs/celery_maintenance.log ]; then
                tail -f logs/celery_maintenance.log
            else
                print_error "Maintenance worker log file not found"
            fi
            ;;
        "beat")
            if [ -f logs/celery_beat.log ]; then
                tail -f logs/celery_beat.log
            else
                print_error "Beat scheduler log file not found"
            fi
            ;;
        "flower")
            if [ -f logs/celery_flower.log ]; then
                tail -f logs/celery_flower.log
            else
                print_error "Flower monitoring log file not found"
            fi
            ;;
        *)
            print_error "Invalid log type. Use: scoring, maintenance, beat, or flower"
            exit 1
            ;;
    esac
}

# Create logs directory
create_logs_dir() {
    if [ ! -d logs ]; then
        mkdir -p logs
        print_status "Created logs directory"
    fi
}

# Main script logic
case "${1:-}" in
    "start")
        create_logs_dir
        check_redis
        start_scoring_workers
        start_maintenance_workers
        start_scheduler
        start_flower
        print_status "All workers started successfully"
        print_status "Flower monitoring available at: http://localhost:5555"
        ;;
    "stop")
        stop_workers
        ;;
    "restart")
        stop_workers
        sleep 2
        create_logs_dir
        check_redis
        start_scoring_workers
        start_maintenance_workers
        start_scheduler
        start_flower
        print_status "All workers restarted successfully"
        ;;
    "status")
        check_status
        ;;
    "logs")
        show_logs $2
        ;;
    "clean")
        print_status "Cleaning up PID files..."
        rm -f /tmp/celery_*.pid
        print_status "PID files cleaned"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all Celery workers and services"
        echo "  stop    - Stop all Celery workers and services"
        echo "  restart - Restart all Celery workers and services"
        echo "  status  - Check status of all workers"
        echo "  logs    - Show logs for specific worker (scoring|maintenance|beat|flower)"
        echo "  clean   - Clean up stale PID files"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 logs scoring"
        echo "  $0 status"
        exit 1
        ;;
esac 