"""
LetterOn Server - Authentication Tests
Purpose: Test auth endpoints and JWT functionality
Testing: pytest tests/test_auth.py -v
AWS Deployment: Not deployed (tests only)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.auth import hash_password, verify_password, create_access_token, verify_token


client = TestClient(app)


# ===== PASSWORD HASHING TESTS =====

def test_hash_password():
    """Test password hashing."""
    password = "testpassword123"
    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "testpassword123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "testpassword123"
    hashed = hash_password(password)

    assert verify_password("wrongpassword", hashed) is False


# ===== JWT TOKEN TESTS =====

def test_create_access_token():
    """Test JWT token creation."""
    data = {"user_id": "123", "email": "test@example.com"}
    token = create_access_token(data)

    assert token is not None
    assert len(token) > 0
    assert isinstance(token, str)


def test_verify_token_valid():
    """Test JWT token verification with valid token."""
    data = {"user_id": "123", "email": "test@example.com"}
    token = create_access_token(data)

    user_id = verify_token(token)

    assert user_id == "123"


def test_verify_token_invalid():
    """Test JWT token verification with invalid token."""
    invalid_token = "invalid.token.string"

    user_id = verify_token(invalid_token)

    assert user_id is None


# ===== REGISTRATION ENDPOINT TESTS =====

@patch('app.api.auth.dynamodb_client')
def test_register_success(mock_db):
    """Test successful user registration."""
    # Mock database responses
    mock_db.get_user_by_email.return_value = None  # User doesn't exist
    mock_db.create_user.return_value = {
        "user_id": "123",
        "email": "newuser@example.com",
        "name": "New User",
        "created_at": 1234567890
    }

    response = client.post(
        "/auth/register",
        json={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["name"] == "New User"


@patch('app.api.auth.dynamodb_client')
def test_register_duplicate_email(mock_db):
    """Test registration with existing email."""
    # Mock database to return existing user
    mock_db.get_user_by_email.return_value = {
        "user_id": "123",
        "email": "existing@example.com"
    }

    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "existing@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_register_invalid_email():
    """Test registration with invalid email."""
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "invalid-email",
            "password": "password123"
        }
    )

    assert response.status_code == 422  # Validation error


def test_register_short_password():
    """Test registration with too short password."""
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "short"
        }
    )

    assert response.status_code == 422  # Validation error


# ===== LOGIN ENDPOINT TESTS =====

@patch('app.api.auth.dynamodb_client')
def test_login_success(mock_db):
    """Test successful login."""
    # Hash a test password
    test_password = "testpassword123"
    password_hash = hash_password(test_password)

    # Mock database response
    mock_db.get_user_by_email.return_value = {
        "user_id": "123",
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": password_hash
    }

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": test_password
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"


@patch('app.api.auth.dynamodb_client')
def test_login_wrong_password(mock_db):
    """Test login with incorrect password."""
    password_hash = hash_password("correctpassword")

    mock_db.get_user_by_email.return_value = {
        "user_id": "123",
        "email": "test@example.com",
        "password_hash": password_hash
    }

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


@patch('app.api.auth.dynamodb_client')
def test_login_user_not_found(mock_db):
    """Test login with non-existent user."""
    mock_db.get_user_by_email.return_value = None

    response = client.post(
        "/auth/login",
        json={
            "email": "notfound@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


# ===== LOGOUT ENDPOINT TESTS =====

@patch('app.dependencies.dynamodb_client')
def test_logout_success(mock_db):
    """Test successful logout."""
    # Create a valid token
    token = create_access_token({"user_id": "123", "email": "test@example.com"})

    # Mock user exists
    mock_db.get_user_by_id.return_value = {
        "user_id": "123",
        "email": "test@example.com"
    }

    response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert "Logged out" in response.json()["message"]


def test_logout_without_token():
    """Test logout without authentication token."""
    response = client.post("/auth/logout")

    assert response.status_code == 403  # Forbidden (no auth header)


def test_logout_invalid_token():
    """Test logout with invalid token."""
    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer invalid.token.here"}
    )

    assert response.status_code == 401  # Unauthorized


# ===== GET CURRENT USER TESTS =====

@patch('app.dependencies.dynamodb_client')
def test_get_current_user_success(mock_db):
    """Test getting current user info."""
    # Create a valid token
    token = create_access_token({"user_id": "123", "email": "test@example.com"})

    # Mock database response
    mock_db.get_user_by_id.return_value = {
        "user_id": "123",
        "email": "test@example.com",
        "name": "Test User"
    }

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "123"
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


def test_get_current_user_no_token():
    """Test getting current user without token."""
    response = client.get("/auth/me")

    assert response.status_code == 403


@patch('app.dependencies.dynamodb_client')
def test_get_current_user_not_found(mock_db):
    """Test getting current user when user doesn't exist in database."""
    token = create_access_token({"user_id": "999", "email": "test@example.com"})

    mock_db.get_user_by_id.return_value = None

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
