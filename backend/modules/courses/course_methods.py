from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, func, select

from backend.models.database import Course
from backend.modules.courses.course_schema import CourseCreate, CourseResponse, CourseUpdate


def course_to_response(course) -> CourseResponse:
    """Convert Course model to CourseResponse schema."""
    return CourseResponse(
        id=course.id,
        name=course.name,
        description=course.description,
        cover_image_url=course.cover_image_url,
        video_preview_url=course.video_preview_url,
        price=course.price,
        category=course.category,
        tags=course.tags,
        is_published=course.is_published,
        user_id=course.user_id,
        created_at=course.created_at.isoformat(),
        updated_at=course.updated_at.isoformat()
    )


def create_course(session: Session, course_data: CourseCreate, user_id: str) -> Course:
    """
    Create a new course for a specific user.
    """
    course = Course(
        name=course_data.name,
        description=course_data.description,
        cover_image_url=course_data.cover_image_url,
        video_preview_url=course_data.video_preview_url,
        price=course_data.price,
        category=course_data.category,
        tags=course_data.tags,
        is_published=course_data.is_published,
        user_id=user_id
    )

    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def get_course_by_id(session: Session, course_id: str) -> Optional[Course]:
    """
    Get a course by its ID.
    """
    statement = select(Course).where(
        Course.id == course_id,
        Course.is_deleted == False
    )
    return session.exec(statement).first()


def get_courses(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    user_id: Optional[str] = None,
    is_published: Optional[bool] = None,
    category: Optional[str] = None,
    search_query: Optional[str] = None
) -> tuple[list[Course], int]:
    """
    Get a list of courses with optional filtering, search, and pagination.
    Returns tuple of (courses, total_count).
    """
    statement = select(Course).where(Course.is_deleted == False)
    count_statement = select(func.count(Course.id)).where(Course.is_deleted == False)

    # Apply filters
    if user_id:
        statement = statement.where(Course.user_id == user_id)
        count_statement = count_statement.where(Course.user_id == user_id)

    if is_published is not None:
        statement = statement.where(Course.is_published == is_published)
        count_statement = count_statement.where(Course.is_published == is_published)

    if category:
        statement = statement.where(Course.category == category)
        count_statement = count_statement.where(Course.category == category)

    # Apply search filter
    if search_query:
        search_pattern = f"%{search_query}%"
        search_condition = (
            Course.name.ilike(search_pattern) |
            Course.description.ilike(search_pattern) |
            Course.tags.ilike(search_pattern)
        )
        statement = statement.where(search_condition)
        count_statement = count_statement.where(search_condition)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)

    courses = session.exec(statement).all()
    total = session.exec(count_statement).one()

    return courses, total


def update_course(
    session: Session,
    course_id: str,
    course_data: CourseUpdate,
    user_id: str
) -> Optional[Course]:
    """
    Update a course. Only the course owner can update it.
    """
    course = get_course_by_id(session, course_id)

    if not course:
        return None

    # Check if user owns the course
    if course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this course")

    # Update only provided fields
    update_data = course_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(course, field, value)

    course.updated_at = datetime.now()

    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def delete_course(session: Session, course_id: str, user_id: str) -> bool:
    """
    Soft delete a course. Only the course owner can delete it.
    """
    course = get_course_by_id(session, course_id)

    if not course:
        return False

    # Check if user owns the course
    if course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this course")

    course.is_deleted = True
    course.updated_at = datetime.now()

    session.add(course)
    session.commit()
    return True


def get_user_courses(session: Session, user_id: str, skip: int = 0, limit: int = 10) -> tuple[list[Course], int]:
    """
    Get all courses created by a specific user.
    """
    return get_courses(session, skip=skip, limit=limit, user_id=user_id)


def get_published_courses(session: Session, skip: int = 0, limit: int = 10) -> tuple[list[Course], int]:
    """
    Get all published courses.
    """
    return get_courses(session, skip=skip, limit=limit, is_published=True)


def search_courses(
    session: Session,
    query: str,
    skip: int = 0,
    limit: int = 10
) -> tuple[list[Course], int]:
    """
    Search courses by name, description, or tags.
    """
    search_pattern = f"%{query}%"

    statement = select(Course).where(
        Course.is_deleted == False,
        Course.is_published == True,
        (
            Course.name.ilike(search_pattern) |
            Course.description.ilike(search_pattern) |
            Course.tags.ilike(search_pattern)
        )
    ).offset(skip).limit(limit)

    count_statement = select(func.count(Course.id)).where(
        Course.is_deleted == False,
        Course.is_published == True,
        (
            Course.name.ilike(search_pattern) |
            Course.description.ilike(search_pattern) |
            Course.tags.ilike(search_pattern)
        )
    )

    courses = session.exec(statement).all()
    total = session.exec(count_statement).one()

    return courses, total


def toggle_course_publication(session: Session, course_id: str, user_id: str) -> Optional[Course]:
    """
    Toggle the publication status of a course.
    """
    course = get_course_by_id(session, course_id)

    if not course:
        return None

    # Check if user owns the course
    if course.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this course")

    course.is_published = not course.is_published
    course.updated_at = datetime.now()

    session.add(course)
    session.commit()
    session.refresh(course)
    return course
