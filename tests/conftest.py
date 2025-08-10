import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.main import app
from backend.models.database import User
from backend.models.engine import db_session
from backend.modules.auth import auth_methods


# Create test database engine with in-memory SQLite
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    def get_current_user_override():
        # For endpoints with optional authentication, return None
        # For endpoints with required authentication, this will cause a 422 error
        # which is better than a 401 for testing purposes
        return None

    app.dependency_overrides[db_session] = get_session_override
    app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="unauthorized_client")
def unauthorized_client_fixture(session: Session):
    """Create a test client without authentication override for testing unauthorized access"""

    def get_session_override():
        return session

    app.dependency_overrides[db_session] = get_session_override
    # Don't override get_current_user to test actual authentication
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {"name": "Test User", "email": "test@example.com", "password": "testpassword123"}


@pytest.fixture
def test_user(session: Session, test_user_data):
    """Create a test user in the database"""
    hashed_password = auth_methods.hash_password(test_user_data["password"])
    user = User(name=test_user_data["name"], email=test_user_data["email"], password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for testing protected endpoints"""
    access_token = auth_methods.create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(name="auth_client")
def auth_client_fixture(session: Session, test_user):
    """Create a test client with authentication override"""

    def get_session_override():
        return session

    def get_current_user_override():
        return test_user.id

    app.dependency_overrides[db_session] = get_session_override
    app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def another_user_data():
    """Another sample user data for testing conflicts"""
    return {"name": "Another User", "email": "another@example.com", "password": "anotherpassword123"}
