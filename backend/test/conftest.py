"""
Pytest configuration and fixtures for backend testing.

This module provides shared fixtures for all backend tests including:
- Database session management (using test database)
- FastAPI test client
- Test users and authentication tokens
- Test data fixtures
"""
import pytest
import os
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from datetime import date, datetime

# Import application modules
# When running from /app (Docker container) or with PYTHONPATH set
try:
    from app.database import Base, get_db
    from app.main import app
    from app.config import get_settings, reset_settings
    from app.models.user import User
    from app.models.admin_user import AdminUser
    from app.models.department import Department
    from app.services.auth_service import AuthService
except ImportError:
    # Fallback for running with backend. prefix
    from backend.app.database import Base, get_db
    from backend.app.main import app
    from backend.app.config import get_settings, reset_settings
    from backend.app.models.user import User
    from backend.app.models.admin_user import AdminUser
    from backend.app.models.department import Department
    from backend.app.services.auth_service import AuthService


# ============================================================================
# Test Database Configuration
# ============================================================================

# Use environment variable for test database URL, with sensible defaults
# In Docker: postgresql+psycopg://postgres:postgres@postgres:5432/home_health_test
# Locally: postgresql+psycopg://postgres:postgres@localhost:5432/home_health_test
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@postgres:5432/home_health_test"
)

# Create test database engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"options": "-c timezone=UTC"},
    pool_pre_ping=True,
)

# Create test session factory
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_db_engine():
    """
    Session-scoped database engine.
    Creates all tables at the start of the test session and drops them at the end.
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    # Drop all tables after all tests complete
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Function-scoped database session.
    Each test gets a fresh session that is rolled back after the test.
    This ensures tests don't affect each other.
    """
    connection = test_db_engine.connect()
    transaction = connection.begin()

    # Create a session bound to this transaction
    session = TestingSessionLocal(bind=connection)

    yield session

    # Cleanup: rollback all changes, close session and connection
    session.rollback()
    session.close()
    connection.close()


# ============================================================================
# FastAPI Test Client Fixture
# ============================================================================

@pytest.fixture(scope="function")
def test_client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Function-scoped FastAPI test client with database dependency override.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    client = TestClient(app)

    yield client

    # Clean up overrides
    app.dependency_overrides.clear()


# ============================================================================
# Test User Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """
    Creates a test user in the database.
    Returns the User object.
    """
    user = User(
        phone="13800138000",
        nickname="测试用户",
        gender="male",
        is_profile_completed=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_2(db_session: Session) -> User:
    """
    Creates a second test user in the database.
    Useful for testing multi-user scenarios.
    """
    user = User(
        phone="13900139000",
        nickname="测试用户2",
        gender="female",
        is_profile_completed=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_with_password(db_session: Session) -> User:
    """
    Creates a test user with a password set.
    Useful for testing password login.
    """
    from backend.app.services.auth_service import AuthService

    user, _ = AuthService.register_with_password(
        db_session,
        phone="13800138001",
        password="TestPassword123"
    )
    return user


@pytest.fixture(scope="function")
def test_user_token(db_session: Session, test_user: User) -> str:
    """
    Creates a test user and returns a valid JWT token for authentication.
    """
    token = AuthService.create_token(test_user.id, "access")
    return token


@pytest.fixture(scope="function")
def test_user_headers(db_session: Session, test_user: User) -> dict:
    """
    Creates a test user and returns headers with Authorization token.
    """
    token = AuthService.create_token(test_user.id, "access")
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Admin User Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_admin(db_session: Session) -> AdminUser:
    """
    Creates a test admin user in the database.
    Returns the AdminUser object.
    """
    try:
        from app.services.admin_auth_service import AdminAuthService
    except ImportError:
        from backend.app.services.admin_auth_service import AdminAuthService

    admin = AdminUser(
        username="test_admin",
        full_name="测试管理员",
        is_active=True,
    )
    admin.password_hash = AdminAuthService.hash_password("AdminPassword123")
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def test_admin_token(test_admin: AdminUser) -> str:
    """
    Creates a test admin and returns a valid JWT token for authentication.
    """
    try:
        from app.services.admin_auth_service import AdminAuthService
    except ImportError:
        from backend.app.services.admin_auth_service import AdminAuthService
    token = AdminAuthService.create_admin_token(test_admin.id)
    return token


@pytest.fixture(scope="function")
def test_admin_headers(test_admin: AdminUser) -> dict:
    """
    Creates a test admin and returns headers with Authorization token.
    """
    try:
        from app.services.admin_auth_service import AdminAuthService
    except ImportError:
        from backend.app.services.admin_auth_service import AdminAuthService
    token = AdminAuthService.create_admin_token(test_admin.id)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Doctor Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_doctor(db_session: Session) -> AdminUser:
    """
    Creates a test doctor in the database.
    Returns the AdminUser object with doctor role.
    """
    try:
        from app.services.admin_auth_service import AdminAuthService
    except ImportError:
        from backend.app.services.admin_auth_service import AdminAuthService

    doctor = AdminUser(
        username="test_doctor",
        full_name="测试医生",
        role="doctor",
        is_active=True,
    )
    doctor.password_hash = AdminAuthService.hash_password("DoctorPassword123")
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return doctor


@pytest.fixture(scope="function")
def test_doctor_headers(test_doctor: AdminUser) -> dict:
    """
    Creates a test doctor and returns headers with Authorization token.
    """
    try:
        from app.services.admin_auth_service import AdminAuthService
    except ImportError:
        from backend.app.services.admin_auth_service import AdminAuthService
    token = AdminAuthService.create_admin_token(test_doctor.id)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Department Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_department(db_session: Session) -> Department:
    """
    Creates a test department in the database.
    Returns the Department object.
    """
    department = Department(
        name="内科",
        description="内科科室",
        icon="heart-pulse",
        sort_order=1,
    )
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department


# ============================================================================
# Test Mode Token Fixture
# ============================================================================

@pytest.fixture(scope="function")
def test_mode_token() -> str:
    """
    Returns a test mode token that bypasses authentication in TEST_MODE.
    The token format is test_N where N is the user_id.

    Note: This only works when TEST_MODE=true is set in environment.
    """
    return "test_1"


@pytest.fixture(scope="function")
def test_mode_headers() -> dict:
    """
    Returns headers with test mode Authorization token.
    The token format is test_N where N is the user_id.

    Note: This only works when TEST_MODE=true is set in environment.
    """
    return {"Authorization": "Bearer test_1"}


# ============================================================================
# Verification Code Fixture
# ============================================================================

@pytest.fixture(scope="function")
def test_verification_code() -> str:
    """
    Returns the universal test verification code.
    In TEST_MODE, 000000 is a valid code for any phone number.

    Note: This only works when TEST_MODE=true is set in environment.
    """
    return "000000"


# ============================================================================
# Settings Override Fixture
# ============================================================================

@pytest.fixture(scope="function")
def test_settings():
    """
    Fixture that provides test settings and resets them after the test.
    """
    reset_settings()
    original_test_mode = os.getenv("TEST_MODE")

    # Set test mode for testing
    os.environ["TEST_MODE"] = "true"

    yield get_settings()

    # Restore original settings
    if original_test_mode is not None:
        os.environ["TEST_MODE"] = original_test_mode
    else:
        os.environ.pop("TEST_MODE", None)

    reset_settings()


# ============================================================================
# Autouse fixtures - run automatically for each test
# ============================================================================

@pytest.fixture(autouse=True)
def reset_settings_before_each_test():
    """
    Automatically reset settings before each test to ensure clean state.
    """
    reset_settings()
    yield
    reset_settings()
