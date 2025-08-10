from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, func, select

from backend.models.database import Discussion, Lesson
from backend.modules.discussions.discussion_schema import DiscussionCreate, DiscussionResponse, DiscussionUpdate


# Helper function
def discussion_to_response(discussion, include_user_info: bool = False) -> DiscussionResponse:
    """Convert Discussion model to DiscussionResponse schema."""
    response_data = {
        "id": discussion.id,
        "content": discussion.content,
        "lesson_id": discussion.lesson_id,
        "user_id": discussion.user_id,
        "created_at": discussion.created_at.isoformat(),
        "updated_at": discussion.updated_at.isoformat(),
    }

    if include_user_info and hasattr(discussion, "user") and discussion.user:
        response_data["user_name"] = discussion.user.name
        response_data["user_email"] = discussion.user.email

    return DiscussionResponse(**response_data)


# Discussion CRUD operations
def create_discussion(session: Session, discussion_data: DiscussionCreate, user_id: str) -> Discussion:
    """
    Create a new discussion for a specific lesson.
    """
    # Check if lesson exists
    lesson_statement = select(Lesson).where(Lesson.id == discussion_data.lesson_id, Lesson.is_deleted == False)
    lesson = session.exec(lesson_statement).first()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    discussion = Discussion(content=discussion_data.content, lesson_id=discussion_data.lesson_id, user_id=user_id)

    session.add(discussion)
    session.commit()
    session.refresh(discussion)
    return discussion


def get_discussion_by_id(session: Session, discussion_id: str) -> Optional[Discussion]:
    """
    Get a discussion by its ID.
    """
    statement = select(Discussion).where(Discussion.id == discussion_id, Discussion.is_deleted == False)
    return session.exec(statement).first()


def get_discussions(
    session: Session, skip: int = 0, limit: int = 10, lesson_id: Optional[str] = None, include_user_info: bool = False
) -> tuple[list[Discussion], int]:
    """
    Get discussions with optional filtering by lesson_id.
    """
    statement = select(Discussion).where(Discussion.is_deleted == False)

    if lesson_id:
        statement = statement.where(Discussion.lesson_id == lesson_id)

    # Get total count
    count_statement = select(func.count(Discussion.id)).where(Discussion.is_deleted == False)
    if lesson_id:
        count_statement = count_statement.where(Discussion.lesson_id == lesson_id)

    total = session.exec(count_statement).one()

    # Get discussions with pagination
    statement = statement.order_by(Discussion.created_at.desc()).offset(skip).limit(limit)
    discussions = session.exec(statement).all()

    return discussions, total


def get_discussions_by_lesson(
    session: Session, lesson_id: str, skip: int = 0, limit: int = 10
) -> tuple[list[Discussion], int]:
    """
    Get discussions for a specific lesson.
    """
    return get_discussions(session, skip, limit, lesson_id, False)


def update_discussion(
    session: Session, discussion_id: str, discussion_data: DiscussionUpdate, user_id: str
) -> Optional[Discussion]:
    """
    Update a discussion. Only the author can update their discussion.
    """
    statement = select(Discussion).where(Discussion.id == discussion_id, Discussion.is_deleted == False)
    discussion = session.exec(statement).first()

    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    # Check if user is the author of the discussion
    if discussion.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this discussion")

    # Update fields
    if discussion_data.content is not None:
        discussion.content = discussion_data.content

    discussion.updated_at = datetime.utcnow()
    session.add(discussion)
    session.commit()
    session.refresh(discussion)
    return discussion


def delete_discussion(session: Session, discussion_id: str, user_id: str) -> bool:
    """
    Delete a discussion (soft delete). Only the author can delete their discussion.
    """
    statement = select(Discussion).where(Discussion.id == discussion_id, Discussion.is_deleted == False)
    discussion = session.exec(statement).first()

    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")

    # Check if user is the author of the discussion
    if discussion.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this discussion")

    # Soft delete
    discussion.is_deleted = True
    discussion.updated_at = datetime.utcnow()
    session.add(discussion)
    session.commit()
    return True
