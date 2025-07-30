# Caliber - AI-Powered Inventory Scoring Platform

A modern, scalable platform for AI-powered inventory scoring and campaign management.

## 🚀 Features

- **Firebase Authentication**: Secure user authentication with Firebase
- **PostgreSQL Database**: Robust data storage with SQLAlchemy ORM
- **Redis Caching**: High-performance caching and task queues
- **FastAPI Backend**: Modern, fast Python web framework
- **Alembic Migrations**: Database schema management
- **Docker Support**: Containerized development environment
- **Comprehensive Logging**: Structured logging throughout the application

## 📁 Project Structure

```
caliber/
├── backend/
│   ├── auth_service/          # Authentication service
│   │   ├── firebase_verify.py # Firebase token verification
│   │   ├── dependencies.py    # Auth schemas & dependencies
│   │   └── routes.py          # Auth API endpoints
│   ├── common/                # Shared utilities
│   │   ├── schemas.py         # Common API schemas
│   │   ├── logging.py         # Logging configuration
│   │   ├── utils.py           # Utility functions
│   │   └── exceptions.py      # Custom exceptions
│   ├── config/                # Configuration
│   │   ├── settings.py        # Application settings
│   │   ├── database.py        # Database configuration
│   │   └── redis.py           # Redis configuration
│   ├── db/                    # Database models
│   │   ├── base.py            # Base model class
│   │   ├── models.py          # SQLAlchemy models
│   │   └── migrations/        # Alembic migrations
│   └── main.py                # FastAPI application
├── frontend/                  # Frontend application (React/Vue)
├── worker/                    # Background task workers
├── storage/                   # File storage
├── docker-compose.yml         # Docker services
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── run_server.py             # Development server script
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (via Docker)
- Redis (via Docker)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd caliber

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# - Database credentials
# - Firebase credentials
# - OpenAI API key
# - AWS S3 credentials (optional)
```

### 3. Start Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Run database migrations
alembic upgrade head

# Start the development server
python run_server.py
```

### 4. Access the Application

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔐 Authentication

The application uses Firebase Authentication:

1. **Setup Firebase Project**: Create a Firebase project and enable Authentication
2. **Download Service Account**: Download Firebase service account credentials
3. **Configure Environment**: Set `FIREBASE_CREDENTIALS_PATH` in `.env`
4. **Frontend Integration**: Use Firebase SDK for client-side authentication

### API Endpoints

- `POST /api/v1/auth/login` - Login with Firebase token
- `GET /api/v1/auth/profile` - Get user profile
- `PUT /api/v1/auth/profile` - Update user profile

## 🗄️ Database Models

### Core Entities

- **User**: User accounts with Firebase authentication
- **Organization**: Organizations that users belong to
- **CampaignTemplate**: Templates for campaign configuration
- **Campaign**: Campaign instances with scoring results
- **ScoringResult**: Domain scoring results
- **AIInsight**: AI-generated insights for campaigns

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🔧 Development

### Running the Server

```bash
# Development mode with auto-reload
python run_server.py

# Or directly with uvicorn
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Code Quality

```bash
# Format code
black backend/
isort backend/

# Lint code
flake8 backend/
mypy backend/

# Run tests
pytest
```

### Adding New Features

1. **Create Models**: Add SQLAlchemy models in `db/models.py`
2. **Create Migrations**: Generate and apply Alembic migrations
3. **Create Schemas**: Add Pydantic schemas for API requests/responses
4. **Create Routes**: Add FastAPI routes with proper authentication
5. **Add Tests**: Write comprehensive tests for new features

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Required environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis
REDIS_URL=redis://host:port/0

# Firebase
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Security
SECRET_KEY=your-secret-key
ENVIRONMENT=production
```

## 📚 API Documentation

The API documentation is automatically generated and available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {...},
  "message": "Success message",
  "errors": null
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the API documentation
- Review the logs for debugging information

---

**Caliber** - Empowering data-driven advertising decisions with AI 🎯
