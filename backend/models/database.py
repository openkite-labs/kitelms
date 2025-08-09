from enum import Enum

from sqlmodel import Field

from backend.utils.models import BaseModel


class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(BaseModel, table=True):
    name: str
    email: str = Field(unique=True)
    password: str
    role: RoleEnum = Field(default=RoleEnum.USER)


class AppSettings(BaseModel, table=True):
    has_admin: bool = Field(default=False)
    enable_signup: bool = Field(default=False)