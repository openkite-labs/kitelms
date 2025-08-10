from typing import List, Optional

from pydantic import BaseModel

from backend.modules.lessons.lesson_schema import LessonResponse


class SectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    order: int
    course_id: str


class SectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class SectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    order: int
    course_id: str
    created_at: str
    updated_at: str


class SectionWithLessonsResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    order: int
    course_id: str
    created_at: str
    updated_at: str
    lessons: List[LessonResponse]


class SectionListResponse(BaseModel):
    sections: List[SectionResponse]
    total: int
    skip: int
    limit: int


class SectionOrderItem(BaseModel):
    id: str
    order: int


class SectionReorderRequest(BaseModel):
    course_id: str
    section_orders: List[SectionOrderItem]


# Update forward reference
SectionWithLessonsResponse.model_rebuild()
