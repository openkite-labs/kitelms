"""Test utilities and helper functions"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt

from backend.core.settings import settings
from backend.models.database import User
from backend.modules.auth import auth_methods


def create_test_user_data(
    email: str = "test@example.com", name: str = "Test User", password: str = "testpass123"
    ) -> Dict[str, str]:
    """Create test user data dictionary"""
    return {
        "name": name,
        "email": email,
        "password": password
    }


def create_test_user_in_db(session, user_data: Dict[str, str]) -> User:
    """Create a test user in the database"""
    hashed_password = auth_methods.hash_password(user_data["password"])
    user = User(
        name=user_data["name"],
        email=user_data["email"],
        password=hashed_password
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_access_token_for_user(email: str, expire_minutes: int = 30) -> str:
    """Create an access token for testing"""
    data = {"sub": email}
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    data.update({"exp": expire})
    return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_expired_token(email: str) -> str:
    """Create an expired token for testing"""
    data = {"sub": email}
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)  # Expired 1 minute ago
    data.update({"exp": expire})
    return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def get_auth_headers(token: str) -> Dict[str, str]:
    """Get authorization headers for API requests"""
    return {"Authorization": f"Bearer {token}"}


def assert_user_response_format(response_data: Dict[str, Any], expected_email: str, expected_name: str):
    """Assert that user response has correct format"""
    assert "id" in response_data
    assert "name" in response_data
    assert "email" in response_data
    assert "password" not in response_data  # Password should never be in response
    assert response_data["email"] == expected_email
    assert response_data["name"] == expected_name
    assert isinstance(response_data["id"], str)
    assert len(response_data["id"]) > 0


def assert_login_response_format(response_data: Dict[str, Any]):
    """Assert that login response has correct format"""
    assert "access_token" in response_data
    assert "token_type" in response_data
    assert response_data["token_type"] == "bearer"
    assert isinstance(response_data["access_token"], str)
    assert len(response_data["access_token"]) > 0


def assert_error_response_format(response_data: Dict[str, Any], expected_detail: str = None):
    """Assert that error response has correct format"""
    assert "detail" in response_data
    if expected_detail:
        assert expected_detail in response_data["detail"]
