"""Reusable FastAPI dependencies."""
from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import SECRET_KEY
from .database import get_db
from .models import User

ALGORITHM = "HS256"
bearer_scheme = HTTPBearer(auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    """Dependency that yields a synchronous database session."""
    yield from get_db()


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode a JWT access token and return its payload."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_db_session),
) -> User:
    """Return the authenticated user from the Authorization header."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token_payload = decode_access_token(credentials.credentials)
    user_id = token_payload.get("sub")
    tenant_id: Optional[str] = token_payload.get("account_id") or token_payload.get(
        "company_id"
    )

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    query = session.query(User).filter(User.id == int(user_id))
    if tenant_id is not None:
        if hasattr(User, "account_id"):
            query = query.filter(User.account_id == tenant_id)
        elif hasattr(User, "company_id"):
            query = query.filter(User.company_id == tenant_id)

    user = query.first()
    if user is None or not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or missing user",
        )

    return user


def require_same_tenant(user: User, account_id: str) -> None:
    """Raise if the requested tenant does not match the authenticated user."""
    user_account = getattr(user, "account_id", None) or getattr(user, "company_id", None)
    if user_account != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch",
        )


def require_admin(user: User) -> None:
    """Ensure the current user has the admin role."""

    if getattr(user, "role", "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required",
        )


def token_payload(user: User) -> dict[str, Any]:
    """
    Generate the JWT payload for a given user.

    auth.login() will add "exp" on top of this.
    """
    return {
        "username": getattr(user, "username", ""),
        "account_id": getattr(user, "account_id", None)
        or getattr(user, "company_id", None),
        "iat": int(datetime.utcnow().timestamp()),
    }
