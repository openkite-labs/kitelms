
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.models.database import BillingStatus
from backend.models.engine import db_session
from backend.modules.auth.auth_methods import get_current_user
from backend.modules.enrollments.enrollment_methods import (
    billing_to_response,
    check_user_enrollment,
    create_billing,
    create_enrollment,
    enrollment_to_response,
    get_enrollment_by_id,
    get_user_enrollments,
    purchase_course,
    update_billing_status,
)
from backend.modules.enrollments.enrollment_schema import (
    BillingCreate,
    BillingResponse,
    EnrollmentCreate,
    EnrollmentListResponse,
    EnrollmentResponse,
    PurchaseCourseRequest,
    PurchaseCourseResponse,
)

enrollment_router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@enrollment_router.post("/purchase", response_model=PurchaseCourseResponse)
async def purchase_course_endpoint(
    purchase_data: PurchaseCourseRequest,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user),
):
    """Purchase a course - creates billing and enrollment in one step."""
    try:
        billing, enrollment = purchase_course(session, purchase_data, current_user)

        return PurchaseCourseResponse(
            billing=billing_to_response(billing),
            enrollment=enrollment_to_response(enrollment) if enrollment else None,
            message="Course purchased successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@enrollment_router.post("/billing", response_model=BillingResponse)
async def create_billing_endpoint(
    billing_data: BillingCreate, session: Session = Depends(db_session), current_user: str = Depends(get_current_user)
):
    """Create a billing record for course purchase."""
    try:
        billing = create_billing(session, billing_data, current_user)
        return billing_to_response(billing)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@enrollment_router.post("/billing/{billing_id}/confirm", response_model=BillingResponse)
async def confirm_payment(
    billing_id: str, session: Session = Depends(db_session), current_user: str = Depends(get_current_user)
):
    """Confirm payment for a billing record (demo endpoint)."""
    try:
        billing = update_billing_status(session, billing_id, BillingStatus.PAID)
        return billing_to_response(billing)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@enrollment_router.post("/", response_model=EnrollmentResponse)
async def create_enrollment_endpoint(
    enrollment_data: EnrollmentCreate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user),
):
    """Create an enrollment after payment verification."""
    try:
        enrollment = create_enrollment(session, enrollment_data, current_user)
        return enrollment_to_response(enrollment)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@enrollment_router.get("/", response_model=EnrollmentListResponse)
async def list_user_enrollments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user),
):
    """Get current user's enrollments."""
    try:
        enrollments, total = get_user_enrollments(session, current_user, skip, limit)

        return EnrollmentListResponse(
            enrollments=[enrollment_to_response(e) for e in enrollments],
            total=total,
            page=(skip // limit) + 1,
            per_page=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@enrollment_router.get("/{enrollment_id}", response_model=EnrollmentResponse)
async def get_enrollment(
    enrollment_id: str, session: Session = Depends(db_session), current_user: str = Depends(get_current_user)
):
    """Get a specific enrollment by ID."""
    try:
        enrollment = get_enrollment_by_id(session, enrollment_id, current_user)
        return enrollment_to_response(enrollment)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@enrollment_router.get("/check/{course_id}")
async def check_enrollment(
    course_id: str, session: Session = Depends(db_session), current_user: str = Depends(get_current_user)
):
    """Check if user is enrolled in a specific course."""
    try:
        is_enrolled = check_user_enrollment(session, current_user, course_id)
        return {
            "course_id": course_id,
            "is_enrolled": is_enrolled,
            "message": "Enrolled" if is_enrolled else "Not enrolled",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
