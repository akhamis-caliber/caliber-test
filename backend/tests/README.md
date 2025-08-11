# 🧪 Caliber Backend Test Suite

This directory contains comprehensive tests for the Caliber Backend authentication service and other components.

## 📋 Test Coverage

### 🔐 Authentication Service Tests (`test_auth_service.py`)

#### **1. Firebase Token Verification**
- ✅ **Valid Firebase Token**: Test that valid Firebase tokens are accepted and decoded correctly
- ✅ **Invalid Firebase Token**: Test that invalid tokens return 401 Unauthorized
- ✅ **User Creation**: Test that new users are created from valid Firebase tokens

#### **2. JWT Token Generation**
- ✅ **Token Structure**: Verify JWT tokens have correct format (header.payload.signature)
- ✅ **Token Payload**: Ensure tokens contain correct user information
- ✅ **Token Expiration**: Verify access and refresh tokens have different expiration times

#### **3. Refresh Token Flow**
- ✅ **Token Refresh**: Test that refresh tokens issue new valid JWT tokens
- ✅ **Invalid Refresh**: Test that invalid refresh tokens are rejected
- ✅ **Expired Refresh**: Test that expired refresh tokens are rejected

#### **4. Password Security**
- ✅ **Password Hashing**: Verify passwords are stored hashed (bcrypt) never in plaintext
- ✅ **Password Verification**: Test that password verification works with hashed passwords
- ✅ **Incorrect Password**: Test that incorrect passwords are rejected during login

#### **5. Role-Based Access Control**
- ✅ **Admin Access**: Test that admin users can access all endpoints
- ✅ **User Access**: Test that regular users have appropriate access levels
- ✅ **Viewer Access**: Test that viewer users have limited access
- ✅ **Inactive Users**: Test that inactive users cannot access protected endpoints

#### **6. Multi-Tenant Organization Access**
- ✅ **Organization Isolation**: Test that users cannot access data from other organizations
- ✅ **Tenant Boundaries**: Verify organization isolation is properly enforced

#### **7. Audit Logging**
- ✅ **Login Events**: Test that login events are logged with correct details
- ✅ **Logout Events**: Test that logout events are logged
- ✅ **Token Refresh**: Test that token refresh events are logged
- ✅ **User Registration**: Test that user registration events are logged

#### **8. User Management**
- ✅ **Profile Updates**: Test that users can update their profiles
- ✅ **Account Deletion**: Test that users can delete their accounts (soft delete)
- ✅ **User Info**: Test that /me endpoint returns correct user information

#### **9. Security Features**
- ✅ **CORS Headers**: Test that CORS headers are properly set
- ✅ **Rate Limiting**: Test that rate limiting is configured
- ✅ **Security Headers**: Test that security headers are present

#### **10. Error Handling**
- ✅ **Malformed JSON**: Test that malformed JSON returns 422
- ✅ **Missing Fields**: Test that missing required fields return 422
- ✅ **Invalid Email**: Test that invalid email format returns 422
- ✅ **Duplicate Email**: Test that duplicate email registration returns 400

## 🚀 Running Tests

### **Prerequisites**
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Ensure you're in the backend directory
cd caliber/backend
```

### **Quick Start**
```bash
# Run all tests
python run_tests.py

# Run only authentication tests
python run_tests.py auth

# Run with pytest directly
python -m pytest tests/ -v
```

### **Test Commands**
```bash
# Run all tests
python run_tests.py all

# Run specific test categories
python run_tests.py auth          # Authentication tests only
python run_tests.py unit          # Unit tests only
python run_tests.py integration   # Integration tests only

# Run with coverage
python run_tests.py coverage

# Show help
python run_tests.py help
```

### **Pytest Commands**
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth_service.py -v

# Run specific test class
python -m pytest tests/test_auth_service.py::TestFirebaseTokenVerification -v

# Run specific test method
python -m pytest tests/test_auth_service.py::TestFirebaseTokenVerification::test_valid_firebase_token_accepted -v

# Run tests with markers
python -m pytest tests/ -m auth -v
python -m pytest tests/ -m security -v

# Run tests with coverage
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term
```

## 🏗️ Test Architecture

