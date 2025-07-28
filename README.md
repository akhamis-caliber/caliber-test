# Caliber - Full-Stack Web Application

A modern full-stack web application built with Next.js frontend and FastAPI backend, featuring campaign management, AI-powered scoring, and comprehensive analytics.

## 🚀 Features

- **Campaign Management**: Create, manage, and track marketing campaigns
- **AI-Powered Scoring**: Intelligent lead scoring using machine learning
- **Real-time Analytics**: Live dashboard with comprehensive reporting
- **File Upload & Validation**: Secure file handling with validation
- **Authentication**: Firebase-based user authentication
- **Redis Integration**: Caching and session management
- **WebSocket Support**: Real-time communication

## 🏗️ Architecture

```
caliber/
├── frontend/          # Next.js React application
├── backend/           # FastAPI Python backend
├── worker/            # Background task processing
├── storage/           # File storage and uploads
├── docs/              # Project documentation
└── docker-compose.yml # Development environment
```

## 🛠️ Tech Stack

### Frontend

- **Next.js** - React framework
- **Tailwind CSS** - Styling
- **Jest** - Testing
- **WebSocket** - Real-time updates

### Backend

- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Redis** - Caching and sessions
- **Firebase** - Authentication
- **OpenAI** - AI services

## 📋 Prerequisites

- Node.js 18+
- Python 3.9+
- Redis
- Docker (optional)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd caliber
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Environment Configuration

Copy environment templates and configure:

```bash
# Backend
cp backend/env.template backend/.env

# Frontend
cp frontend/env.template frontend/.env.local
```

### 5. Start Development Servers

```bash
# Backend (from backend directory)
uvicorn main:app --reload

# Frontend (from frontend directory)
npm run dev
```

## 🐳 Docker Setup

```bash
docker-compose up -d
```

## 📚 Documentation

- [Backend API Documentation](docs/backend/)
- [Frontend Development Guide](docs/frontend/)
- [Deployment Guide](docs/deployment/)

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation in the `docs/` folder
- Review the troubleshooting guide

## 🔄 Development Workflow

1. Create a feature branch from `develop`
2. Make your changes
3. Write/update tests
4. Submit a pull request
5. Code review and approval
6. Merge to `develop`
7. Deploy to staging
8. Merge to `main` for production

## 📊 Project Status

- ✅ Core backend API
- ✅ Frontend dashboard
- ✅ Authentication system
- ✅ File upload system
- ✅ AI scoring integration
- ✅ Real-time updates
- 🔄 Documentation updates
- 🔄 Test coverage improvements
