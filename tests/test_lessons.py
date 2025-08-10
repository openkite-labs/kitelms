from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.main import app
from backend.models.database import Course, Lesson, Section, User
from backend.models.engine import db_session
from backend.modules.auth import auth_methods


class TestLessonRoutes:
    """Test lesson CRUD operations."""

    def test_create_lesson_success(self, session: Session):
        """Test successful lesson creation."""
        # Create a user, course, and section first
        user = User(id="user123", email="test1@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        lesson_data = {
            "title": "Test Lesson",
            "content": "This is test content",
            "video_url": "https://example.com/video",
            "order": 1,
            "section_id": section.id,
        }

        # Create client with session override
        client = TestClient(app)
        client.app.dependency_overrides[db_session] = lambda: session
        client.app.dependency_overrides[auth_methods.get_current_user] = lambda: user.id

        response = client.post("/lessons/", json=lesson_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Test Lesson"
        assert data["content"] == "This is test content"
        assert data["video_url"] == "https://example.com/video"
        assert data["order"] == 1
        assert data["section_id"] == section.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_lesson_section_not_found(self, session: Session):
        """Test lesson creation with non-existent section."""
        # Create a user first
        user = User(name="testuser", email="test@example.com", password="password123")
        session.add(user)
        session.commit()
        session.refresh(user)

        lesson_data = {
            "title": "Test Lesson",
            "content": "This is test content",
            "order": 1,
            "section_id": "nonexistent_section_id",  # Non-existent section ID
        }

        # Create client with session override
        client = TestClient(app)
        client.app.dependency_overrides[db_session] = lambda: session
        client.app.dependency_overrides[auth_methods.get_current_user] = lambda: user.id

        response = client.post("/lessons/", json=lesson_data)
        assert response.status_code == 404
        assert "Section not found" in response.json()["detail"]

    def test_create_lesson_unauthorized(self, auth_client: TestClient, session: Session):
        """Test lesson creation for section not owned by user."""
        # Create another user and their course/section
        other_user = User(id="other_user", email="other1@example.com", name="Other User", password="password456")
        session.add(other_user)
        session.commit()

        course = Course(name="Other Course", description="Other Description", user_id=other_user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Other Section", description="Other Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        lesson_data = {"title": "Test Lesson", "content": "This is test content", "order": 1, "section_id": section.id}

        response = auth_client.post("/lessons/", json=lesson_data)
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_create_lesson_missing_fields(self, auth_client: TestClient):
        """Test lesson creation with missing required fields."""
        lesson_data = {
            "title": "Test Lesson"
            # Missing order and section_id
        }

        response = auth_client.post("/lessons/", json=lesson_data)
        assert response.status_code == 422

    def test_get_lessons_success(self, client: TestClient, session: Session):
        """Test successful lesson listing."""
        # Create test data
        user = User(id="user123", email="test2@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        # Create multiple lessons
        lessons = [
            Lesson(title=f"Lesson {i}", content=f"Content {i}", order=i, section_id=section.id) for i in range(1, 4)
        ]
        for lesson in lessons:
            session.add(lesson)
        session.commit()

        response = client.get("/lessons/")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 3
        assert len(data["lessons"]) == 3
        assert data["skip"] == 0
        assert data["limit"] == 10

        # Check lesson order
        for i, lesson in enumerate(data["lessons"]):
            assert lesson["title"] == f"Lesson {i + 1}"
            assert lesson["order"] == i + 1

    def test_get_lessons_with_section_filter(self, client: TestClient, session: Session):
        """Test lesson listing with section filter."""
        # Create test data with multiple sections
        user = User(id="user123", email="test3@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section1 = Section(name="Section 1", description="Section 1 Description", order=1, course_id=course.id)
        section2 = Section(name="Section 2", description="Section 2 Description", order=2, course_id=course.id)
        session.add(section1)
        session.add(section2)
        session.commit()
        session.refresh(section1)
        session.refresh(section2)

        # Create lessons for both sections
        lesson1 = Lesson(title="Lesson 1", content="Content 1", order=1, section_id=section1.id)
        lesson2 = Lesson(title="Lesson 2", content="Content 2", order=1, section_id=section2.id)
        session.add(lesson1)
        session.add(lesson2)
        session.commit()

        # Test filtering by section1
        response = client.get(f"/lessons/?section_id={section1.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert len(data["lessons"]) == 1
        assert data["lessons"][0]["title"] == "Lesson 1"
        assert data["lessons"][0]["section_id"] == section1.id

    def test_get_lessons_pagination(self, client: TestClient, session: Session):
        """Test lesson listing with pagination."""
        # Create test data
        user = User(id="user123", email="test4@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        # Create 5 lessons
        lessons = [
            Lesson(title=f"Lesson {i}", content=f"Content {i}", order=i, section_id=section.id) for i in range(1, 6)
        ]
        for lesson in lessons:
            session.add(lesson)
        session.commit()

        # Test pagination
        response = client.get("/lessons/?skip=2&limit=2")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 5
        assert len(data["lessons"]) == 2
        assert data["skip"] == 2
        assert data["limit"] == 2
        assert data["lessons"][0]["title"] == "Lesson 3"
        assert data["lessons"][1]["title"] == "Lesson 4"

    def test_get_lesson_by_id_success(self, session: Session):
        """Test successful lesson retrieval by ID."""
        # Create test data
        user = User(id="user123", email="test5@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        lesson = Lesson(
            title="Test Lesson",
            content="Test Content",
            video_url="https://example.com/video",
            order=1,
            section_id=section.id,
        )
        session.add(lesson)
        session.commit()
        session.refresh(lesson)

        # Create client with session override
        client = TestClient(app)
        client.app.dependency_overrides[db_session] = lambda: session
        client.app.dependency_overrides[auth_methods.get_current_user] = lambda: user.id

        response = client.get(f"/lessons/{lesson.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == lesson.id
        assert data["title"] == "Test Lesson"
        assert data["content"] == "Test Content"
        assert data["video_url"] == "https://example.com/video"
        assert data["order"] == 1
        assert data["section_id"] == section.id

    def test_get_lesson_by_id_not_found(self, client: TestClient):
        """Test lesson retrieval with non-existent ID."""
        response = client.get("/lessons/nonexistent_id")
        assert response.status_code == 404
        assert "Lesson not found" in response.json()["detail"]

    def test_update_lesson_success(self, auth_client: TestClient, session: Session):
        """Test successful lesson update."""
        # Create test data
        user = User(id="user123", email="test6@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        lesson = Lesson(title="Original Title", content="Original Content", order=1, section_id=section.id)
        session.add(lesson)
        session.commit()
        session.refresh(lesson)

        update_data = {
            "title": "Updated Title",
            "content": "Updated Content",
            "video_url": "https://example.com/new-video",
        }

        # Create client with session override
        client = TestClient(app)
        client.app.dependency_overrides[db_session] = lambda: session
        client.app.dependency_overrides[auth_methods.get_current_user] = lambda: user.id

        response = client.put(f"/lessons/{lesson.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated Content"
        assert data["video_url"] == "https://example.com/new-video"
        assert data["order"] == 1  # Should remain unchanged

    def test_update_lesson_partial(self, session: Session):
        """Test partial lesson update."""
        # Create test data
        user = User(id="user123", email="test7@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        lesson = Lesson(
            title="Original Title",
            content="Original Content",
            video_url="https://example.com/original",
            order=1,
            section_id=section.id,
        )
        session.add(lesson)
        session.commit()
        session.refresh(lesson)

        # Create client with session override
        client = TestClient(app)
        client.app.dependency_overrides[db_session] = lambda: session
        client.app.dependency_overrides[auth_methods.get_current_user] = lambda: user.id

        # Update only title
        update_data = {"title": "Updated Title Only"}

        response = client.put(f"/lessons/{lesson.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Updated Title Only"
        assert data["content"] == "Original Content"  # Should remain unchanged
        assert data["video_url"] == "https://example.com/original"  # Should remain unchanged
        assert data["order"] == 1

    def test_update_lesson_not_found(self, auth_client: TestClient):
        """Test lesson update with non-existent ID."""
        update_data = {"title": "Updated Title"}

        response = auth_client.put("/lessons/nonexistent_id", json=update_data)
        assert response.status_code == 404
        assert "Lesson not found" in response.json()["detail"]

    def test_update_lesson_unauthorized(self, auth_client: TestClient, session: Session):
        """Test lesson update by non-owner."""
        # Create another user and their lesson
        other_user = User(id="other_user", email="other@example.com", name="Other User", password="password456")
        session.add(other_user)
        session.commit()

        course = Course(name="Other Course", description="Other Description", user_id=other_user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Other Section", description="Other Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        lesson = Lesson(title="Other Lesson", content="Other Content", order=1, section_id=section.id)
        session.add(lesson)
        session.commit()
        session.refresh(lesson)

        update_data = {"title": "Hacked Title"}

        response = auth_client.put(f"/lessons/{lesson.id}", json=update_data)
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_delete_lesson(self, session: Session):
        """Test successful lesson deletion."""
        # Create test data
        user = User(id="user123", email="test9@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        lesson = Lesson(title="Test Lesson", content="Test Content", order=1, section_id=section.id)
        session.add(lesson)
        session.commit()
        session.refresh(lesson)

        # Create client with session override
        client = TestClient(app)
        client.app.dependency_overrides[db_session] = lambda: session
        client.app.dependency_overrides[auth_methods.get_current_user] = lambda: user.id

        response = client.delete(f"/lessons/{lesson.id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify lesson is soft deleted
        session.refresh(lesson)
        assert lesson.is_deleted is True

    def test_delete_lesson_not_found(self, auth_client: TestClient):
        """Test lesson deletion with non-existent ID."""
        response = auth_client.delete("/lessons/nonexistent_id")
        assert response.status_code == 404
        assert "Lesson not found" in response.json()["detail"]

    def test_delete_lesson_unauthorized(self, auth_client: TestClient, session: Session):
        """Test lesson deletion by non-owner."""
        # Create another user and their lesson
        other_user = User(id="other_user", email="other@example.com", name="Other User", password="password456")
        session.add(other_user)
        session.commit()

        course = Course(name="Other Course", description="Other Description", user_id=other_user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Other Section", description="Other Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        lesson = Lesson(title="Other Lesson", content="Other Content", order=1, section_id=section.id)
        session.add(lesson)
        session.commit()
        session.refresh(lesson)

        response = auth_client.delete(f"/lessons/{lesson.id}")
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_reorder_lessons_success(self, session: Session):
        """Test successful lesson reordering."""
        # Create test data
        user = User(id="user123", email="test10@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        # Create multiple lessons
        lessons = [
            Lesson(title=f"Lesson {i}", content=f"Content {i}", order=i, section_id=section.id) for i in range(1, 4)
        ]
        for lesson in lessons:
            session.add(lesson)
        session.commit()
        for lesson in lessons:
            session.refresh(lesson)

        # Reorder lessons (reverse order)
        reorder_data = {
            "section_id": section.id,
            "lesson_orders": [
                {"id": lessons[2].id, "order": 1},
                {"id": lessons[1].id, "order": 2},
                {"id": lessons[0].id, "order": 3},
            ],
        }

        # Create client with session override
        client = TestClient(app)
        client.app.dependency_overrides[db_session] = lambda: session
        client.app.dependency_overrides[auth_methods.get_current_user] = lambda: user.id

        response = client.put("/lessons/reorder", json=reorder_data)
        assert response.status_code == 200
        assert "reordered successfully" in response.json()["message"]

        # Verify new order
        for lesson in lessons:
            session.refresh(lesson)

        assert lessons[0].order == 3
        assert lessons[1].order == 2
        assert lessons[2].order == 1

    def test_reorder_lessons_section_not_found(self, auth_client: TestClient):
        """Test lesson reordering with non-existent section."""
        reorder_data = {
            "section_id": "nonexistent_section_id",
            "lesson_orders": [{"id": "lesson1", "order": 1}, {"id": "lesson2", "order": 2}],
        }

        response = auth_client.put("/lessons/reorder", json=reorder_data)
        assert response.status_code == 404
        assert "Section not found" in response.json()["detail"]

    def test_reorder_lessons_unauthorized(self, auth_client: TestClient, session: Session):
        """Test lesson reordering by non-owner."""
        # Create another user and their section
        other_user = User(id="other_user", email="other@example.com", name="Other User", password="password456")
        session.add(other_user)
        session.commit()

        course = Course(name="Other Course", description="Other Description", user_id=other_user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Other Section", description="Other Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        reorder_data = {
            "section_id": section.id,
            "lesson_orders": [{"id": "lesson1", "order": 1}, {"id": "lesson2", "order": 2}],
        }

        response = auth_client.put("/lessons/reorder", json=reorder_data)
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]


class TestLessonIntegration:
    """Integration tests for lesson functionality."""

    def test_lesson_lifecycle(self, session: Session):
        """Test complete lesson lifecycle: create, read, update, delete."""
        # Setup: Create user, course, and section
        user = User(id="user123", email="test11@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        section = Section(name="Test Section", description="Test Section Description", order=1, course_id=course.id)
        session.add(section)
        session.commit()
        session.refresh(section)

        # 1. Create lesson
        lesson_data = {
            "title": "Test Lesson",
            "content": "Initial content",
            "video_url": "https://example.com/video",
            "order": 1,
            "section_id": section.id,
        }

        # Create client with session override
        client = TestClient(app)
        client.app.dependency_overrides[db_session] = lambda: session
        client.app.dependency_overrides[auth_methods.get_current_user] = lambda: user.id

        create_response = client.post("/lessons/", json=lesson_data)
        assert create_response.status_code == 200
        lesson_id = create_response.json()["id"]

        # 2. Read lesson
        get_response = client.get(f"/lessons/{lesson_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Test Lesson"

        # 3. Update lesson
        update_data = {"title": "Updated Lesson", "content": "Updated content"}
        update_response = client.put(f"/lessons/{lesson_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Lesson"

        # 4. Delete lesson
        delete_response = client.delete(f"/lessons/{lesson_id}")
        assert delete_response.status_code == 200

        # 5. Verify lesson is deleted
        get_deleted_response = client.get(f"/lessons/{lesson_id}")
        assert get_deleted_response.status_code == 404

    def test_lesson_ownership_isolation(self, session: Session):
        """Test that users can only access their own lessons."""
        # Create two users with their own courses, sections, and lessons
        user1 = User(id="user1", email="user1@example.com", name="User 1", password="password123")
        user2 = User(id="user2", email="user2@example.com", name="User 2", password="password456")
        session.add(user1)
        session.add(user2)
        session.commit()

        # User 1's course and section
        course1 = Course(name="Course 1", description="Description 1", user_id=user1.id)
        session.add(course1)
        session.commit()
        session.refresh(course1)

        section1 = Section(name="Section 1", description="Section 1 Description", order=1, course_id=course1.id)
        session.add(section1)
        session.commit()
        session.refresh(section1)

        lesson1 = Lesson(title="Lesson 1", content="Content 1", order=1, section_id=section1.id)
        session.add(lesson1)
        session.commit()
        session.refresh(lesson1)

        # User 2's course and section
        course2 = Course(name="Course 2", description="Description 2", user_id=user2.id)
        session.add(course2)
        session.commit()
        session.refresh(course2)

        section2 = Section(name="Section 2", description="Section 2 Description", order=1, course_id=course2.id)
        session.add(section2)
        session.commit()
        session.refresh(section2)

        lesson2 = Lesson(title="Lesson 2", content="Content 2", order=1, section_id=section2.id)
        session.add(lesson2)
        session.commit()
        session.refresh(lesson2)

        # Test that user1 cannot update user2's lesson
        client1 = TestClient(app)
        client1.app.dependency_overrides[db_session] = lambda: session
        client1.app.dependency_overrides[auth_methods.get_current_user] = lambda: user1.id

        response = client1.put(f"/lessons/{lesson2.id}", json={"title": "Hacked Title"})
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

        # Test that user2 cannot update user1's lesson
        client2 = TestClient(app)
        client2.app.dependency_overrides[db_session] = lambda: session
        client2.app.dependency_overrides[auth_methods.get_current_user] = lambda: user2.id

        response = client2.put(f"/lessons/{lesson1.id}", json={"title": "Hacked Title"})
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_lesson_section_relationship(self, session: Session):
        """Test lesson-section relationship and filtering."""
        # Create user, course, and multiple sections
        user = User(id="user123", email="test8@example.com", name="Test User", password="password123")
        session.add(user)
        session.commit()

        course = Course(name="Test Course", description="Test Description", user_id=user.id)
        session.add(course)
        session.commit()
        session.refresh(course)

        sections = [
            Section(name=f"Section {i}", description=f"Section {i} Description", order=i, course_id=course.id)
            for i in range(1, 4)
        ]
        for section in sections:
            session.add(section)
        session.commit()
        for section in sections:
            session.refresh(section)

        # Create lessons for each section
        for i, section in enumerate(sections):
            for j in range(1, 3):  # 2 lessons per section
                lesson = Lesson(
                    title=f"Section {i + 1} Lesson {j}",
                    content=f"Content for section {i + 1} lesson {j}",
                    order=j,
                    section_id=section.id,
                )
                session.add(lesson)
        session.commit()

        # Create client with session override
        client = TestClient(app)
        client.app.dependency_overrides[db_session] = lambda: session
        client.app.dependency_overrides[auth_methods.get_current_user] = lambda: user.id

        # Test getting all lessons
        all_response = client.get("/lessons/")
        assert all_response.status_code == 200
        assert all_response.json()["total"] == 6  # 3 sections * 2 lessons each

        # Test filtering by each section
        for i, section in enumerate(sections):
            section_response = client.get(f"/lessons/?section_id={section.id}")
            assert section_response.status_code == 200
            data = section_response.json()
            assert data["total"] == 2
            assert len(data["lessons"]) == 2

            # Verify all lessons belong to the correct section
            for lesson in data["lessons"]:
                assert lesson["section_id"] == section.id
                assert f"Section {i + 1}" in lesson["title"]