### **Test Fixtures (`conftest.py`)**
- **Database Setup**: SQLite test database with automatic cleanup
- **User Fixtures**: Test users with different roles (Admin, User, Viewer)
- **Organization Fixtures**: Test organizations for multi-tenant testing
- **Authentication Headers**: Pre-generated auth headers for different user types
- **Mock Services**: Mocked Firebase and OpenAI services

### **Test Database**
- **SQLite**: In-memory SQLite database for fast test execution
- **Automatic Cleanup**: Database is recreated for each test function
- **Isolated Tests**: Each test runs in isolation with fresh data

### **Mocking Strategy**
- **Firebase**: Mocked Firebase token verification
- **OpenAI**: Mocked OpenAI API calls
- **External Services**: All external dependencies are mocked

## 📊 Test Results

### **Expected Test Count**
- **Total Tests**: ~50+ authentication service tests
- **Coverage**: Comprehensive coverage of all authentication flows
- **Execution Time**: Fast execution with SQLite test database

### **Test Categories**
- **Unit Tests**: Individual function and method testing
- **Integration Tests**: End-to-end API endpoint testing
- **Security Tests**: Authentication and authorization testing
- **Error Handling**: Edge cases and error scenarios

## 🔧 Configuration

### **Environment Variables**
Tests use a minimal configuration that doesn't require external services:
- **Database**: SQLite test database
- **Authentication**: Mocked Firebase service
- **AI Services**: Mocked OpenAI API

### **Test Settings**
- **Database URL**: `sqlite:///./test.db`
- **Logging**: Minimal logging for test output
- **CORS**: Test-appropriate CORS settings

## 🐛 Troubleshooting

### **Common Issues**

#### **Import Errors**
```bash
# Ensure you're in the backend directory
cd caliber/backend

# Check Python path
python -c "import sys; print(sys.path)"
```

#### **Database Errors**
```bash
# Clean up test database
rm -f test.db

# Recreate test environment
python -m pytest tests/ --setup-show
```

#### **Mock Issues**
```bash
# Check mock configuration
python -c "from unittest.mock import patch; print('Mock available')"
```

### **Debug Mode**
```bash
# Run tests with debug output
python -m pytest tests/ -v -s --tb=long

# Run single test with debug
python -m pytest tests/test_auth_service.py::TestFirebaseTokenVerification::test_valid_firebase_token_accepted -v -s
```

## 📈 Continuous Integration

### **GitHub Actions**
Tests are automatically run in CI/CD pipeline:
- **On Push**: Run all tests on every commit
- **On PR**: Run tests before merging
- **Coverage**: Generate coverage reports

### **Local Development**
```bash
# Pre-commit hook (optional)
pip install pre-commit
pre-commit install

# Run tests before committing
python run_tests.py all
```

## 🎯 Best Practices

### **Test Writing**
- **Descriptive Names**: Use clear, descriptive test method names
- **Single Responsibility**: Each test should test one specific behavior
- **Proper Assertions**: Use specific assertions with clear error messages
- **Test Isolation**: Tests should not depend on each other

### **Test Data**
- **Realistic Data**: Use realistic but safe test data
- **Edge Cases**: Include boundary conditions and error scenarios
- **Cleanup**: Always clean up test data

### **Performance**
- **Fast Execution**: Tests should run quickly (under 1 second each)
- **Efficient Setup**: Minimize setup and teardown overhead
- **Resource Management**: Use in-memory databases and mocked services

## 🔮 Future Enhancements

### **Planned Features**
- **Performance Testing**: Load and stress testing
- **Security Testing**: Penetration testing and vulnerability scanning
- **API Contract Testing**: OpenAPI specification validation
- **Database Migration Testing**: Test database schema changes

### **Test Expansion**
- **Campaign Service Tests**: Test campaign management functionality
- **Scoring Service Tests**: Test scoring engine functionality
- **Report Service Tests**: Test report generation functionality
- **AI Service Tests**: Test AI insights generation

## 📚 Additional Resources

### **Documentation**
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

### **Examples**
- **Test Files**: See individual test files for examples
- **Fixtures**: Check `conftest.py` for fixture examples
- **Mocking**: See test files for mocking examples

---

**Happy Testing! 🧪✨**



