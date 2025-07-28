# GitHub Repository Setup Guide

This guide provides instructions for setting up the Caliber repository on GitHub with proper branch protection and team collaboration features.

## 🚀 Repository Setup

### 1. Create GitHub Repository

1. Go to GitHub and create a new repository
2. Name: `caliber`
3. Description: "Full-stack web application with AI-powered scoring and campaign management"
4. Visibility: Private (recommended for team projects)
5. **Do NOT** initialize with README, .gitignore, or license (we already have these)

### 2. Connect Local Repository

```bash
# Add remote origin
git remote add origin https://github.com/your-username/caliber.git

# Push main branch
git push -u origin main

# Push develop branch
git push -u origin develop
```

## 🛡️ Branch Protection Rules

### Main Branch Protection

**Settings → Branches → Add rule for `main`:**

- ✅ **Require a pull request before merging**

  - Require approvals: **2** (minimum)
  - Dismiss stale PR approvals when new commits are pushed
  - Require review from code owners

- ✅ **Require status checks to pass before merging**

  - Require branches to be up to date before merging
  - Status checks: `ci/tests`, `ci/lint`, `ci/build`

- ✅ **Require conversation resolution before merging**
- ✅ **Require signed commits**
- ✅ **Require linear history**
- ✅ **Include administrators**
- ✅ **Restrict pushes that create files larger than 100 MB**

### Develop Branch Protection

**Settings → Branches → Add rule for `develop`:**

- ✅ **Require a pull request before merging**

  - Require approvals: **1** (minimum)
  - Dismiss stale PR approvals when new commits are pushed

- ✅ **Require status checks to pass before merging**

  - Require branches to be up to date before merging
  - Status checks: `ci/tests`, `ci/lint`

- ✅ **Require conversation resolution before merging**
- ✅ **Include administrators**

## 👥 Team Collaboration Setup

### 1. Repository Settings

**Settings → General:**

- ✅ **Issues**: Enable issues
- ✅ **Pull requests**: Enable pull requests
- ✅ **Wikis**: Enable wikis
- ✅ **Discussions**: Enable discussions
- ✅ **Projects**: Enable projects

### 2. Issue Templates

Create `.github/ISSUE_TEMPLATE/` directory with:

**bug_report.md:**

```markdown
---
name: Bug report
about: Create a report to help us improve
title: ""
labels: "bug"
assignees: ""
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**

- OS: [e.g. Windows 10]
- Browser: [e.g. Chrome 120]
- Version: [e.g. 1.0.0]

**Additional context**
Add any other context about the problem here.
```

**feature_request.md:**

```markdown
---
name: Feature request
about: Suggest an idea for this project
title: ""
labels: "enhancement"
assignees: ""
---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

### 3. Pull Request Template

Create `.github/pull_request_template.md:`

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

## 📋 Project Board Setup

### 1. Create Project Board

**Projects → New project:**

- **Template**: Board (Kanban)
- **Name**: Caliber Development
- **Description**: Project management board for Caliber development

### 2. Configure Columns

- **To Do**: New issues and tasks
- **In Progress**: Currently being worked on
- **Review**: Ready for code review
- **Testing**: Ready for testing
- **Done**: Completed and deployed

### 3. Automation Rules

- **When issues are created**: Move to "To Do"
- **When PRs are opened**: Move to "In Progress"
- **When PRs are ready for review**: Move to "Review"
- **When PRs are merged**: Move to "Done"

## 🔧 GitHub Actions Setup

### 1. Create Workflow Directory

```bash
mkdir -p .github/workflows
```

### 2. CI/CD Workflow

Create `.github/workflows/ci.yml:`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm test

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Lint backend
        run: |
          cd backend
          pip install flake8
          flake8 .
      - name: Lint frontend
        run: |
          cd frontend
          npm run lint
```

## 🔐 Security Settings

### 1. Security & Analysis

**Settings → Security & analysis:**

- ✅ **Dependency graph**: Enable
- ✅ **Dependabot alerts**: Enable
- ✅ **Dependabot security updates**: Enable
- ✅ **Code scanning**: Enable (if using GitHub Advanced Security)

### 2. Secrets Management

**Settings → Secrets and variables → Actions:**

Add the following secrets:

- `DATABASE_URL`
- `REDIS_URL`
- `FIREBASE_SERVICE_ACCOUNT`
- `OPENAI_API_KEY`
- `JWT_SECRET`

## 📊 Repository Insights

### 1. Enable Insights

**Settings → General:**

- ✅ **Allow forking**: Enable
- ✅ **Allow squash merging**: Enable
- ✅ **Allow rebase merging**: Enable
- ✅ **Allow merge commits**: Disable (for linear history)

### 2. Code Owners

Create `.github/CODEOWNERS:`

```
# Global owners
* @project-admin

# Backend
/backend/ @backend-team

# Frontend
/frontend/ @frontend-team

# Documentation
/docs/ @docs-team

# Infrastructure
/docker-compose.yml @devops-team
/.github/ @devops-team
```

## 🚀 Deployment Integration

### 1. Environment Setup

**Settings → Environments:**

Create environments:

- **staging**: For develop branch deployments
- **production**: For main branch deployments

### 2. Deployment Protection

For each environment:

- ✅ **Required reviewers**: Add deployment approvers
- ✅ **Wait timer**: 5 minutes (optional)
- ✅ **Deployment branches**: Restrict to specific branches

## 📈 Monitoring & Analytics

### 1. Enable Analytics

**Settings → General:**

- ✅ **Repository insights**: Enable
- ✅ **Dependency insights**: Enable

### 2. Set up Notifications

**Settings → Notifications:**

Configure team notifications for:

- Pull request reviews
- Issue assignments
- Security alerts
- Deployment status

## ✅ Verification Checklist

- [ ] Repository created and connected
- [ ] Branch protection rules configured
- [ ] Issue and PR templates added
- [ ] Project board created
- [ ] GitHub Actions workflows configured
- [ ] Security settings enabled
- [ ] Team permissions set
- [ ] Code owners configured
- [ ] Environments created
- [ ] Notifications configured

## 🆘 Troubleshooting

### Common Issues

1. **Branch protection not working**: Ensure you're an admin or have proper permissions
2. **Actions not running**: Check workflow file syntax and triggers
3. **Secrets not available**: Verify secret names match workflow references
4. **PR templates not showing**: Ensure file is in correct location and format

### Support

For GitHub-specific issues:

- Check GitHub documentation
- Contact GitHub support
- Review repository settings
- Verify team permissions
