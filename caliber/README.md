# Caliber Application

This directory contains the main Caliber application - a comprehensive campaign performance analytics platform.

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Start all services:**
```bash
docker-compose up -d
```

2. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

3. **Stop services:**
```bash
docker-compose down
```

### Manual Setup

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📁 Directory Structure

```
caliber/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application
│   ├── requirements.txt    # Python dependencies
│   ├── db/                 # Database models
│   ├── auth_service/       # Authentication
│   ├── campaign_service/   # Campaign management
│   ├── scoring_service/    # Scoring engine
│   ├── report_service/     # Reporting
│   └── ai_service/         # AI services
├── frontend/               # React frontend
│   ├── src/                # Source code
│   ├── public/             # Static assets
│   └── package.json        # Dependencies
├── scripts/                # Utility scripts
├── docker-compose.yml      # Docker configuration
├── Dockerfile.backend      # Backend container
├── Dockerfile.frontend     # Frontend container
└── Makefile               # Build commands
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
MONGO_URL=mongodb://localhost:27017/caliber
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=your-secret-key
OPENAI_API_KEY=your-openai-key

# Application
DEBUG=true
LOG_LEVEL=INFO
```

### Docker Configuration

The `docker-compose.yml` file defines three services:
- **backend**: FastAPI application
- **frontend**: React application  
- **mongodb**: Database
- **redis**: Cache

## 🛠️ Development

### Available Commands

```bash
# Start development environment
make dev

# Build containers
make build

# Run tests
make test

# Clean up
make clean

# View logs
make logs
```

### API Endpoints

Key endpoints:
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/campaigns` - Create campaign
- `POST /api/campaigns/{id}/upload` - Upload campaign data
- `POST /api/campaigns/{id}/score` - Start scoring
- `GET /api/reports/{id}/scores` - Get scoring results

## 📊 Features

- **User Authentication**: JWT-based authentication
- **Campaign Management**: Create and manage advertising campaigns
- **File Processing**: Upload and process CSV/Excel files
- **AI Scoring**: Advanced performance scoring with customizable metrics
- **Real-time Results**: Interactive dashboards and analytics
- **Multi-user Support**: Secure user isolation

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 3000, 8000, 27017, and 6379 are available
2. **Database connection**: Check MongoDB is running and accessible
3. **File uploads**: Ensure proper file permissions and format

### Logs

View logs for specific services:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb
```

## 📝 License

This project is licensed under the MIT License.