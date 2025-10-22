"""
LetterOn Server - Authentication Service
Purpose: JWT token generation and verification, password hashing
Testing: Unit test token generation and verification
AWS Deployment: No special configuration needed

This module provides:
- Password hashing with bcrypt
- JWT token generation
- JWT token verification
- Token decoding and validation
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.settings import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (typically {"user_id": "...", "email": "..."})
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token

    Example:
        token = create_access_token(
            data={"user_id": "123", "email": "user@example.com"}
        )
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    # Encode JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )

    logger.debug(f"Access token created for data: {data}")
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Dict: Decoded token payload or None if invalid

    Example:
        payload = decode_access_token(token)
        if payload:
            user_id = payload["user_id"]
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        logger.debug(f"Token decoded successfully: {payload.get('user_id')}")
        return payload

    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return None


def verify_token(token: str) -> Optional[str]:
    """
    Verify a JWT token and return the user_id if valid.

    Args:
        token: JWT token string

    Returns:
        str: user_id if token is valid, None otherwise

    Example:
        user_id = verify_token(token)
        if not user_id:
            raise HTTPException(401, "Invalid token")
    """
    payload = decode_access_token(token)

    if payload is None:
        return None

    user_id = payload.get("user_id")

    if user_id is None:
        logger.warning("Token missing user_id")
        return None

    return user_id


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from a JWT token.

    Args:
        token: JWT token string

    Returns:
        Dict with user info (user_id, email) or None if invalid
    """
    payload = decode_access_token(token)

    if payload is None:
        return None

    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
    }
