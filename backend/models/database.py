from enum import Enum

from sqlmodel import Field, Relationship

from backend.utils.models import BaseModel


class RoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(BaseModel, table=True):
    name: str
    email: str = Field(unique=True)
    password: str
    role: RoleEnum = Field(default=RoleEnum.USER)

    courses: list["Course"] = Relationship(back_populates="user")


class AppSettings(BaseModel, table=True):
    has_admin: bool = Field(default=False)
    enable_signup: bool = Field(default=False)

    # Oauth Settings
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    google_redirect_uri: str = Field(default="")


class Course(BaseModel, table=True):
    name: str
    description: str
    cover_image_url: str = Field(default="")
    video_preview_url: str = Field(default="")
    price: float = Field(default=0.0)
    category: str = Field(default="")
    tags: str = Field(default="")

    is_published: bool = Field(default=False)

    user_id: str = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="courses")

    sections: list["Section"] = Relationship(back_populates="course")


class Section(BaseModel, table=True):
    name: str
    description: str
    order: int = Field(default=0)

    course_id: str = Field(foreign_key="course.id")
    course: Course = Relationship(back_populates="sections")

    lessons: list["Lesson"] = Relationship(back_populates="section")


class Lesson(BaseModel, table=True):
    title: str
    content: str
    video_url: str = Field(default="")
    order: int = Field(default=0)

    section_id: str = Field(foreign_key="section.id")
    section: Section = Relationship(back_populates="lessons")
