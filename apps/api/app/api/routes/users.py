from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.user import (
    UserChangePassword,
    UserPreferenceRead,
    UserPreferenceUpdate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Returns profile of currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Updates non-sensitive profile details (e.g. display name) for authenticated user."""
    current_user.name = body.name.strip()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_current_user_password(
    body: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Securely updates password after verifying current credentials."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed",
        )
    current_user.password_hash = hash_password(body.new_password)
    db.add(current_user)
    db.commit()
    return {"message": "Password changed successfully"}


@router.get("/me/preferences", response_model=UserPreferenceRead)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPreferenceRead:
    """Returns stored UI theme and appearance preferences for authenticated user."""
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not pref:
        # Create default preference if none exists
        pref = UserPreference(
            user_id=current_user.id,
            theme="signal-loom",
            avatar_preset="loom",
            color_mode="system",
            reduced_motion=False,
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return UserPreferenceRead.model_validate(pref)


@router.patch("/me/preferences", response_model=UserPreferenceRead)
async def update_user_preferences(
    body: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPreferenceRead:
    """Updates UI theme and appearance preferences for authenticated user."""
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not pref:
        pref = UserPreference(
            user_id=current_user.id,
            theme="signal-loom",
            avatar_preset="loom",
            color_mode="system",
            reduced_motion=False,
        )
        db.add(pref)

    if body.theme is not None:
        pref.theme = body.theme
    if body.avatar_preset is not None:
        pref.avatar_preset = body.avatar_preset
    if body.color_mode is not None:
        pref.color_mode = body.color_mode
    if body.reduced_motion is not None:
        pref.reduced_motion = body.reduced_motion

    db.commit()
    db.refresh(pref)
    return UserPreferenceRead.model_validate(pref)


