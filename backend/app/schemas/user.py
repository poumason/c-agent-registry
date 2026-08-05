import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import UserRole, UserStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: UserRole = UserRole.member
    status: UserStatus = UserStatus.active


class UserUpdate(BaseModel):
    name: str | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    password: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
