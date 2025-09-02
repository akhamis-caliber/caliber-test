# Caliber - Campaign Performance Analytics Platform

A comprehensive web application for analyzing and scoring digital advertising campaign performance using advanced analytics and AI-powered insights.

## 🚀 Features

- **Campaign Management**: Create, configure, and manage advertising campaigns
- **File Upload & Processing**: Support for CSV/Excel campaign data files
- **Advanced Scoring Engine**: AI-powered performance scoring with customizable metrics
- **Real-time Analytics**: Interactive dashboards and performance insights
- **Multi-user Support**: Secure authentication and user management
- **Docker Deployment**: Containerized application for easy deployment

## 🏗️ Architecture

- **Frontend**: React.js with modern UI components
- **Backend**: FastAPI (Python) with async/await support
- **Database**: MongoDB with Beanie ODM
- **Cache**: Redis for performance optimization
- **Containerization**: Docker & Docker Compose

## 📁 Project Structure

```
caliber/
├── backend/                 # FastAPI backend application
│   ├── main.py             # Main application entry point
│   ├── requirements.txt    # Python dependencies
│   ├── db/                 # Database models and configuration
│   ├── auth_service/       # Authentication services
│   ├── campaign_service/   # Campaign management services
│   ├── scoring_service/    # AI scoring engine
│   ├── report_service/     # Reporting and analytics
│   └── ai_service/         # AI/ML services
├── frontend/               # React.js frontend application
│   ├── src/                # Source code
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── scripts/                # Utility scripts
├── docker-compose.yml      # Docker orchestration
├── Dockerfile.backend      # Backend container
├── Dockerfile.frontend     # Frontend container
└── README.md               # Project documentation
```

## 🛠️ Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for local development)
- Python 3.8+ (for local development)

### Running with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd caliber
```

2. Start the application:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

1. Install dependencies:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

2. Start services:
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm start
```

## 🔧 Configuration

Environment variables can be configured in `docker-compose.yml` or `.env` file:

- `MONGO_URL`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `JWT_SECRET`: JWT token secret

## 📊 API Documentation

The API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions, please open an issue in the GitHub repository.
