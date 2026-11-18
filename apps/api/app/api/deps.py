from typing import Generator, Optional
import uuid
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.schemas.token import TokenPayload

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts and authenticates user from either:
    1. HttpOnly access_token cookie (preferred for browser clients)
    2. Authorization: Bearer <token> header (for API / external clients)
    """
    token: Optional[str] = None

    # Check HttpOnly cookie first
    cookie_token = request.cookies.get(settings.cookie_name)
    if cookie_token:
        token = cookie_token
        # CSRF mitigation for cookie-authenticated state-mutations
        if not (bearer and bearer.credentials) and settings.environment != "testing":
            if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                content_type = request.headers.get("content-type", "")
                x_requested = request.headers.get("x-requested-with", "")
                origin = request.headers.get("origin", "")

                is_valid_csrf = (
                    "application/json" in content_type
                    or "multipart/form-data" in content_type
                    or x_requested.lower() == "xmlhttprequest"
                    or (origin and origin in settings.cors_origins)
                )
                if not is_valid_csrf:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="CSRF protection: request missing valid origin or JSON content type.",
                    )
    elif bearer and bearer.credentials:
        token = bearer.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token)
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = uuid.UUID(token_data.sub)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
