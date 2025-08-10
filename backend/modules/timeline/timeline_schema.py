from typing import List, Optional

from pydantic import BaseModel


class PostCreate(BaseModel):
    content: str
    image_url: Optional[str] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None


class CommentCreate(BaseModel):
    content: str
    post_id: str


class CommentUpdate(BaseModel):
    content: Optional[str] = None


class CommentResponse(BaseModel):
    id: str
    content: str
    post_id: str
    user_id: str
    created_at: str
    updated_at: str

    # Optional user info for display
    user_name: Optional[str] = None
    user_email: Optional[str] = None


class PostResponse(BaseModel):
    id: str
    content: str
    image_url: str
    user_id: str
    created_at: str
    updated_at: str

    # Optional user info for display
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    # Optional comments
    comments: Optional[List[CommentResponse]] = None
    comments_count: Optional[int] = None


class PostListResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    skip: int
    limit: int


class CommentListResponse(BaseModel):
    comments: List[CommentResponse]
    total: int
    skip: int
    limit: int
