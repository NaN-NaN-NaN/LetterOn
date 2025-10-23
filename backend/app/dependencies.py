"""
LetterOn Server - FastAPI Dependencies
Purpose: Reusable dependencies for authentication and authorization
Testing: Mock these dependencies in tests
AWS Deployment: No special configuration needed

This module provides:
- JWT authentication dependency
- User extraction from token
- Protected route decorator
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth import verify_token, get_user_from_token
from app.services.dynamo import dynamodb_client

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and verify user_id from JWT token.

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        str: user_id

    Raises:
        HTTPException: 401 if token is invalid or missing

    Usage:
        @app.get("/protected")
        async def protected_route(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    token = credentials.credentials
    print("HAHAHAHA",credentials )
    user_id = verify_token(token)

    if not user_id:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Extract full user information from JWT token and verify in database.

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        dict: Full user object from database

    Raises:
        HTTPException: 401 if token is invalid or user not found

    Usage:
        @app.get("/profile")
        async def get_profile(user: dict = Depends(get_current_user)):
            return user
    """
    token = credentials.credentials

    # Decode token
    user_info = get_user_from_token(token)

    if not user_info or not user_info.get("user_id"):
        logger.warning("Invalid token: missing user information")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = user_info["user_id"]

    # Verify user exists in database
    user = dynamodb_client.get_user_by_id(user_id)

    if not user:
        logger.warning(f"User not found in database: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Extract user_id from token if present, None otherwise.

    Useful for endpoints that work differently for authenticated vs anonymous users.

    Args:
        credentials: Optional HTTP Authorization header

    Returns:
        str: user_id or None
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        user_id = verify_token(token)
        return user_id
    except Exception:
        return None
