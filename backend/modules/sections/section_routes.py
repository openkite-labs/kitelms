from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.models.engine import db_session
from backend.modules.auth.auth_methods import get_current_user
from backend.modules.sections.section_methods import (
    create_section,
    delete_section,
    get_section_by_id,
    get_sections,
    reorder_sections,
    section_to_response,
    section_with_lessons_to_response,
    update_section,
)
from backend.modules.sections.section_schema import (
    SectionCreate,
    SectionListResponse,
    SectionReorderRequest,
    SectionResponse,
    SectionUpdate,
    SectionWithLessonsResponse,
)

section_router = APIRouter(prefix="/sections", tags=["sections"])


@section_router.post("/", response_model=SectionResponse)
def create_section_endpoint(
    section_data: SectionCreate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new section for a specific course.
    """
    try:
        section = create_section(session, section_data, current_user)
        return section_to_response(section)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@section_router.get("/", response_model=SectionListResponse)
def get_sections_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    course_id: Optional[str] = Query(None),
    session: Session = Depends(db_session)
):
    """
    Get sections with optional filtering by course_id.
    """
    try:
        sections, total = get_sections(session, skip, limit, course_id)
        return SectionListResponse(
            sections=[section_to_response(section) for section in sections],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@section_router.put("/reorder")
def reorder_sections_endpoint(
    reorder_data: SectionReorderRequest,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """
    Reorder sections within a course.
    Expects {"course_id": "course_id", "section_orders": [{"id": "section_id", "order": new_order}]}
    """
    try:
        # Convert Pydantic models to dict for the reorder_sections function
        section_orders_dict = [item.dict() for item in reorder_data.section_orders]

        success = reorder_sections(session, reorder_data.course_id, section_orders_dict, current_user)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to reorder sections")
        return {"message": "Sections reordered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
