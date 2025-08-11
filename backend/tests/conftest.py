import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys
from unittest.mock import Mock, patch

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from config.database import get_db
from db.models import Base, User, Organization, UserOrganization, UserRole
from auth_service.models.user import UserService
from auth_service.jwt_manager import create_user_tokens
from config.settings import settings

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with a fresh database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_organization(db_session):
    """Create a test organization."""
    org = Organization(
        name="Test Organization",
        description="Test organization for testing",
        is_active=True
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture(scope="function")
def test_user(db_session, test_organization):
    """Create a test user."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create user-organization relationship
    user_org = UserOrganization(
        user_id=user.id,
        organization_id=test_organization.id,
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user_org)
    db_session.commit()
    
    return user

@pytest.fixture(scope="function")
def test_admin_user(db_session, test_organization):
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    
    # Create user-organization relationship
    user_org = UserOrganization(
        user_id=admin.id,
        organization_id=test_organization.id,
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user_org)
    db_session.commit()
    
    return admin

@pytest.fixture(scope="function")
def test_viewer_user(db_session, test_organization):
    """Create a test viewer user."""
    viewer = User(
        email="viewer@example.com",
        full_name="Viewer User",
        role=UserRole.VIEWER,
        is_active=True
    )
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(viewer)
    
    # Create user-organization relationship
    user_org = UserOrganization(
        user_id=viewer.id,
        organization_id=test_organization.id,
        role=UserRole.VIEWER,
        is_active=True
    )
    db_session.add(user_org)
    db_session.commit()
    
    return viewer

@pytest.fixture(scope="function")
def test_organization_2(db_session):
    """Create a second test organization for multi-tenant testing."""
    org = Organization(
        name="Test Organization 2",
        description="Second test organization for testing",
        is_active=True
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org

@pytest.fixture(scope="function")
def test_user_org2(db_session, test_organization_2):
    """Create a test user in the second organization."""
    user = User(
        email="user2@example.com",
        full_name="User 2",
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create user-organization relationship
    user_org = UserOrganization(
        user_id=user.id,
        organization_id=test_organization_2.id,
        role=UserRole.USER,
        is_active=True
    )
    db_session.add(user_org)
    db_session.commit()
    
    return user

@pytest.fixture(scope="function")
def valid_firebase_token():
    """Mock valid Firebase token payload."""
    return {
        "uid": "test_firebase_uid_123",
        "email": "firebase@example.com",
        "name": "Firebase User",
        "email_verified": True
    }

@pytest.fixture(scope="function")
def invalid_firebase_token():
    """Mock invalid Firebase token."""
    return "invalid_token_string"

@pytest.fixture(scope="function")
def mock_firebase_verify():
    """Mock Firebase token verification."""
    with patch('auth_service.firebase_verify.verify_google_token') as mock:
        yield mock

@pytest.fixture(scope="function")
def mock_openai():
    """Mock OpenAI API calls."""
    with patch('ai_service.insight_generator.openai') as mock:
        yield mock

@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Generate authentication headers for a test user."""
    tokens = create_user_tokens(test_user.id, test_user.email)
    return {"Authorization": f"Bearer {tokens['access_token']}"}

@pytest.fixture(scope="function")
def admin_auth_headers(test_admin_user):
    """Generate authentication headers for an admin user."""
    tokens = create_user_tokens(test_admin_user.id, test_admin_user.email)
    return {"Authorization": f"Bearer {tokens['access_token']}"}

@pytest.fixture(scope="function")
def viewer_auth_headers(test_viewer_user):
    """Generate authentication headers for a viewer user."""
    tokens = create_user_tokens(test_viewer_user.id, test_viewer_user.email)
    return {"Authorization": f"Bearer {tokens['access_token']}"}



