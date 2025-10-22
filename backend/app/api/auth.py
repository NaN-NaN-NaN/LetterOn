"""
LetterOn Server - Authentication API Routes
Purpose: User registration, login, and logout endpoints
Testing: Use FastAPI TestClient for endpoint testing
AWS Deployment: No special configuration needed

Endpoints:
- POST /auth/register - Register new user
- POST /auth/login - Login and get JWT token
- POST /auth/logout - Logout (client-side token invalidation)
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends

from app.models import (
    UserRegisterRequest,
    UserLoginRequest,
    AuthResponse,
    UserResponse,
    MessageResponse,
    ErrorResponse
)
from app.services.auth import hash_password, verify_password, create_access_token
from app.services.dynamo import dynamodb_client
from app.dependencies import get_current_user_id
from app.utils.helpers import is_valid_email

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or user already exists"},
    }
)
async def register(user_data: UserRegisterRequest):
    """
    Register a new user.

    Creates a new user account with hashed password and returns JWT token.

    Args:
        user_data: User registration data (name, email, password)

    Returns:
        AuthResponse: JWT token and user information

    Raises:
        HTTPException 400: If email is already registered or invalid
    """
    logger.info(f"Registration attempt for email: {user_data.email}")

    # Validate email format
    if not is_valid_email(user_data.email):
        logger.warning(f"Invalid email format: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # Check if user already exists
    existing_user = dynamodb_client.get_user_by_email(user_data.email)
    if existing_user:
        logger.warning(f"User already exists: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Hash password
    password_hash = hash_password(user_data.password)

    # Create user
    try:
        user = dynamodb_client.create_user({
            "email": user_data.email,
            "password_hash": password_hash,
            "name": user_data.name
        })

        logger.info(f"User registered successfully: {user['user_id']}")

        # Generate JWT token
        access_token = create_access_token(
            data={
                "user_id": user["user_id"],
                "email": user["email"]
            }
        )

        return AuthResponse(
            token=access_token,
            user=UserResponse(
                user_id=user["user_id"],
                name=user["name"],
                email=user["email"]
            )
        )

    except Exception as e:
        logger.error(f"Error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user account"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    }
)
async def login(credentials: UserLoginRequest):
    """
    Login with email and password.

    Verifies credentials and returns JWT token.

    Args:
        credentials: User login credentials (email, password)

    Returns:
        AuthResponse: JWT token and user information

    Raises:
        HTTPException 401: If credentials are invalid
    """
    logger.info(f"Login attempt for email: {credentials.email}")

    # Get user by email
    user = dynamodb_client.get_user_by_email(credentials.email)

    if not user:
        logger.warning(f"Login failed: user not found - {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        logger.warning(f"Login failed: incorrect password - {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    logger.info(f"User logged in successfully: {user['user_id']}")

    # Generate JWT token
    access_token = create_access_token(
        data={
            "user_id": user["user_id"],
            "email": user["email"]
        }
    )

    return AuthResponse(
        token=access_token,
        user=UserResponse(
            user_id=user["user_id"],
            name=user["name"],
            email=user["email"]
        )
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    responses={
        200: {"model": MessageResponse, "description": "Logout successful"},
    }
)
async def logout(user_id: str = Depends(get_current_user_id)):
    """
    Logout current user.

    Note: Since we use stateless JWT tokens, logout is handled client-side
    by removing the token. This endpoint just validates the token and
    returns a success message.

    For production with token blacklisting:
    - Store revoked tokens in Redis with TTL = token expiration
    - Check token against blacklist in get_current_user_id dependency

    Args:
        user_id: Current user ID from JWT token

    Returns:
        MessageResponse: Success message
    """
    logger.info(f"User logged out: {user_id}")

    # TODO: For production, implement token blacklisting
    # Example:
    # redis_client.setex(f"revoked_token:{token}", ttl=JWT_EXPIRATION, "1")

    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    }
)
async def get_current_user_info(user_id: str = Depends(get_current_user_id)):
    """
    Get current authenticated user information.

    Args:
        user_id: Current user ID from JWT token

    Returns:
        UserResponse: Current user information

    Raises:
        HTTPException 404: If user not found
    """
    user = dynamodb_client.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        user_id=user["user_id"],
        name=user["name"],
        email=user["email"]
    )
