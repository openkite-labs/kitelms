from typing import List, Optional

from pydantic import BaseModel


class LessonCreate(BaseModel):
    title: str
    content: Optional[str] = None
    video_url: Optional[str] = None
    order: int
    section_id: str


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    order: Optional[int] = None


class LessonResponse(BaseModel):
    id: str
    title: str
    content: Optional[str]
    video_url: Optional[str]
    order: int
    section_id: str
    created_at: str
    updated_at: str


class LessonListResponse(BaseModel):
    lessons: List[LessonResponse]
    total: int
    skip: int
    limit: int


class LessonOrderItem(BaseModel):
    id: str
    order: int


class LessonReorderRequest(BaseModel):
    section_id: str
    lesson_orders: List[LessonOrderItem]
