# Team Onboarding Guide

Welcome to the Caliber development team! This guide will help you get started with the project and understand our development workflow.

## 🚀 Quick Start for New Developers

### 1. Prerequisites

Before you begin, ensure you have the following installed:

- **Git**: Latest version
- **Node.js**: 18+ 
- **Python**: 3.9+
- **Docker**: (optional, for containerized development)
- **VS Code**: (recommended IDE)

### 2. Repository Setup

```bash
# Clone the repository
git clone https://github.com/your-org/caliber.git
cd caliber

# Set up Git Flow (if not already configured)
git config --global init.defaultBranch main
```

### 3. Development Environment Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend Setup
```bash
cd frontend
npm install
```

#### Environment Configuration
```bash
# Copy environment templates
cp backend/env.template backend/.env
cp frontend/env.template frontend/.env.local

# Edit the files with your configuration
```

### 4. Start Development Servers

```bash
# Backend (from backend directory)
uvicorn main:app --reload

# Frontend (from frontend directory)
npm run dev
```

## 🌿 Git Workflow

### Branch Strategy

We follow **Git Flow** with these branches:

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical fixes

### Creating a Feature Branch

```bash
# Start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/123-your-feature-name

# Make your changes and commit
git add .
git commit -m "feat(feature): add new functionality"

# Push to remote
git push -u origin feature/123-your-feature-name
```

### Pull Request Process

1. **Create PR** from your feature branch to `develop`
2. **Fill out PR template** completely
3. **Request reviews** from team members
4. **Address feedback** and update PR
5. **Merge** when approved

## 📋 Development Guidelines

### Code Standards

#### Backend (Python)
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all functions
- Maximum line length: 88 characters (Black formatter)

#### Frontend (JavaScript/React)
- Use ESLint and Prettier
- Follow React best practices
- Use functional components with hooks
- Write PropTypes for components

### Testing Requirements

- **Backend**: Minimum 85% code coverage
- **Frontend**: Minimum 80% code coverage
- Write unit tests for all new functionality
- Include integration tests for API endpoints

### Documentation

- Update README.md for significant changes
- Add inline comments for complex logic
- Update API documentation
- Create/update component documentation

## 🛠️ Development Tools

### Recommended VS Code Extensions

- **Python**: Python, Pylance
- **JavaScript**: ESLint, Prettier
- **Git**: GitLens, Git History
- **General**: Auto Rename Tag, Bracket Pair Colorizer

### Useful Commands

```bash
# Backend
cd backend
pytest                    # Run tests
flake8 .                 # Lint code
black .                  # Format code

# Frontend
cd frontend
npm test                 # Run tests
npm run lint             # Lint code
npm run build            # Build for production
```

## 📚 Project Structure

```
caliber/
├── frontend/              # Next.js React application
│   ├── components/        # React components
│   ├── pages/            # Next.js pages
│   ├── services/         # API services
│   └── utils/            # Utility functions
├── backend/              # FastAPI Python backend
│   ├── auth_service/     # Authentication
│   ├── campaign_service/ # Campaign management
│   ├── scoring_service/  # AI scoring
│   └── report_service/   # Reporting
├── worker/               # Background tasks
├── storage/              # File storage
└── docs/                 # Documentation
```

## 🔍 Key Components

### Backend Services

- **Auth Service**: Firebase authentication, JWT management
- **Campaign Service**: Campaign CRUD operations
- **Scoring Service**: AI-powered lead scoring
- **Report Service**: Report generation and exports
- **AI Service**: OpenAI integration for insights

### Frontend Components

- **Dashboard**: Main application dashboard
- **Campaign Management**: Create and manage campaigns
- **File Upload**: Secure file handling
- **Report Viewer**: View and export reports
- **AI Insights**: AI-generated recommendations

## 🚀 Deployment Process

### Development Workflow

1. **Feature Development**: Work on feature branch
2. **Code Review**: Submit PR to `develop`
3. **Testing**: Automated and manual testing
4. **Staging**: Deploy to staging environment
5. **Production**: Merge to `main` and deploy

### Environment Types

- **Development**: Local development
- **Staging**: Pre-production testing
- **Production**: Live application

## 📞 Communication

### Team Communication

- **Slack**: #caliber-dev channel
- **Email**: caliber-team@company.com
- **Meetings**: Daily standup at 9:00 AM
- **Code Reviews**: GitHub PR reviews

### Getting Help

1. **Check Documentation**: Start with README.md
2. **Search Issues**: Look for similar problems
3. **Ask Team**: Post in Slack or create issue
4. **Pair Programming**: Schedule with team members

## 🎯 First Tasks

### Week 1: Setup & Familiarization

- [ ] Complete environment setup
- [ ] Read through documentation
- [ ] Run the application locally
- [ ] Review codebase structure
- [ ] Set up development tools

### Week 2: First Contribution

- [ ] Pick up a "good first issue"
- [ ] Create feature branch
- [ ] Implement solution
- [ ] Write tests
- [ ] Submit PR

### Week 3: Integration

- [ ] Participate in code reviews
- [ ] Attend team meetings
- [ ] Contribute to documentation
- [ ] Learn deployment process

## 📊 Performance Expectations

### Code Quality

- Write clean, maintainable code
- Follow established patterns
- Consider performance implications
- Write comprehensive tests

### Communication

- Respond to PR reviews within 24 hours
- Update team on progress regularly
- Ask questions when stuck
- Share knowledge with team

### Productivity

- Complete assigned tasks on time
- Communicate blockers early
- Help other team members
- Continuously improve skills

## 🎉 Welcome to the Team!

We're excited to have you on board! Remember:

- **Ask questions** - No question is too small
- **Be patient** - Learning takes time
- **Contribute ideas** - Fresh perspectives are valuable
- **Have fun** - Enjoy the development process

### Next Steps

1. Complete the setup checklist above
2. Introduce yourself to the team
3. Pick up your first task
4. Start contributing!

Welcome to Caliber! 🚀 