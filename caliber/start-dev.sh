#!/bin/bash

# Caliber Development Server Start Script
# This script starts both backend and frontend servers for development
# 
# Note: If you prefer Docker, use: docker-compose up
# The Celery worker has been disabled in docker-compose.yml to fix deployment issues.
# See DOCKER_FIXES.md for more details.

set -e

echo "🚀 Starting Caliber Development Servers"
echo "======================================="
echo "💡 Alternative: Use 'docker-compose up' for containerized deployment"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Run ./setup.sh first${NC}"
    exit 1
fi

# Start backend server
echo -e "${BLUE}🔧 Starting backend server...${NC}"
cd backend

# Check if requirements are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip3 install -r requirements.txt
fi

echo -e "${GREEN}Backend starting on http://localhost:8000${NC}"
python3 main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo -e "${BLUE}🎨 Starting frontend server...${NC}"
cd ../frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    yarn install
fi

echo -e "${GREEN}Frontend starting on http://localhost:3000${NC}"
yarn start &
FRONTEND_PID=$!

# Show status
echo ""
echo -e "${GREEN}✅ Both servers started successfully!${NC}"
echo "========================================"
echo -e "${BLUE}📋 Access Points:${NC}"
echo -e "  Frontend:  ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for both processes
wait