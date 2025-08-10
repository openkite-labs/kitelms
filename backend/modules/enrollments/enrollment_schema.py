from typing import Optional

from pydantic import BaseModel

from backend.models.database import BillingStatus


class BillingCreate(BaseModel):
    course_id: str
    payment_method: str
    transaction_id: Optional[str] = ""


class BillingResponse(BaseModel):
    id: str
    user_id: str
    course_id: str
    amount: float
    status: BillingStatus
    payment_method: str
    transaction_id: str
    created_at: str
    updated_at: str


class EnrollmentCreate(BaseModel):
    course_id: str
    billing_id: str


class EnrollmentResponse(BaseModel):
    id: str
    user_id: str
    course_id: str
    billing_id: str
    created_at: str
    updated_at: str
    billing: BillingResponse


class EnrollmentListResponse(BaseModel):
    enrollments: list[EnrollmentResponse]
    total: int
    page: int
    per_page: int


class PurchaseCourseRequest(BaseModel):
    course_id: str
    payment_method: str
    transaction_id: Optional[str] = ""


class PurchaseCourseResponse(BaseModel):
    billing: BillingResponse
    enrollment: Optional[EnrollmentResponse] = None
    message: str
