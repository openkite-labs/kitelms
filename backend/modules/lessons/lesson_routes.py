from typing import Optional

from backend.models.engine import db_session
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.modules.auth.auth_methods import get_current_user
from backend.modules.lessons.lesson_methods import (
    create_lesson,
    delete_lesson,
    get_lesson_by_id,
    get_lessons,
    lesson_to_response,
    reorder_lessons,
    update_lesson,
)
from backend.modules.lessons.lesson_schema import (
    LessonCreate,
    LessonListResponse,
    LessonReorderRequest,
    LessonResponse,
    LessonUpdate,
)

lesson_router = APIRouter(prefix="/lessons", tags=["lessons"])


@lesson_router.post("/", response_model=LessonResponse)
def create_lesson_endpoint(
    lesson_data: LessonCreate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new lesson. Section ID should be provided in the request body.
    """
    try:
        lesson = create_lesson(session, lesson_data, current_user)
        return lesson_to_response(lesson)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@lesson_router.get("/", response_model=LessonListResponse)
def get_lessons_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    section_id: Optional[str] = Query(None),
    session: Session = Depends(db_session)
):
    """
    Get lessons with optional filtering by section_id.
    """
    try:
        lessons, total = get_lessons(session, skip, limit, section_id)
        return LessonListResponse(
            lessons=[lesson_to_response(lesson) for lesson in lessons],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@lesson_router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: str,
    session: Session = Depends(db_session)
):
    """
    Get a specific lesson by ID.
    """
    lesson = get_lesson_by_id(session, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson_to_response(lesson)


@lesson_router.put("/{lesson_id}", response_model=LessonResponse)
def update_lesson_endpoint(
    lesson_id: str,
    lesson_data: LessonUpdate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Update a specific lesson.
    """
    try:
        lesson = update_lesson(session, lesson_id, lesson_data, current_user)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson_to_response(lesson)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@lesson_router.delete("/{lesson_id}")
def delete_lesson_endpoint(
    lesson_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Delete a specific lesson.
    """
    try:
        success = delete_lesson(session, lesson_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return {"message": "Lesson deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@lesson_router.put("/reorder")
def reorder_lessons_endpoint(
    reorder_data: LessonReorderRequest,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Reorder lessons within a section.
    Expects {"section_id": "section_id", "lesson_orders": [{"id": "lesson_id", "order": new_order}]}
    """
    try:
        # Convert Pydantic models to dict for the reorder_lessons function
        lesson_orders_dict = [item.dict() for item in reorder_data.lesson_orders]

        success = reorder_lessons(session, reorder_data.section_id, lesson_orders_dict, current_user)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to reorder lessons")
        return {"message": "Lessons reordered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
