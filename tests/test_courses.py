import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.models.database import Course
from tests.test_utils import (
    create_test_user_data,
    create_test_user_in_db,
)


class TestCourseCreate:
    """Test cases for course creation endpoint"""

    @pytest.fixture
    def course_data(self):
        """Sample course data for testing"""
        return {
            "name": "Test Course",
            "description": "A comprehensive test course",
            "cover_image_url": "https://example.com/cover.jpg",
            "video_preview_url": "https://example.com/preview.mp4",
            "price": 99.99,
            "category": "Programming",
            "tags": "python,testing,fastapi",
            "is_published": False,
        }

    def test_create_course_success(self, auth_client: TestClient, course_data):
        """Test successful course creation"""
        response = auth_client.post("/courses/", json=course_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == course_data["name"]
        assert data["description"] == course_data["description"]
        assert data["price"] == course_data["price"]
        assert data["category"] == course_data["category"]
        assert data["is_published"] == course_data["is_published"]
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_course_minimal_data(self, auth_client: TestClient):
        """Test course creation with minimal required data"""
        minimal_data = {"name": "Minimal Course", "description": "Basic description"}
        response = auth_client.post("/courses/", json=minimal_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == minimal_data["name"]
        assert data["description"] == minimal_data["description"]
        assert data["price"] == 0.0  # Default value
        assert data["category"] == ""  # Default value
        assert data["is_published"] == False  # Default value

    def test_create_course_unauthorized(self, client: TestClient, course_data):
        """Test creating course without authentication"""
        response = client.post("/courses/", json=course_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_course_missing_required_fields(self, auth_client: TestClient):
        """Test course creation with missing required fields"""
        incomplete_data = {
            "name": "Test Course"
            # Missing description
        }
        response = auth_client.post("/courses/", json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCourseList:
    """Test cases for course listing endpoint"""

    @pytest.fixture
    def sample_courses(self, session: Session, test_user):
        """Create sample courses for testing"""
        courses = []
        course_data = [
            {
                "name": "Python Basics",
                "description": "Learn Python fundamentals",
                "category": "Programming",
                "price": 49.99,
                "is_published": True,
                "user_id": test_user.id,
            },
            {
                "name": "Advanced Python",
                "description": "Advanced Python concepts",
                "category": "Programming",
                "price": 99.99,
                "is_published": False,
                "user_id": test_user.id,
            },
            {
                "name": "Web Development",
                "description": "Build web applications",
                "category": "Web",
                "price": 79.99,
                "is_published": True,
                "user_id": test_user.id,
            },
        ]

        for data in course_data:
            course = Course(**data)
            session.add(course)
            courses.append(course)

        session.commit()
        for course in courses:
            session.refresh(course)

        return courses

    def test_list_courses_default(self, client: TestClient, sample_courses):
        """Test listing courses with default parameters"""
        response = client.get("/courses/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "courses" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["courses"]) <= 10  # Default limit

    def test_list_courses_pagination(self, client: TestClient, sample_courses):
        """Test course listing with pagination"""
        response = client.get("/courses/?skip=0&limit=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["courses"]) <= 2
        assert data["per_page"] == 2
        assert data["page"] == 1

    def test_list_courses_filter_by_published(self, client: TestClient, sample_courses):
        """Test filtering courses by published status"""
        response = client.get("/courses/?is_published=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for course in data["courses"]:
            assert course["is_published"] == True

    def test_list_courses_filter_by_category(self, client: TestClient, sample_courses):
        """Test filtering courses by category"""
        response = client.get("/courses/?category=Programming")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for course in data["courses"]:
            assert course["category"] == "Programming"

    def test_list_courses_search(self, client: TestClient, sample_courses):
        """Test searching courses"""
        response = client.get("/courses/?search=Python")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should find courses with "Python" in name or description
        assert len(data["courses"]) >= 1

    def test_list_my_courses(self, auth_client: TestClient, sample_courses):
        """Test listing user's own courses"""
        response = auth_client.get("/courses/?my_courses=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All returned courses should belong to the authenticated user
        assert len(data["courses"]) >= 0


class TestCourseDetail:
    """Test cases for course detail endpoint"""

    @pytest.fixture
    def sample_course(self, session: Session, test_user):
        """Create a sample course for testing"""
        course = Course(
            name="Test Course",
            description="Test description",
            category="Test",
            price=50.0,
            is_published=True,
            user_id=test_user.id,
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        return course

    def test_get_course_success(self, client: TestClient, sample_course):
        """Test successful course retrieval"""
        response = client.get(f"/courses/{sample_course.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_course.id
        assert data["name"] == sample_course.name
        assert data["description"] == sample_course.description

    def test_get_course_not_found(self, client: TestClient):
        """Test retrieving non-existent course"""
        response = client.get("/courses/nonexistent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Course not found" in response.json()["detail"]


class TestCourseUpdate:
    """Test cases for course update endpoint"""

    @pytest.fixture
    def sample_course(self, session: Session, test_user):
        """Create a sample course for testing"""
        course = Course(
            name="Original Course",
            description="Original description",
            category="Original",
            price=50.0,
            is_published=False,
            user_id=test_user.id,
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        return course

    def test_update_course_success(self, auth_client: TestClient, sample_course):
        """Test successful course update"""
        update_data = {"name": "Updated Course", "description": "Updated description", "price": 75.0}
        response = auth_client.put(f"/courses/{sample_course.id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["price"] == update_data["price"]

    def test_update_course_partial(self, auth_client: TestClient, sample_course):
        """Test partial course update"""
        update_data = {"name": "Partially Updated Course"}
        response = auth_client.put(f"/courses/{sample_course.id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == sample_course.description  # Should remain unchanged

    def test_update_course_unauthorized(self, client: TestClient, sample_course):
        """Test updating course without authentication"""
        update_data = {"name": "Unauthorized Update"}
        response = client.put(f"/courses/{sample_course.id}", json=update_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_course_not_found(self, auth_client: TestClient):
        """Test updating non-existent course"""
        update_data = {"name": "Updated Course"}
        response = auth_client.put("/courses/nonexistent-id", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_course_wrong_owner(self, session: Session, sample_course):
        """Test updating course by non-owner"""
        from backend.main import app
        from backend.models.engine import db_session
        from backend.modules.auth import auth_methods

        # Create another user
        other_user_data = create_test_user_data(email="other@example.com")
        other_user = create_test_user_in_db(session, other_user_data)

        def get_session_override():
            return session

        def get_other_user_override():
            return other_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_other_user_override
        other_client = TestClient(app)

        update_data = {"name": "Unauthorized Update"}
        response = other_client.put(f"/courses/{sample_course.id}", json=update_data)

        # Should return 403 for unauthorized access
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]

        # Clean up
        app.dependency_overrides.clear()


class TestCourseDelete:
    """Test cases for course deletion endpoint"""

    @pytest.fixture
    def sample_course(self, session: Session, test_user):
        """Create a sample course for testing"""
        course = Course(
            name="Course to Delete",
            description="This course will be deleted",
            category="Test",
            price=50.0,
            is_published=False,
            user_id=test_user.id,
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        return course

    def test_delete_course_success(self, auth_client: TestClient, sample_course):
        """Test successful course deletion"""
        response = auth_client.delete(f"/courses/{sample_course.id}")

        assert response.status_code == status.HTTP_200_OK
        assert "Course deleted successfully" in response.json()["message"]

    def test_delete_course_unauthorized(self, client: TestClient, sample_course):
        """Test deleting course without authentication"""
        response = client.delete(f"/courses/{sample_course.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_course_not_found(self, auth_client: TestClient):
        """Test deleting non-existent course"""
        response = auth_client.delete("/courses/nonexistent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_course_wrong_owner(self, session: Session, sample_course):
        """Test deleting course by non-owner"""
        from backend.main import app
        from backend.models.engine import db_session
        from backend.modules.auth import auth_methods

        # Create another user
        other_user_data = create_test_user_data(email="other@example.com")
        other_user = create_test_user_in_db(session, other_user_data)

        def get_session_override():
            return session

        def get_other_user_override():
            return other_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_other_user_override
        other_client = TestClient(app)

        response = other_client.delete(f"/courses/{sample_course.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]

        # Clean up
        app.dependency_overrides.clear()


class TestCoursePublishing:
    """Test cases for course publishing/unpublishing endpoints"""

    @pytest.fixture
    def unpublished_course(self, session: Session, test_user):
        """Create an unpublished course for testing"""
        course = Course(
            name="Unpublished Course",
            description="This course is not published",
            category="Test",
            price=50.0,
            is_published=False,
            user_id=test_user.id,
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        return course

    @pytest.fixture
    def published_course(self, session: Session, test_user):
        """Create a published course for testing"""
        course = Course(
            name="Published Course",
            description="This course is published",
            category="Test",
            price=50.0,
            is_published=True,
            user_id=test_user.id,
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        return course

    def test_publish_course_success(self, auth_client: TestClient, unpublished_course):
        """Test successful course publishing"""
        response = auth_client.post(f"/courses/{unpublished_course.id}/publish")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_published"] == True

    def test_unpublish_course_success(self, auth_client: TestClient, published_course):
        """Test successful course unpublishing"""
        response = auth_client.post(f"/courses/{published_course.id}/unpublish")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_published"] == False

    def test_publish_course_unauthorized(self, client: TestClient, unpublished_course):
        """Test publishing course without authentication"""
        response = client.post(f"/courses/{unpublished_course.id}/publish")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_publish_course_not_found(self, auth_client: TestClient):
        """Test publishing non-existent course"""
        response = auth_client.post("/courses/nonexistent-id/publish")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_publish_course_wrong_owner(self, session: Session, unpublished_course):
        """Test publishing course by non-owner"""
        from backend.main import app
        from backend.models.engine import db_session
        from backend.modules.auth import auth_methods

        # Create another user
        other_user_data = create_test_user_data(email="other@example.com")
        other_user = create_test_user_in_db(session, other_user_data)

        def get_session_override():
            return session

        def get_other_user_override():
            return other_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_other_user_override
        other_client = TestClient(app)

        response = other_client.post(f"/courses/{unpublished_course.id}/publish")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]

        # Clean up
        app.dependency_overrides.clear()

    def test_unpublish_course_wrong_owner(self, session: Session, published_course):
        """Test unpublishing course by non-owner"""
        from backend.main import app
        from backend.models.engine import db_session
        from backend.modules.auth import auth_methods

        # Create another user
        other_user_data = create_test_user_data(email="other@example.com")
        other_user = create_test_user_in_db(session, other_user_data)

        def get_session_override():
            return session

        def get_other_user_override():
            return other_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_other_user_override
        other_client = TestClient(app)

        response = other_client.post(f"/courses/{published_course.id}/unpublish")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]

        # Clean up
        app.dependency_overrides.clear()


class TestCourseIntegration:
    """Integration tests for course workflows"""

    def test_complete_course_lifecycle(self, auth_client: TestClient):
        """Test complete course creation, update, publish, and delete workflow"""
        # Create course
        course_data = {
            "name": "Lifecycle Test Course",
            "description": "Testing complete lifecycle",
            "price": 99.99,
            "category": "Test",
        }
        create_response = auth_client.post("/courses/", json=course_data)
        assert create_response.status_code == status.HTTP_200_OK
        course_id = create_response.json()["id"]

        # Update course
        update_data = {"name": "Updated Lifecycle Course"}
        update_response = auth_client.put(f"/courses/{course_id}", json=update_data)
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["name"] == update_data["name"]

        # Publish course
        publish_response = auth_client.post(f"/courses/{course_id}/publish")
        assert publish_response.status_code == status.HTTP_200_OK
        assert publish_response.json()["is_published"] == True

        # Unpublish course
        unpublish_response = auth_client.post(f"/courses/{course_id}/unpublish")
        assert unpublish_response.status_code == status.HTTP_200_OK
        assert unpublish_response.json()["is_published"] == False

        # Delete course
        delete_response = auth_client.delete(f"/courses/{course_id}")
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify course is deleted
        get_response = auth_client.get(f"/courses/{course_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_course_ownership_isolation(self, session: Session):
        """Test that users can only access their own courses"""
        from backend.main import app
        from backend.models.engine import db_session
        from backend.modules.auth import auth_methods

        # Create two users
        user1_data = create_test_user_data(email="user1@example.com")
        user2_data = create_test_user_data(email="user2@example.com")
        user1 = create_test_user_in_db(session, user1_data)
        user2 = create_test_user_in_db(session, user2_data)

        def get_session_override():
            return session

        # Create client for user1
        def get_user1_override():
            return user1.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_user1_override
        user1_client = TestClient(app)

        # User1 creates a course
        course_data = {"name": "User1's Course", "description": "This belongs to user1"}
        create_response = user1_client.post("/courses/", json=course_data)
        assert create_response.status_code == status.HTTP_200_OK
        course_id = create_response.json()["id"]

        # Create client for user2
        def get_user2_override():
            return user2.id

        app.dependency_overrides[auth_methods.get_current_user] = get_user2_override
        user2_client = TestClient(app)

        # User2 tries to update user1's course
        update_data = {"name": "Hacked Course"}
        update_response = user2_client.put(f"/courses/{course_id}", json=update_data)
        assert update_response.status_code == status.HTTP_403_FORBIDDEN

        # User2 tries to delete user1's course
        delete_response = user2_client.delete(f"/courses/{course_id}")
        assert delete_response.status_code == status.HTTP_403_FORBIDDEN

        # Clean up
        app.dependency_overrides.clear()
