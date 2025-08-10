from typing import Optional

from pydantic import BaseModel


class CourseCreate(BaseModel):
    name: str
    description: str
    cover_image_url: Optional[str] = ""
    video_preview_url: Optional[str] = ""
    price: Optional[float] = 0.0
    category: Optional[str] = ""
    tags: Optional[str] = ""
    is_published: Optional[bool] = False


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    video_preview_url: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    is_published: Optional[bool] = None


class CourseResponse(BaseModel):
    id: str
    name: str
    description: str
    cover_image_url: str
    video_preview_url: str
    price: float
    category: str
    tags: str
    is_published: bool
    user_id: str
    created_at: str
    updated_at: str


class CourseListResponse(BaseModel):
    courses: list[CourseResponse]
    total: int
    page: int
    per_page: int
