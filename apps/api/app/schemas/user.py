from datetime import datetime
import re
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, description="Full name of user")
    email: str = Field(..., min_length=5, max_length=255, description="Unique email address")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean_email = v.strip().lower()
        if not EMAIL_REGEX.match(clean_email):
            raise ValueError("Invalid email address format")
        return clean_email


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Password (at least 8 characters)")


class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean_email = v.strip().lower()
        if not EMAIL_REGEX.match(clean_email):
            raise ValueError("Invalid email address format")
        return clean_email


class UserUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, description="Full name or display name")


class UserChangePassword(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password (at least 8 characters)")


class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


ALLOWED_THEMES = {"signal-loom", "daybreak", "nebula", "oceanic"}
ALLOWED_AVATARS = {"loom", "aqua", "amber", "violet", "emerald", "slate"}
ALLOWED_COLOR_MODES = {"system", "dark", "light"}


class UserPreferenceRead(BaseModel):
    theme: str = Field(default="signal-loom", description="Website theme identifier")
    avatar_preset: str = Field(default="loom", description="Avatar preset identifier")
    color_mode: str = Field(default="system", description="Color mode: system, dark, light")
    reduced_motion: bool = Field(default=False, description="Whether reduced motion is preferred")
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserPreferenceUpdate(BaseModel):
    theme: str | None = Field(None, description="Website theme: signal-loom, daybreak, nebula, oceanic")
    avatar_preset: str | None = Field(None, description="Avatar preset: loom, aqua, amber, violet, emerald, slate")
    color_mode: str | None = Field(None, description="Color mode: system, dark, light")
    reduced_motion: bool | None = Field(None, description="Reduced motion preference")

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str | None) -> str | None:
        if v is not None:
            clean = v.strip().lower()
            if clean not in ALLOWED_THEMES:
                raise ValueError(f"Theme must be one of: {', '.join(sorted(ALLOWED_THEMES))}")
            return clean
        return v

    @field_validator("avatar_preset")
    @classmethod
    def validate_avatar(cls, v: str | None) -> str | None:
        if v is not None:
            clean = v.strip().lower()
            if clean not in ALLOWED_AVATARS:
                raise ValueError(f"Avatar preset must be one of: {', '.join(sorted(ALLOWED_AVATARS))}")
            return clean
        return v

    @field_validator("color_mode")
    @classmethod
    def validate_color_mode(cls, v: str | None) -> str | None:
        if v is not None:
            clean = v.strip().lower()
            if clean not in ALLOWED_COLOR_MODES:
                raise ValueError(f"Color mode must be one of: {', '.join(sorted(ALLOWED_COLOR_MODES))}")
            return clean
        return v

