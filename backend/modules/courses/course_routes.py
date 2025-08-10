from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.models.engine import db_session
from backend.modules.auth.auth_methods import get_current_user
from backend.modules.courses.course_methods import (
    course_to_response,
    create_course,
    delete_course,
    get_course_by_id,
    get_courses,
    toggle_course_publication,
    update_course,
)
from backend.modules.courses.course_schema import CourseCreate, CourseListResponse, CourseResponse, CourseUpdate

course_router = APIRouter(prefix="/courses", tags=["courses"])


@course_router.post("/", response_model=CourseResponse)
async def create_new_course(
    course_data: CourseCreate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Create a new course."""
    try:
        course = create_course(session, course_data, current_user)
        return course_to_response(course)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@course_router.get("/", response_model=CourseListResponse)
async def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    my_courses: bool = Query(False),
    session: Session = Depends(db_session),
    current_user: Optional[str] = Depends(get_current_user)
):
    """Get a list of courses with optional filtering, search, and my_courses functionality."""
    # If my_courses is True, filter by current user
    filter_user_id = current_user if my_courses else user_id

    courses, total = get_courses(
        session,
        skip=skip,
        limit=limit,
        user_id=filter_user_id,
        is_published=is_published,
        category=category,
        search_query=search
    )

    course_responses = [course_to_response(course) for course in courses]

    return CourseListResponse(
        courses=course_responses,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@course_router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    session: Session = Depends(db_session)
):
    """Get a specific course by ID."""
    course = get_course_by_id(session, course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course_to_response(course)


@course_router.put("/{course_id}", response_model=CourseResponse)
async def update_course_endpoint(
    course_id: str,
    course_data: CourseUpdate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Update a course. Only the course owner can update it."""
    try:
        course = update_course(session, course_id, course_data, current_user)

        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        return course_to_response(course)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@course_router.delete("/{course_id}")
async def delete_course_endpoint(
    course_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Delete a course. Only the course owner can delete it."""
    try:
        success = delete_course(session, course_id, current_user)

        if not success:
            raise HTTPException(status_code=404, detail="Course not found")

        return {"message": "Course deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@course_router.patch("/{course_id}/toggle-publication", response_model=CourseResponse)
async def toggle_course_publication_endpoint(
    course_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Toggle the publication status of a course."""
    try:
        course = toggle_course_publication(session, course_id, current_user)

        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        return course_to_response(course)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
