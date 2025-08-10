from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, func, select

from backend.models.database import Course, Lesson, Section
from backend.modules.lessons.lesson_schema import LessonCreate, LessonResponse, LessonUpdate


# Helper function
def lesson_to_response(lesson) -> LessonResponse:
    """Convert Lesson model to LessonResponse schema."""
    return LessonResponse(
        id=lesson.id,
        title=lesson.title,
        content=lesson.content,
        video_url=lesson.video_url,
        order=lesson.order,
        section_id=lesson.section_id,
        created_at=lesson.created_at.isoformat(),
        updated_at=lesson.updated_at.isoformat(),
    )


# Lesson CRUD operations
def create_lesson(session: Session, lesson_data: LessonCreate, user_id: str) -> Lesson:
    """
    Create a new lesson for a specific section.
    """
    # Check if user owns the course through section
    section_statement = select(Section).where(Section.id == lesson_data.section_id, Section.is_deleted == False)
    section = session.exec(section_statement).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    course_statement = select(Course).where(Course.id == section.course_id)
    course = session.exec(course_statement).first()

    if not course or course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to add lessons to this section")

    lesson = Lesson(
        title=lesson_data.title,
        content=lesson_data.content,
        video_url=lesson_data.video_url,
        order=lesson_data.order,
        section_id=lesson_data.section_id,
    )

    session.add(lesson)
    session.commit()
    session.refresh(lesson)
    return lesson


def get_lesson_by_id(session: Session, lesson_id: str) -> Optional[Lesson]:
    """
    Get a lesson by its ID.
    """
    statement = select(Lesson).where(Lesson.id == lesson_id, Lesson.is_deleted == False)
    return session.exec(statement).first()


def get_lessons(
    session: Session, skip: int = 0, limit: int = 10, section_id: Optional[str] = None
) -> tuple[list[Lesson], int]:
    """
    Get lessons with optional filtering by section_id.
    """
    statement = select(Lesson).where(Lesson.is_deleted == False)
    count_statement = select(func.count(Lesson.id)).where(Lesson.is_deleted == False)

    # Apply section filter if provided
    if section_id:
        statement = statement.where(Lesson.section_id == section_id)
        count_statement = count_statement.where(Lesson.section_id == section_id)

    statement = statement.order_by(Lesson.order).offset(skip).limit(limit)

    lessons = session.exec(statement).all()
    total = session.exec(count_statement).one()

    return lessons, total


def get_lessons_by_section(
    session: Session, section_id: str, skip: int = 0, limit: int = 10
) -> tuple[list[Lesson], int]:
    """
    Get all lessons for a specific section.
    Deprecated: Use get_lessons with section_id parameter instead.
    """
    return get_lessons(session, skip, limit, section_id)


def update_lesson(session: Session, lesson_id: str, lesson_data: LessonUpdate, user_id: str) -> Optional[Lesson]:
    """
    Update a lesson. Only the course owner can update it.
    """
    lesson = get_lesson_by_id(session, lesson_id)

    if not lesson:
        return None

    # Check if user owns the course through section
    section_statement = select(Section).where(Section.id == lesson.section_id)
    section = session.exec(section_statement).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    course_statement = select(Course).where(Course.id == section.course_id)
    course = session.exec(course_statement).first()

    if not course or course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this lesson")

    # Update only provided fields
    update_data = lesson_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(lesson, field, value)

    lesson.updated_at = datetime.now()

    session.add(lesson)
    session.commit()
    session.refresh(lesson)
    return lesson


def delete_lesson(session: Session, lesson_id: str, user_id: str) -> bool:
    """
    Soft delete a lesson. Only the course owner can delete it.
    """
    lesson = get_lesson_by_id(session, lesson_id)

    if not lesson:
        return False

    # Check if user owns the course through section
    section_statement = select(Section).where(Section.id == lesson.section_id)
    section = session.exec(section_statement).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    course_statement = select(Course).where(Course.id == section.course_id)
    course = session.exec(course_statement).first()

    if not course or course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this lesson")

    lesson.is_deleted = True
    lesson.updated_at = datetime.now()

    session.add(lesson)
    session.commit()
    return True


def reorder_lessons(session: Session, section_id: str, lesson_orders: list[dict], user_id: str) -> bool:
    """
    Reorder lessons within a section.
    lesson_orders should be a list of {"id": "lesson_id", "order": new_order}
    """
    # Check if user owns the course through section
    section_statement = select(Section).where(Section.id == section_id, Section.is_deleted == False)
    section = session.exec(section_statement).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    course_statement = select(Course).where(Course.id == section.course_id)
    course = session.exec(course_statement).first()

    if not course or course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to reorder lessons in this section")

    for lesson_order in lesson_orders:
        lesson_statement = select(Lesson).where(
            Lesson.id == lesson_order["id"], Lesson.section_id == section_id, Lesson.is_deleted == False
        )
        lesson = session.exec(lesson_statement).first()

        if lesson:
            lesson.order = lesson_order["order"]
            lesson.updated_at = datetime.now()
            session.add(lesson)

    session.commit()
    return True
