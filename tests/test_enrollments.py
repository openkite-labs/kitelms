import pytest
from sqlmodel import Session

from backend.models.database import Course


@pytest.fixture
def test_course(session: Session, test_user):
    """Create a test course for enrollment testing."""
    course = Course(
        name="Test Course",
        description="A test course for enrollment",
        price=99.99,
        is_published=True,
        user_id=test_user.id,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def test_purchase_course_flow(auth_client, test_course):
    """Test the complete course purchase flow."""
    # Purchase course
    purchase_data = {"course_id": test_course.id, "payment_method": "credit_card", "transaction_id": "test_txn_123"}

    response = auth_client.post("/enrollments/purchase", json=purchase_data)
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Course purchased successfully"
    assert data["billing"]["status"] == "paid"
    assert data["enrollment"] is not None
    assert data["enrollment"]["course_id"] == test_course.id


def test_check_enrollment(auth_client, test_course):
    """Test checking enrollment status."""
    # Check enrollment before purchase
    response = auth_client.get(f"/enrollments/check/{test_course.id}")
    assert response.status_code == 200
    assert response.json()["is_enrolled"] is False

    # Purchase course
    purchase_data = {"course_id": test_course.id, "payment_method": "credit_card", "transaction_id": "test_txn_456"}

    auth_client.post("/enrollments/purchase", json=purchase_data)

    # Check enrollment after purchase
    response = auth_client.get(f"/enrollments/check/{test_course.id}")
    assert response.status_code == 200
    assert response.json()["is_enrolled"] is True


def test_list_user_enrollments(auth_client, test_course):
    """Test listing user enrollments."""
    # Purchase course first
    purchase_data = {"course_id": test_course.id, "payment_method": "credit_card", "transaction_id": "test_txn_789"}

    auth_client.post("/enrollments/purchase", json=purchase_data)

    # List enrollments
    response = auth_client.get("/enrollments/")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] >= 1
    assert len(data["enrollments"]) >= 1
    assert data["enrollments"][0]["course_id"] == test_course.id


def test_create_billing_only(auth_client, test_course):
    """Test creating billing record without immediate enrollment."""
    billing_data = {"course_id": test_course.id, "payment_method": "paypal", "transaction_id": "test_billing_123"}

    response = auth_client.post("/enrollments/billing", json=billing_data)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "pending"
    assert data["course_id"] == test_course.id
    assert data["payment_method"] == "paypal"


def test_duplicate_purchase_prevention(auth_client, test_course):
    """Test that duplicate purchases are prevented."""
    purchase_data = {
        "course_id": test_course.id,
        "payment_method": "credit_card",
        "transaction_id": "test_duplicate_123",
    }

    # First purchase should succeed
    response = auth_client.post("/enrollments/purchase", json=purchase_data)
    assert response.status_code == 200

    # Second purchase should fail
    response = auth_client.post("/enrollments/purchase", json=purchase_data)
    assert response.status_code == 400
    assert "already purchased" in response.json()["detail"].lower()


def test_unpublished_course_purchase_prevention(auth_client, session: Session, test_user):
    """Test that unpublished courses cannot be purchased."""
    # Create unpublished course
    unpublished_course = Course(
        name="Unpublished Course",
        description="This course is not published",
        price=99.99,
        is_published=False,
        user_id=test_user.id,
    )
    session.add(unpublished_course)
    session.commit()
    session.refresh(unpublished_course)

    purchase_data = {
        "course_id": unpublished_course.id,
        "payment_method": "credit_card",
        "transaction_id": "test_unpublished_123",
    }

    response = auth_client.post("/enrollments/purchase", json=purchase_data)
    assert response.status_code == 400
    assert "not published" in response.json()["detail"].lower()
