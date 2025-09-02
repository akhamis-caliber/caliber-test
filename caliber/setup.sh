#!/bin/bash

# Caliber Application Setup Script
# This script sets up the Caliber application for development

set -e  # Exit on error

echo "🚀 Setting up Caliber - AI-Powered Inventory Scoring"
echo "=============================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
echo "📋 Checking system requirements..."

# Check Node.js
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'.' -f1 | sed 's/v//')
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node --version)"
    exit 1
fi
echo "✅ Node.js $(node --version) found"

# Check Python
if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}' | cut -d'.' -f1-2)
echo "✅ Python $(python3 --version) found"

# Check pip
if ! command_exists pip3; then
    echo "❌ pip3 is not installed. Please install pip"
    exit 1
fi
echo "✅ pip3 found"

# Check yarn (install if not present)
if ! command_exists yarn; then
    echo "🔧 Installing Yarn package manager..."
    npm install -g yarn
fi
echo "✅ Yarn $(yarn --version) found"

# Setup environment files
echo ""
echo "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "📝 Please update .env with your configuration (especially OPENAI_API_KEY)"
else
    echo "✅ .env file already exists"
fi

# Install backend dependencies
echo ""
echo "🔧 Installing backend dependencies..."
cd backend
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in backend directory"
    exit 1
fi

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
echo "✅ Backend dependencies installed"
cd ..

# Install frontend dependencies
echo ""
echo "🎨 Installing frontend dependencies..."
cd frontend
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found in frontend directory"
    exit 1
fi

yarn install
echo "✅ Frontend dependencies installed"
cd ..

# Check MongoDB (optional)
echo ""
echo "🗄️  Checking database options..."
if command_exists mongod; then
    echo "✅ MongoDB found locally"
    MONGO_STATUS="local"
elif command_exists docker; then
    echo "✅ Docker found - can use MongoDB container"
    MONGO_STATUS="docker"
else
    echo "⚠️  MongoDB not found locally, Docker not available"
    echo "   You can use MongoDB Atlas (cloud) or install MongoDB locally"
    MONGO_STATUS="cloud"
fi

# Setup complete
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Next Steps:"
echo ""

if [ "$MONGO_STATUS" = "local" ]; then
    echo "1. Start MongoDB:"
    echo "   sudo systemctl start mongod"
    echo ""
elif [ "$MONGO_STATUS" = "docker" ]; then
    echo "1. Start MongoDB with Docker:"
    echo "   docker run -d -p 27017:27017 --name caliber-mongo mongo:7"
    echo ""
else
    echo "1. Setup MongoDB:"
    echo "   - Install MongoDB locally: https://docs.mongodb.com/manual/installation/"
    echo "   - OR use MongoDB Atlas: https://www.mongodb.com/atlas"
    echo "   - Update MONGO_URL in .env file"
    echo ""
fi

echo "2. Start the backend server:"
echo "   cd backend && python main.py"
echo ""
echo "3. In a new terminal, start the frontend:"
echo "   cd frontend && yarn start"
echo ""
echo "4. Access the application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📝 Don't forget to update your .env file with:"
echo "   - OPENAI_API_KEY (for AI features)"
echo "   - MONGO_URL (if using remote MongoDB)"
echo ""
echo "For Docker setup, see DOCKER.md"