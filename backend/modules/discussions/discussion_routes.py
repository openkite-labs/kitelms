from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.models.engine import db_session
from backend.modules.auth.auth_methods import get_current_user
from backend.modules.discussions.discussion_methods import (
    create_discussion,
    delete_discussion,
    discussion_to_response,
    get_discussion_by_id,
    get_discussions,
    update_discussion,
)
from backend.modules.discussions.discussion_schema import (
    DiscussionCreate,
    DiscussionListResponse,
    DiscussionResponse,
    DiscussionUpdate,
)

discussion_router = APIRouter(prefix="/discussions", tags=["discussions"])


@discussion_router.post("/", response_model=DiscussionResponse)
def create_discussion_endpoint(
    discussion_data: DiscussionCreate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new discussion. Lesson ID should be provided in the request body.
    """
    try:
        discussion = create_discussion(session, discussion_data, current_user)
        return discussion_to_response(discussion)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@discussion_router.get("/", response_model=DiscussionListResponse)
def get_discussions_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    lesson_id: Optional[str] = Query(None),
    include_user_info: bool = Query(False),
    session: Session = Depends(db_session)
):
    """
    Get discussions with optional filtering by lesson_id.
    """
    try:
        discussions, total = get_discussions(session, skip, limit, lesson_id, include_user_info)
        return DiscussionListResponse(
            discussions=[discussion_to_response(d, include_user_info) for d in discussions],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@discussion_router.get("/{discussion_id}", response_model=DiscussionResponse)
def get_discussion(
    discussion_id: str,
    include_user_info: bool = Query(False),
    session: Session = Depends(db_session)
):
    """
    Get a specific discussion by ID.
    """
    discussion = get_discussion_by_id(session, discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return discussion_to_response(discussion, include_user_info)


@discussion_router.put("/{discussion_id}", response_model=DiscussionResponse)
def update_discussion_endpoint(
    discussion_id: str,
    discussion_data: DiscussionUpdate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Update a discussion. Only the author can update their discussion.
    """
    try:
        discussion = update_discussion(session, discussion_id, discussion_data, current_user)
        if not discussion:
            raise HTTPException(status_code=404, detail="Discussion not found")
        return discussion_to_response(discussion)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@discussion_router.delete("/{discussion_id}")
def delete_discussion_endpoint(
    discussion_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Delete a discussion. Only the author can delete their discussion.
    """
    try:
        success = delete_discussion(session, discussion_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Discussion not found")
        return {"message": "Discussion deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
