from typing import List

from backend.utils.engine import db_session
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.modules.auth.auth_methods import get_current_user
from backend.modules.sections.section_methods import (
    create_section,
    delete_section,
    get_section_by_id,
    get_sections_by_course,
    reorder_sections,
    section_to_response,
    section_with_lessons_to_response,
    update_section,
)
from backend.modules.sections.section_schema import (
    SectionCreate,
    SectionListResponse,
    SectionResponse,
    SectionUpdate,
    SectionWithLessonsResponse,
)

section_router = APIRouter(prefix="/sections", tags=["sections"])


@section_router.post("/course/{course_id}", response_model=SectionResponse)
def create_section_endpoint(
    course_id: str,
    section_data: SectionCreate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new section for a specific course.
    """
    try:
        section = create_section(session, section_data, course_id, current_user)
        return section_to_response(section)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@section_router.get("/course/{course_id}", response_model=SectionListResponse)
def get_course_sections(
    course_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(db_session)
):
    """
    Get all sections for a specific course.
    """
    try:
        sections, total = get_sections_by_course(session, course_id, skip, limit)
        return SectionListResponse(
            sections=[section_to_response(section) for section in sections],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@section_router.get("/course/{course_id}/with-lessons", response_model=List[SectionWithLessonsResponse])
def get_course_sections_with_lessons(
    course_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(db_session)
):
    """
    Get all sections for a specific course with their lessons.
    """
    try:
        sections, _ = get_sections_by_course(session, course_id, skip, limit)
        return [section_with_lessons_to_response(section) for section in sections]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@section_router.get("/{section_id}", response_model=SectionResponse)
def get_section(
    section_id: str,
    session: Session = Depends(db_session)
):
    """
    Get a specific section by ID.
    """
    section = get_section_by_id(session, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section_to_response(section)


@section_router.get("/{section_id}/with-lessons", response_model=SectionWithLessonsResponse)
def get_section_with_lessons(
    section_id: str,
    session: Session = Depends(db_session)
):
    """
    Get a specific section by ID with its lessons.
    """
    section = get_section_by_id(session, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section_with_lessons_to_response(section)


@section_router.put("/{section_id}", response_model=SectionResponse)
def update_section_endpoint(
    section_id: str,
    section_data: SectionUpdate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Update a specific section.
    """
    try:
        section = update_section(session, section_id, section_data, current_user)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        return section_to_response(section)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@section_router.delete("/{section_id}")
def delete_section_endpoint(
    section_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Delete a specific section.
    """
    try:
        success = delete_section(session, section_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Section not found")
        return {"message": "Section deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@section_router.put("/course/{course_id}/reorder")
def reorder_course_sections(
    course_id: str,
    section_orders: List[dict],
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Reorder sections within a course.
    Expects a list of {"id": "section_id", "order": new_order}
    """
    try:
        success = reorder_sections(session, course_id, section_orders, current_user)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to reorder sections")
        return {"message": "Sections reordered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
