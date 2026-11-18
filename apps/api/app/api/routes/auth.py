from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.rate_limiter import limit_login
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def set_auth_cookie(response: Response, token: str) -> None:
    """Sets secure HttpOnly cookie for browser sessions."""
    max_age = settings.access_token_expire_minutes * 60
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=max_age,
        expires=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Clears authentication cookie on logout."""
    response.delete_cookie(
        key=settings.cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    response: Response,
    db: Session = Depends(get_db),
) -> Token:
    """Registers a new user with hashed password and returns an authenticated session."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    db_user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip(),
        password_hash=hash_password(user_in.password),
        role="user",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    token = create_access_token(
        subject=str(db_user.id),
        claims={"email": db_user.email, "role": db_user.role},
    )
    set_auth_cookie(response, token)

    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(db_user),
    )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
    _limit: None = Depends(limit_login),
) -> Token:
    """Authenticates a user and issues a JWT session token."""
    user = db.query(User).filter(User.email == credentials.email.lower().strip()).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        subject=str(user.id),
        claims={"email": user.email, "role": user.role},
    )
    set_auth_cookie(response, token)

    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Logs out user by clearing the authentication cookie."""
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_auth_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Returns the currently authenticated user."""
    return UserResponse.model_validate(current_user)
