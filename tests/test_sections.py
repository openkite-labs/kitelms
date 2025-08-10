import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.models.database import Course, Section
from backend.models.engine import db_session
from backend.modules.auth.auth_methods import get_current_user
from tests.test_utils import (
    create_test_user_data,
    create_test_user_in_db,
)


class TestSectionCreate:
    """Test cases for section creation endpoint"""

    @pytest.fixture
    def sample_course(self, session: Session, test_user):
        """Create a sample course for testing"""
        course = Course(
            name="Test Course",
            description="Test description",
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
    def section_data(self, sample_course):
        """Sample section data for testing"""
        return {
            "name": "Introduction",
            "description": "Course introduction section",
            "order": 1,
            "course_id": sample_course.id,
        }

    def test_create_section_success(self, auth_client: TestClient, section_data):
        """Test successful section creation"""
        response = auth_client.post("/sections/", json=section_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == section_data["name"]
        assert data["description"] == section_data["description"]
        assert data["order"] == section_data["order"]
        assert data["course_id"] == section_data["course_id"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_section_unauthorized(self, client: TestClient, section_data):
        """Test creating section without authentication"""
        response = client.post("/sections/", json=section_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_section_invalid_course(self, auth_client: TestClient):
        """Test creating section for non-existent course"""
        section_data = {
            "name": "Test Section",
            "description": "Test description",
            "order": 1,
            "course_id": "nonexistent-course-id",
        }
        response = auth_client.post("/sections/", json=section_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Course not found" in response.json()["detail"]

    def test_create_section_unauthorized_course(self, auth_client: TestClient, session: Session):
        """Test creating section for course owned by another user"""
        # Create another user and their course
        other_user_data = create_test_user_data()
        other_user_data["email"] = "other@example.com"
        other_user = create_test_user_in_db(session, other_user_data)

        other_course = Course(
            name="Other User's Course",
            description="Course owned by another user",
            category="Test",
            price=50.0,
            user_id=other_user.id,
        )
        session.add(other_course)
        session.commit()
        session.refresh(other_course)

        section_data = {
            "name": "Unauthorized Section",
            "description": "Should not be created",
            "order": 1,
            "course_id": other_course.id,
        }
        response = auth_client.post("/sections/", json=section_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]

    def test_create_section_missing_fields(self, auth_client: TestClient, sample_course):
        """Test creating section with missing required fields"""
        incomplete_data = {
            "name": "Test Section"
            # Missing description, order, course_id
        }
        response = auth_client.post("/sections/", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSectionList:
    """Test cases for section listing endpoint"""

    @pytest.fixture
    def sample_sections(self, session: Session, test_user):
        """Create sample sections for testing"""
        # Create courses
        course1 = Course(
            name="Course 1", description="First course", category="Programming", price=49.99, user_id=test_user.id
        )
        course2 = Course(
            name="Course 2", description="Second course", category="Design", price=79.99, user_id=test_user.id
        )
        session.add_all([course1, course2])
        session.commit()
        session.refresh(course1)
        session.refresh(course2)

        # Create sections
        sections = []
        section_data = [
            {"name": "Introduction", "description": "Course introduction", "order": 1, "course_id": course1.id},
            {"name": "Advanced Topics", "description": "Advanced concepts", "order": 2, "course_id": course1.id},
            {"name": "Getting Started", "description": "Design basics", "order": 1, "course_id": course2.id},
        ]

        for data in section_data:
            section = Section(**data)
            session.add(section)
            sections.append(section)

        session.commit()
        for section in sections:
            session.refresh(section)

        return sections, course1, course2

    def test_list_sections_default(self, client: TestClient, sample_sections):
        """Test listing sections with default parameters"""
        sections, _, _ = sample_sections
        response = client.get("/sections/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sections" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert len(data["sections"]) == 3
        assert data["total"] == 3

    def test_list_sections_pagination(self, client: TestClient, sample_sections):
        """Test section listing with pagination"""
        sections, _, _ = sample_sections
        response = client.get("/sections/?skip=1&limit=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sections"]) == 2
        assert data["skip"] == 1
        assert data["limit"] == 2
        assert data["total"] == 3

    def test_list_sections_filter_by_course(self, client: TestClient, sample_sections):
        """Test filtering sections by course_id"""
        sections, course1, course2 = sample_sections
        response = client.get(f"/sections/?course_id={course1.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sections"]) == 2  # course1 has 2 sections
        assert data["total"] == 2
        for section in data["sections"]:
            assert section["course_id"] == course1.id

    def test_list_sections_invalid_pagination(self, client: TestClient, sample_sections):
        """Test section listing with invalid pagination parameters"""
        # Test negative skip
        response = client.get("/sections/?skip=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test limit too high
        response = client.get("/sections/?limit=101")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test limit too low
        response = client.get("/sections/?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSectionDetail:
    """Test cases for section detail endpoint"""

    @pytest.fixture
    def sample_section_with_lessons(self, session: Session, test_user):
        """Create a sample section with lessons for testing"""
        from backend.models.database import Lesson

        course = Course(
            name="Test Course", description="Test description", category="Test", price=50.0, user_id=test_user.id
        )
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test section description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        # Add some lessons
        lessons = [
            Lesson(title="Lesson 1", content="Content for lesson 1", order=1, section_id=section.id),
            Lesson(title="Lesson 2", content="Content for lesson 2", order=2, section_id=section.id),
        ]
        session.add_all(lessons)
        session.commit()
        for lesson in lessons:
            session.refresh(lesson)

        return section, lessons

    def test_get_section_with_lessons_success(self, client: TestClient, sample_section_with_lessons):
        """Test successful section retrieval with lessons"""
        section, lessons = sample_section_with_lessons
        response = client.get(f"/sections/{section.id}/with-lessons")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == section.id
        assert data["name"] == section.name
        assert data["description"] == section.description
        assert "lessons" in data
        assert len(data["lessons"]) == 2

        # Check lessons are included and ordered
        lesson_titles = [lesson["title"] for lesson in data["lessons"]]
        assert "Lesson 1" in lesson_titles
        assert "Lesson 2" in lesson_titles

    def test_get_section_with_lessons_not_found(self, client: TestClient):
        """Test retrieving non-existent section"""
        response = client.get("/sections/nonexistent-id/with-lessons")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Section not found" in response.json()["detail"]


class TestSectionUpdate:
    """Test cases for section update endpoint"""

    @pytest.fixture
    def sample_section(self, session: Session, test_user):
        """Create a sample section for testing"""
        course = Course(
            name="Test Course", description="Test description", category="Test", price=50.0, user_id=test_user.id
        )
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Original Section", description="Original description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)
        return section

    def test_update_section_success(self, auth_client: TestClient, sample_section):
        """Test successful section update"""
        update_data = {"name": "Updated Section", "description": "Updated description", "order": 2}
        response = auth_client.put(f"/sections/{sample_section.id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["order"] == update_data["order"]
        assert data["id"] == sample_section.id

    def test_update_section_partial(self, auth_client: TestClient, sample_section):
        """Test partial section update"""
        update_data = {"name": "Partially Updated Section"}
        response = auth_client.put(f"/sections/{sample_section.id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == sample_section.description  # Should remain unchanged
        assert data["order"] == sample_section.order  # Should remain unchanged

    def test_update_section_unauthorized(self, client: TestClient, sample_section):
        """Test updating section without authentication"""
        update_data = {"name": "Should not update"}
        response = client.put(f"/sections/{sample_section.id}", json=update_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_section_not_found(self, auth_client: TestClient):
        """Test updating non-existent section"""
        update_data = {"name": "Updated Section"}
        response = auth_client.put("/sections/nonexistent-id", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_section_unauthorized_course(self, auth_client: TestClient, session: Session):
        """Test updating section for course owned by another user"""
        # Create another user and their course with section
        other_user_data = create_test_user_data()
        other_user_data["email"] = "other@example.com"
        other_user = create_test_user_in_db(session, other_user_data)

        other_course = Course(
            name="Other User's Course",
            description="Course owned by another user",
            category="Test",
            price=50.0,
            user_id=other_user.id,
        )
        session.add(other_course)
        session.commit()
        session.refresh(other_course)

        other_section = Section(
            name="Other User's Section", description="Section owned by another user", order=1, course_id=other_course.id
        )
        session.add(other_section)
        session.commit()
        session.refresh(other_section)

        update_data = {"name": "Should not update"}
        response = auth_client.put(f"/sections/{other_section.id}", json=update_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]


class TestSectionDelete:
    """Test cases for section deletion endpoint"""

    @pytest.fixture
    def sample_section(self, session: Session, test_user):
        """Create a sample section for testing"""
        course = Course(
            name="Test Course", description="Test description", category="Test", price=50.0, user_id=test_user.id
        )
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(
            name="Section to Delete", description="This section will be deleted", order=1, course_id=course.id
        )
        session.add(section)
        session.commit()
        session.refresh(section)
        return section

    def test_delete_section_success(self, auth_client: TestClient, sample_section):
        """Test successful section deletion"""
        response = auth_client.delete(f"/sections/{sample_section.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]

        # Verify section is soft deleted by trying to get it with lessons
        get_response = auth_client.get(f"/sections/{sample_section.id}/with-lessons")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_section_unauthorized(self, client: TestClient, sample_section):
        """Test deleting section without authentication"""
        response = client.delete(f"/sections/{sample_section.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_section_not_found(self, auth_client: TestClient):
        """Test deleting non-existent section"""
        response = auth_client.delete("/sections/nonexistent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_section_unauthorized_course(self, auth_client: TestClient, session: Session):
        """Test deleting section for course owned by another user"""
        # Create another user and their course with section
        other_user_data = create_test_user_data()
        other_user_data["email"] = "other@example.com"
        other_user = create_test_user_in_db(session, other_user_data)

        other_course = Course(
            name="Other User's Course",
            description="Course owned by another user",
            category="Test",
            price=50.0,
            user_id=other_user.id,
        )
        session.add(other_course)
        session.commit()
        session.refresh(other_course)

        other_section = Section(
            name="Other User's Section", description="Section owned by another user", order=1, course_id=other_course.id
        )
        session.add(other_section)
        session.commit()
        session.refresh(other_section)

        response = auth_client.delete(f"/sections/{other_section.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]


class TestSectionReorder:
    """Test cases for section reordering endpoint"""

    @pytest.fixture
    def sample_sections_for_reorder(self, session: Session, test_user):
        """Create sample sections for reordering tests"""
        course = Course(
            name="Test Course", description="Test description", category="Test", price=50.0, user_id=test_user.id
        )
        session.add(course)
        session.commit()
        session.refresh(course)

        sections = []
        for i in range(3):
            section = Section(
                name=f"Section {i + 1}", description=f"Description {i + 1}", order=i + 1, course_id=course.id
            )
            session.add(section)
            sections.append(section)

        session.commit()
        for section in sections:
            session.refresh(section)

        return sections, course

    def test_reorder_sections_success(self, auth_client: TestClient, sample_sections_for_reorder):
        """Test successful section reordering"""
        sections, course = sample_sections_for_reorder

        # Reorder sections: reverse the order
        reorder_data = {
            "course_id": course.id,
            "section_orders": [
                {"id": sections[2].id, "order": 1},
                {"id": sections[1].id, "order": 2},
                {"id": sections[0].id, "order": 3},
            ],
        }

        response = auth_client.put("/sections/reorder", json=reorder_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "reordered successfully" in data["message"]

        # Verify the new order by listing sections
        list_response = auth_client.get(f"/sections/?course_id={course.id}")
        assert list_response.status_code == status.HTTP_200_OK

        sections_data = list_response.json()["sections"]
        # Sections should be ordered by the new order
        assert sections_data[0]["id"] == sections[2].id
        assert sections_data[1]["id"] == sections[1].id
        assert sections_data[2]["id"] == sections[0].id

    def test_reorder_sections_unauthorized(self, client: TestClient, sample_sections_for_reorder):
        """Test reordering sections without authentication"""
        sections, course = sample_sections_for_reorder

        reorder_data = {
            "course_id": course.id,
            "section_orders": [{"id": sections[0].id, "order": 2}, {"id": sections[1].id, "order": 1}],
        }

        response = client.put("/sections/reorder", json=reorder_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_reorder_sections_course_not_found(self, auth_client: TestClient):
        """Test reordering sections for non-existent course"""
        reorder_data = {
            "course_id": "nonexistent-course",
            "section_orders": [{"id": "section1", "order": 1}, {"id": "section2", "order": 2}],
        }

        response = auth_client.put("/sections/reorder", json=reorder_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Course not found" in response.json()["detail"]

    def test_reorder_sections_unauthorized_course(self, auth_client: TestClient, session: Session):
        """Test reordering sections for course owned by another user"""
        # Create another user and their course
        other_user_data = create_test_user_data()
        other_user_data["email"] = "other@example.com"
        other_user = create_test_user_in_db(session, other_user_data)

        other_course = Course(
            name="Other User's Course",
            description="Course owned by another user",
            category="Test",
            price=50.0,
            user_id=other_user.id,
        )
        session.add(other_course)
        session.commit()
        session.refresh(other_course)

        reorder_data = {
            "course_id": other_course.id,
            "section_orders": [{"id": "section1", "order": 1}, {"id": "section2", "order": 2}],
        }

        response = auth_client.put("/sections/reorder", json=reorder_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]


class TestSectionIntegration:
    """Integration tests for section workflows"""

    def test_complete_section_lifecycle(self, auth_client: TestClient, session: Session, test_user):
        """Test complete section lifecycle: create course, create section, update, delete"""
        # 1. Create a course first
        course_data = {
            "name": "Integration Test Course",
            "description": "Course for integration testing",
            "category": "Test",
            "price": 99.99,
        }
        course_response = auth_client.post("/courses/", json=course_data)
        assert course_response.status_code == status.HTTP_200_OK
        course = course_response.json()

        # 2. Create a section
        section_data = {
            "name": "Test Section",
            "description": "Section for integration testing",
            "order": 1,
            "course_id": course["id"],
        }
        create_response = auth_client.post("/sections/", json=section_data)
        assert create_response.status_code == status.HTTP_200_OK
        section = create_response.json()
        assert section["name"] == section_data["name"]

        # 3. Get section with lessons
        get_response = auth_client.get(f"/sections/{section['id']}/with-lessons")
        assert get_response.status_code == status.HTTP_200_OK
        section_detail = get_response.json()
        assert section_detail["id"] == section["id"]
        assert "lessons" in section_detail

        # 4. Update the section
        update_data = {"name": "Updated Test Section", "description": "Updated description"}
        update_response = auth_client.put(f"/sections/{section['id']}", json=update_data)
        assert update_response.status_code == status.HTTP_200_OK
        updated_section = update_response.json()
        assert updated_section["name"] == update_data["name"]
        assert updated_section["description"] == update_data["description"]

        # 5. List sections for the course
        list_response = auth_client.get(f"/sections/?course_id={course['id']}")
        assert list_response.status_code == status.HTTP_200_OK
        sections_list = list_response.json()
        assert sections_list["total"] == 1
        assert sections_list["sections"][0]["id"] == section["id"]

        # 6. Delete the section
        delete_response = auth_client.delete(f"/sections/{section['id']}")
        assert delete_response.status_code == status.HTTP_200_OK

        # 7. Verify section is deleted
        get_deleted_response = auth_client.get(f"/sections/{section['id']}/with-lessons")
        assert get_deleted_response.status_code == status.HTTP_404_NOT_FOUND

        # 8. Verify section is not in the list
        final_list_response = auth_client.get(f"/sections/?course_id={course['id']}")
        assert final_list_response.status_code == status.HTTP_200_OK
        final_sections_list = final_list_response.json()
        assert final_sections_list["total"] == 0

    def test_section_ownership_isolation(self, session: Session):
        """Test that users can only access their own course sections"""
        from fastapi.testclient import TestClient

        from backend.main import app

        # Create two users
        user1_data = create_test_user_data()
        user1_data["email"] = "user1@example.com"
        user1 = create_test_user_in_db(session, user1_data)

        user2_data = create_test_user_data()
        user2_data["email"] = "user2@example.com"
        user2 = create_test_user_in_db(session, user2_data)

        # Create courses for each user
        course1 = Course(
            name="User 1 Course", description="Course owned by user 1", category="Test", price=50.0, user_id=user1.id
        )
        course2 = Course(
            name="User 2 Course", description="Course owned by user 2", category="Test", price=50.0, user_id=user2.id
        )
        session.add_all([course1, course2])
        session.commit()
        session.refresh(course1)
        session.refresh(course2)

        # Create sections for each course
        section1 = Section(
            name="User 1 Section", description="Section in user 1's course", order=1, course_id=course1.id
        )
        section2 = Section(
            name="User 2 Section", description="Section in user 2's course", order=1, course_id=course2.id
        )
        session.add_all([section1, section2])
        session.commit()
        session.refresh(section1)
        session.refresh(section2)

        # Create authenticated clients for each user
        def get_user1_override():
            return user1.id

        def get_user2_override():
            return user2.id

        try:
            # Override session dependency to use the test session
            def get_session_override():
                return session

            # Test User 1 operations
            app.dependency_overrides[db_session] = get_session_override
            app.dependency_overrides[get_current_user] = get_user1_override
            client1 = TestClient(app)

            # User 1 should be able to update their section
            update_data = {"name": "Updated by User 1"}
            response1 = client1.put(f"/sections/{section1.id}", json=update_data)
            assert response1.status_code == status.HTTP_200_OK

            # User 1 should NOT be able to update user 2's section
            response1_unauthorized = client1.put(f"/sections/{section2.id}", json=update_data)
            assert response1_unauthorized.status_code == status.HTTP_403_FORBIDDEN

            # Test User 2 operations
            app.dependency_overrides[get_current_user] = get_user2_override
            client2 = TestClient(app)

            # User 2 should be able to update their section
            update_data2 = {"name": "Updated by User 2"}
            response2 = client2.put(f"/sections/{section2.id}", json=update_data2)
            assert response2.status_code == status.HTTP_200_OK

            # User 2 should NOT be able to update user 1's section
            response2_unauthorized = client2.put(f"/sections/{section1.id}", json=update_data2)
            assert response2_unauthorized.status_code == status.HTTP_403_FORBIDDEN

        finally:
            # Clean up dependency overrides
            app.dependency_overrides.clear()
