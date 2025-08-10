from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, func, select

from backend.models.database import Course, Section
from backend.modules.lessons.lesson_methods import lesson_to_response
from backend.modules.sections.section_schema import (
    SectionCreate,
    SectionResponse,
    SectionUpdate,
    SectionWithLessonsResponse,
)


# Helper functions
def section_to_response(section) -> SectionResponse:
    """Convert Section model to SectionResponse schema."""
    return SectionResponse(
        id=section.id,
        name=section.name,
        description=section.description,
        order=section.order,
        course_id=section.course_id,
        created_at=section.created_at.isoformat(),
        updated_at=section.updated_at.isoformat()
    )


def section_with_lessons_to_response(section) -> SectionWithLessonsResponse:
    """Convert Section model with lessons to SectionWithLessonsResponse schema."""
    return SectionWithLessonsResponse(
        id=section.id,
        name=section.name,
        description=section.description,
        order=section.order,
        course_id=section.course_id,
        created_at=section.created_at.isoformat(),
        updated_at=section.updated_at.isoformat(),
        lessons=[lesson_to_response(lesson) for lesson in section.lessons]
    )


# Section CRUD operations
def create_section(session: Session, section_data: SectionCreate, course_id: str, user_id: str) -> Section:
    """
    Create a new section for a specific course.
    """
    # Check if user owns the course
    course_statement = select(Course).where(
        Course.id == course_id,
        Course.is_deleted == False
    )
    course = session.exec(course_statement).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to add sections to this course")

    section = Section(
        name=section_data.name,
        description=section_data.description,
        order=section_data.order,
        course_id=course_id
    )

    session.add(section)
    session.commit()
    session.refresh(section)
    return section


def get_section_by_id(session: Session, section_id: str) -> Optional[Section]:
    """
    Get a section by its ID.
    """
    statement = select(Section).where(
        Section.id == section_id,
        Section.is_deleted == False
    )
    return session.exec(statement).first()


def get_sections_by_course(
    session: Session,
    course_id: str,
    skip: int = 0,
    limit: int = 10
) -> tuple[list[Section], int]:
    """
    Get all sections for a specific course.
    """
    statement = select(Section).where(
        Section.course_id == course_id,
        Section.is_deleted == False
    ).order_by(Section.order).offset(skip).limit(limit)

    count_statement = select(func.count(Section.id)).where(
        Section.course_id == course_id,
        Section.is_deleted == False
    )

    sections = session.exec(statement).all()
    total = session.exec(count_statement).one()

    return sections, total


def update_section(
    session: Session,
    section_id: str,
    section_data: SectionUpdate,
    user_id: str
) -> Optional[Section]:
    """
    Update a section. Only the course owner can update it.
    """
    section = get_section_by_id(session, section_id)

    if not section:
        return None

    # Check if user owns the course
    course_statement = select(Course).where(Course.id == section.course_id)
    course = session.exec(course_statement).first()

    if not course or course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this section")

    # Update only provided fields
    update_data = section_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(section, field, value)

    section.updated_at = datetime.now()

    session.add(section)
    session.commit()
    session.refresh(section)
    return section


def delete_section(session: Session, section_id: str, user_id: str) -> bool:
    """
    Soft delete a section. Only the course owner can delete it.
    """
    section = get_section_by_id(session, section_id)

    if not section:
        return False

    # Check if user owns the course
    course_statement = select(Course).where(Course.id == section.course_id)
    course = session.exec(course_statement).first()

    if not course or course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this section")

    section.is_deleted = True
    section.updated_at = datetime.now()

    session.add(section)
    session.commit()
    return True


def reorder_sections(session: Session, course_id: str, section_orders: list[dict], user_id: str) -> bool:
    """
    Reorder sections within a course.
    section_orders should be a list of {"id": "section_id", "order": new_order}
    """
    # Check if user owns the course
    course_statement = select(Course).where(
        Course.id == course_id,
        Course.is_deleted == False
    )
    course = session.exec(course_statement).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to reorder sections in this course")

    for section_order in section_orders:
        section_statement = select(Section).where(
            Section.id == section_order["id"],
            Section.course_id == course_id,
            Section.is_deleted == False
        )
        section = session.exec(section_statement).first()

        if section:
            section.order = section_order["order"]
            section.updated_at = datetime.now()
            session.add(section)

    session.commit()
    return True
