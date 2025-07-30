# CALIBER - AI-Powered Campaign Management Platform

[![CI/CD](https://github.com/akhamis-caliber/caliber-test/workflows/Backend%20CI%2FCD/badge.svg)](https://github.com/akhamis-caliber/caliber-test/actions)
[![Docker](https://github.com/akhamis-caliber/caliber-test/workflows/Docker%20Build%20and%20Push/badge.svg)](https://github.com/akhamis-caliber/caliber-test/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CALIBER is a comprehensive AI-powered platform for campaign management, scoring, and analytics. Built with modern technologies including FastAPI, React, and AI services.

## 🚀 Features

- **AI-Powered Insights**: Advanced analytics and scoring algorithms
- **Campaign Management**: Complete campaign lifecycle management
- **Real-time Scoring**: Dynamic scoring with AI explanations
- **Report Generation**: Automated PDF and export capabilities
- **Authentication**: Firebase-based secure authentication
- **API-First Design**: RESTful APIs with comprehensive documentation
- **Modern UI**: React-based responsive frontend
- **Scalable Architecture**: Microservices with Docker support

## 🏗️ Architecture

```
CALIBER/
├── backend/                 # FastAPI Backend Services
│   ├── ai_service/         # AI and ML Services
│   ├── auth_service/       # Authentication & Authorization
│   ├── campaign_service/   # Campaign Management
│   ├── report_service/     # Report Generation
│   ├── scoring_service/    # Scoring Algorithms
│   └── common/            # Shared Utilities
├── frontend/              # React Frontend
├── worker/               # Celery Background Tasks
└── storage/             # File Storage
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **Celery** - Background task processing
- **Alembic** - Database migrations
- **Pydantic** - Data validation

### Frontend
- **React** - UI framework
- **Node.js** - Runtime environment
- **Firebase** - Authentication
- **Axios** - HTTP client

### DevOps
- **Docker** - Containerization
- **GitHub Actions** - CI/CD
- **PostgreSQL** - Database
- **Redis** - Cache

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/akhamis-caliber/caliber-test.git
cd caliber-test
```

### 2. Backend Setup
```bash
cd caliber
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd caliber
npm install
```

### 4. Environment Configuration
```bash
cp caliber/.env.example caliber/.env
# Edit .env with your configuration
```

### 5. Database Setup
```bash
cd caliber
docker-compose up -d postgres redis
```

### 6. Run the Application
```bash
# Backend
cd caliber
uvicorn backend.main:app --reload

# Frontend (in another terminal)
cd caliber
npm start
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
cd caliber
docker-compose up -d
```

### Individual Services
```bash
# Backend only
docker build -t caliber-backend .
docker run -p 8000:8000 caliber-backend

# Frontend only
cd frontend
docker build -t caliber-frontend .
docker run -p 3000:3000 caliber-frontend
```

## 🧪 Testing

### Backend Tests
```bash
cd caliber
pytest backend/ -v --cov=backend
```

### Frontend Tests
```bash
cd caliber
npm test -- --coverage
```

### Integration Tests
```bash
cd caliber
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `caliber` directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/caliber
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email
FIREBASE_CLIENT_ID=your-client-id

# AI Services
OPENAI_API_KEY=your-openai-key
AI_MODEL=gpt-4

# Storage
STORAGE_PATH=./storage
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/akhamis-caliber/caliber-test/issues)
- **Discussions**: [GitHub Discussions](https://github.com/akhamis-caliber/caliber-test/discussions)
- **Documentation**: [Wiki](https://github.com/akhamis-caliber/caliber-test/wiki)

## 🏆 Acknowledgments

- FastAPI community for the excellent framework
- React team for the amazing frontend library
- All contributors who help improve CALIBER

## 📈 Roadmap

- [ ] Advanced AI model integration
- [ ] Real-time collaboration features
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Multi-tenant architecture
- [ ] API rate limiting
- [ ] Advanced security features

---

**Made with ❤️ by the CALIBER Team** 