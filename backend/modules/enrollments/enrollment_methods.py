from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from backend.models.database import Billing, BillingStatus, Course, Enrollment
from backend.modules.enrollments.enrollment_schema import (
    BillingCreate,
    BillingResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    PurchaseCourseRequest,
)


def billing_to_response(billing: Billing) -> BillingResponse:
    """Convert Billing model to BillingResponse."""
    return BillingResponse(
        id=billing.id,
        user_id=billing.user_id,
        course_id=billing.course_id,
        amount=billing.amount,
        status=billing.status,
        payment_method=billing.payment_method,
        transaction_id=billing.transaction_id,
        created_at=billing.created_at.isoformat(),
        updated_at=billing.updated_at.isoformat(),
    )


def enrollment_to_response(enrollment: Enrollment) -> EnrollmentResponse:
    """Convert Enrollment model to EnrollmentResponse."""
    return EnrollmentResponse(
        id=enrollment.id,
        user_id=enrollment.user_id,
        course_id=enrollment.course_id,
        billing_id=enrollment.billing_id,
        created_at=enrollment.created_at.isoformat(),
        updated_at=enrollment.updated_at.isoformat(),
        billing=billing_to_response(enrollment.billing),
    )


def create_billing(session: Session, billing_data: BillingCreate, user_id: str) -> Billing:
    """Create a new billing record."""
    # Get course to validate and get price
    course = session.get(Course, billing_data.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if not course.is_published:
        raise HTTPException(status_code=400, detail="Course is not published")

    # Check if user already has a paid billing for this course
    existing_billing = session.exec(
        select(Billing).where(
            Billing.user_id == user_id,
            Billing.course_id == billing_data.course_id,
            Billing.status == BillingStatus.PAID,
        )
    ).first()

    if existing_billing:
        raise HTTPException(status_code=400, detail="Course already purchased")

    billing = Billing(
        user_id=user_id,
        course_id=billing_data.course_id,
        amount=course.price,
        payment_method=billing_data.payment_method,
        transaction_id=billing_data.transaction_id,
        status=BillingStatus.PENDING,
    )

    session.add(billing)
    session.commit()
    session.refresh(billing)

    return billing


def update_billing_status(session: Session, billing_id: str, status: BillingStatus) -> Billing:
    """Update billing status."""
    billing = session.get(Billing, billing_id)
    if not billing:
        raise HTTPException(status_code=404, detail="Billing record not found")

    billing.status = status
    billing.updated_at = datetime.now()

    session.add(billing)
    session.commit()
    session.refresh(billing)

    return billing


def create_enrollment(session: Session, enrollment_data: EnrollmentCreate, user_id: str) -> Enrollment:
    """Create a new enrollment after payment verification."""
    # Verify billing exists and is paid
    billing = session.get(Billing, enrollment_data.billing_id)
    if not billing:
        raise HTTPException(status_code=404, detail="Billing record not found")

    if billing.user_id != user_id:
        raise HTTPException(status_code=403, detail="Billing record does not belong to user")

    if billing.status != BillingStatus.PAID:
        raise HTTPException(status_code=400, detail="Payment not completed")

    # Check if enrollment already exists
    existing_enrollment = session.exec(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == enrollment_data.course_id,
            Enrollment.billing_id == enrollment_data.billing_id,
        )
    ).first()

    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    enrollment = Enrollment(
        user_id=user_id,
        course_id=enrollment_data.course_id,
        billing_id=enrollment_data.billing_id,
    )

    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)

    return enrollment


def purchase_course(
    session: Session, purchase_data: PurchaseCourseRequest, user_id: str
) -> tuple[Billing, Optional[Enrollment]]:
    """Handle complete course purchase flow: billing + enrollment."""
    # Create billing record
    billing_data = BillingCreate(
        course_id=purchase_data.course_id,
        payment_method=purchase_data.payment_method,
        transaction_id=purchase_data.transaction_id,
    )

    billing = create_billing(session, billing_data, user_id)

    # For demo purposes, automatically mark as paid
    # In real implementation, this would be handled by payment gateway webhook
    billing = update_billing_status(session, billing.id, BillingStatus.PAID)

    # Create enrollment after payment
    enrollment_data = EnrollmentCreate(
        course_id=purchase_data.course_id,
        billing_id=billing.id,
    )

    enrollment = create_enrollment(session, enrollment_data, user_id)

    return billing, enrollment


def get_user_enrollments(
    session: Session, user_id: str, skip: int = 0, limit: int = 10
) -> tuple[list[Enrollment], int]:
    """Get user's enrollments with pagination."""
    # Get total count
    total_query = select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.is_deleted == False)
    total = len(session.exec(total_query).all())

    # Get paginated results
    query = (
        select(Enrollment)
        .where(Enrollment.user_id == user_id, Enrollment.is_deleted == False)
        .offset(skip)
        .limit(limit)
    )

    enrollments = session.exec(query).all()

    return enrollments, total


def get_enrollment_by_id(session: Session, enrollment_id: str, user_id: str) -> Enrollment:
    """Get enrollment by ID for the current user."""
    enrollment = session.get(Enrollment, enrollment_id)
    if not enrollment or enrollment.is_deleted:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if enrollment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return enrollment


def check_user_enrollment(session: Session, user_id: str, course_id: str) -> bool:
    """Check if user is enrolled in a course."""
    enrollment = session.exec(
        select(Enrollment).where(
            Enrollment.user_id == user_id, Enrollment.course_id == course_id, Enrollment.is_deleted == False
        )
    ).first()

    return enrollment is not None
