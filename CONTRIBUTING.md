# Contributing to Caliber

Thank you for your interest in contributing to Caliber! This document provides guidelines and information for contributors.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- Git
- Docker (optional)

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/caliber.git`
3. Create a virtual environment: `python -m venv venv`
4. Install dependencies:
   ```bash
   # Backend
   cd backend && pip install -r requirements.txt
   
   # Frontend
   cd frontend && npm install
   ```

## 🌿 Branch Strategy

We follow a **Git Flow** approach with the following branches:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical production fixes
- `release/*` - Release preparation

### Branch Naming Convention

```
<type>/<ticket-number>-<description>
```

**Types:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical fixes
- `release/` - Release preparation
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

**Examples:**
- `feature/123-campaign-management`
- `bugfix/456-file-upload-error`
- `docs/789-api-documentation`
- `refactor/101-auth-service`

## 📝 Pull Request Process

### Before Submitting a PR

1. **Ensure your code follows our standards:**
   - Run linting: `npm run lint` (frontend) / `flake8` (backend)
   - Run tests: `npm test` (frontend) / `pytest` (backend)
   - Check code coverage: `npm run test:coverage`

2. **Update documentation:**
   - Update README.md if needed
   - Add/update API documentation
   - Update inline code comments

3. **Test your changes:**
   - Test locally with different environments
   - Ensure all existing tests pass
   - Add new tests for new functionality

### PR Guidelines

1. **Title Format:**
   ```
   <type>(<scope>): <description>
   
   Examples:
   feat(campaign): add campaign creation endpoint
   fix(auth): resolve login validation issue
   docs(api): update authentication documentation
   ```

2. **Description Template:**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests added/updated
   - [ ] No breaking changes (or documented)

   ## Related Issues
   Closes #123
   ```

3. **Keep PRs focused:**
   - One feature/fix per PR
   - Keep changes small and manageable
   - Break large features into smaller PRs

## 🔍 Code Review Process

### Review Checklist

**Code Quality:**
- [ ] Code is readable and well-structured
- [ ] Follows project coding standards
- [ ] No code duplication
- [ ] Proper error handling
- [ ] Security considerations addressed

**Testing:**
- [ ] Adequate test coverage
- [ ] Tests are meaningful and pass
- [ ] Edge cases considered
- [ ] Performance impact assessed

**Documentation:**
- [ ] Code is self-documenting
- [ ] Comments added where necessary
- [ ] API documentation updated
- [ ] README updated if needed

### Review Guidelines

1. **Be constructive and respectful**
2. **Focus on the code, not the person**
3. **Provide specific, actionable feedback**
4. **Use inline comments for specific issues**
5. **Suggest improvements when possible**

### Review Process

1. **Initial Review:** Automated checks (CI/CD)
2. **Code Review:** At least one team member approval
3. **Testing:** Ensure all tests pass
4. **Final Review:** Senior developer approval for complex changes
5. **Merge:** Squash and merge to maintain clean history

## 🧪 Testing Guidelines

### Frontend Testing
- Unit tests for components and utilities
- Integration tests for API calls
- E2E tests for critical user flows
- Minimum 80% code coverage

### Backend Testing
- Unit tests for all functions and classes
- Integration tests for API endpoints
- Database migration tests
- Minimum 85% code coverage

### Test Naming Convention
```
<function/component>_<scenario>_<expected_result>
```

**Examples:**
- `test_campaign_creation_with_valid_data_returns_success`
- `test_file_upload_with_invalid_format_returns_error`
- `test_user_authentication_with_valid_credentials_succeeds`

## 📚 Documentation Standards

### Code Documentation
- Use clear, descriptive function and variable names
- Add docstrings for all public functions
- Include type hints (Python) and PropTypes (React)
- Comment complex algorithms and business logic

### API Documentation
- Use OpenAPI/Swagger for backend APIs
- Include request/response examples
- Document error codes and messages
- Keep documentation up-to-date with code changes

## 🚀 Deployment Process

### Development Workflow
1. Feature branch → `develop` (via PR)
2. `develop` → staging environment
3. `develop` → `main` (via release PR)
4. `main` → production environment

### Release Process
1. Create release branch from `develop`
2. Update version numbers and changelog
3. Final testing and bug fixes
4. Merge to `main` and tag release
5. Deploy to production

## 🐛 Bug Reports

### Bug Report Template
```markdown
## Bug Description
Clear description of the issue

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Windows 10, macOS 12]
- Browser: [e.g., Chrome 120, Firefox 119]
- Node.js: [e.g., 18.17.0]
- Python: [e.g., 3.11.0]

## Additional Information
Screenshots, logs, or other relevant information
```

## 💡 Feature Requests

### Feature Request Template
```markdown
## Feature Description
Clear description of the requested feature

## Use Case
Why this feature is needed

## Proposed Solution
How you think it should be implemented

## Alternatives Considered
Other approaches you've considered

## Additional Information
Any other relevant details
```

## 📞 Getting Help

- **Issues:** Create an issue for bugs or feature requests
- **Discussions:** Use GitHub Discussions for questions
- **Documentation:** Check the `docs/` folder
- **Team:** Reach out to the development team

## 🎉 Recognition

Contributors will be recognized in:
- Project README
- Release notes
- Contributor hall of fame

Thank you for contributing to Caliber! 🚀 