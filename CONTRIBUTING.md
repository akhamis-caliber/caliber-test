# Contributing to CALIBER

Thank you for your interest in contributing to CALIBER! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/akhamis-caliber/caliber-test.git
   cd caliber-test
   ```

2. **Backend Setup**
   ```bash
   cd caliber
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd caliber
   npm install
   ```

4. **Database Setup**
   ```bash
   cd caliber
   docker-compose up -d postgres redis
   ```

5. **Environment Configuration**
   ```bash
   cp caliber/.env.example caliber/.env
   # Edit .env with your configuration
   ```

## Development Workflow

### Branch Naming Convention
- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/urgent-fix` - Critical fixes
- `refactor/component-name` - Code refactoring

### Commit Message Convention
Use conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation

3. **Run tests locally**
   ```bash
   # Backend tests
   cd caliber
   pytest backend/ -v
   
   # Frontend tests
   npm test
   ```

4. **Push and create PR**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Use the PR template
   - Describe changes clearly
   - Link related issues
   - Request reviews from team members

## Code Standards

### Python (Backend)
- Use Black for code formatting
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for functions
- Maximum line length: 88 characters

### JavaScript/React (Frontend)
- Use ESLint and Prettier
- Follow React best practices
- Use functional components with hooks
- Write unit tests for components

### Database
- Use Alembic for migrations
- Follow naming conventions
- Add indexes for performance
- Document schema changes

## Testing

### Backend Testing
```bash
cd caliber
pytest backend/ -v --cov=backend
```

### Frontend Testing
```bash
cd caliber
npm test -- --coverage
```

### Integration Testing
```bash
cd caliber
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Security

- Never commit sensitive data (API keys, passwords)
- Use environment variables for configuration
- Follow OWASP security guidelines
- Run security scans regularly

## Documentation

- Update README.md for major changes
- Document API endpoints
- Keep inline comments up to date
- Update deployment guides

## Getting Help

- Create an issue for bugs or feature requests
- Use discussions for questions
- Join team meetings for complex decisions
- Contact maintainers for urgent issues

## Release Process

1. Create release branch from main
2. Update version numbers
3. Update changelog
4. Create release PR
5. Get approval from maintainers
6. Merge and tag release
7. Deploy to production

Thank you for contributing to CALIBER! 🚀 