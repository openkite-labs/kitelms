from typing import Optional

from pydantic import BaseModel

from backend.models.database import RoleEnum


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[RoleEnum] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: RoleEnum
    created_at: str
    updated_at: str
    is_deleted: bool


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    per_page: int


class UserBanRequest(BaseModel):
    reason: Optional[str] = None
