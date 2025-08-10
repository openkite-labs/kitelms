from typing import List, Optional

from pydantic import BaseModel


class DiscussionCreate(BaseModel):
    content: str
    lesson_id: str


class DiscussionUpdate(BaseModel):
    content: Optional[str] = None


class DiscussionResponse(BaseModel):
    id: str
    content: str
    lesson_id: str
    user_id: str
    created_at: str
    updated_at: str

    # Optional user info for display
    user_name: Optional[str] = None
    user_email: Optional[str] = None


class DiscussionListResponse(BaseModel):
    discussions: List[DiscussionResponse]
    total: int
    skip: int
    limit: int
