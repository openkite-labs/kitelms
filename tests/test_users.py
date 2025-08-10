from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.models.database import RoleEnum, User
from backend.modules.auth import auth_methods


class TestListUsers:
    """Test cases for GET /users/ endpoint"""

    def test_list_users_as_admin_success(self, session: Session):
        """Test successful user listing by admin"""
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        session.add(admin_user)

        # Create regular users
        user1 = User(
            name="User One",
            email="user1@example.com",
            password=auth_methods.hash_password("password1"),
            role=RoleEnum.USER,
        )
        user2 = User(
            name="User Two",
            email="user2@example.com",
            password=auth_methods.hash_password("password2"),
            role=RoleEnum.USER,
        )
        session.add_all([user1, user2])
        session.commit()
        session.refresh(admin_user)

        # Create authenticated client with admin user
        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get("/users/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert data["total"] == 3  # admin + 2 regular users
        assert len(data["users"]) == 3

        app.dependency_overrides.clear()

    def test_list_users_as_regular_user_forbidden(self, session: Session):
        """Test that regular users cannot list users"""
        # Create regular user
        user = User(
            name="Regular User",
            email="user@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get("/users/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Only admins can list users" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_list_users_with_pagination(self, session: Session):
        """Test user listing with pagination parameters"""
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        session.add(admin_user)

        # Create multiple users
        for i in range(5):
            user = User(
                name=f"User {i}",
                email=f"user{i}@example.com",
                password=auth_methods.hash_password(f"password{i}"),
                role=RoleEnum.USER,
            )
            session.add(user)

        session.commit()
        session.refresh(admin_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get("/users/?skip=0&limit=3")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 6  # admin + 5 regular users
        assert len(data["users"]) == 3
        assert data["page"] == 1
        assert data["per_page"] == 3

        app.dependency_overrides.clear()

    def test_list_users_with_search(self, session: Session):
        """Test user listing with search functionality"""
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        session.add(admin_user)

        # Create users with specific names
        user1 = User(
            name="John Doe",
            email="john@example.com",
            password=auth_methods.hash_password("password1"),
            role=RoleEnum.USER,
        )
        user2 = User(
            name="Jane Smith",
            email="jane@example.com",
            password=auth_methods.hash_password("password2"),
            role=RoleEnum.USER,
        )
        session.add_all([user1, user2])
        session.commit()
        session.refresh(admin_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get("/users/?search=John")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["users"]) == 1
        assert data["users"][0]["name"] == "John Doe"

        app.dependency_overrides.clear()


class TestGetCurrentUserProfile:
    """Test cases for GET /users/me endpoint"""

    def test_get_current_user_profile_success(self, session: Session):
        """Test successful retrieval of current user profile"""
        user = User(
            name="Test User",
            email="test@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get("/users/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == user.id
        assert data["name"] == user.name
        assert data["email"] == user.email
        assert data["role"] == user.role.value
        assert "created_at" in data
        assert "updated_at" in data

        app.dependency_overrides.clear()

    def test_get_current_user_profile_user_not_found(self, session: Session):
        """Test current user profile when user doesn't exist"""
        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return "nonexistent-id"

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get("/users/me")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

        app.dependency_overrides.clear()


class TestGetUserById:
    """Test cases for GET /users/{user_id} endpoint"""

    def test_get_user_by_id_own_profile(self, session: Session):
        """Test user accessing their own profile"""
        user = User(
            name="Test User",
            email="test@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get(f"/users/{user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == user.id
        assert data["name"] == user.name

        app.dependency_overrides.clear()

    def test_get_user_by_id_as_admin(self, session: Session):
        """Test admin accessing another user's profile"""
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        target_user = User(
            name="Target User",
            email="target@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add_all([admin_user, target_user])
        session.commit()
        session.refresh(admin_user)
        session.refresh(target_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get(f"/users/{target_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == target_user.id
        assert data["name"] == target_user.name

        app.dependency_overrides.clear()

    def test_get_user_by_id_permission_denied(self, session: Session):
        """Test regular user trying to access another user's profile"""
        user1 = User(
            name="User One",
            email="user1@example.com",
            password=auth_methods.hash_password("password1"),
            role=RoleEnum.USER,
        )
        user2 = User(
            name="User Two",
            email="user2@example.com",
            password=auth_methods.hash_password("password2"),
            role=RoleEnum.USER,
        )
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user1.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get(f"/users/{user2.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Permission denied" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_get_user_by_id_not_found(self, session: Session):
        """Test accessing non-existent user as regular user (should get permission denied)"""
        user = User(
            name="Test User",
            email="test@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get("/users/nonexistent-id")

        # Regular user trying to access another user's profile gets permission denied
        # even if the target user doesn't exist
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Permission denied" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_get_user_by_id_not_found_as_admin(self, session: Session):
        """Test admin accessing non-existent user (should get user not found)"""
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.get("/users/nonexistent-id")

        # Admin should get user not found when accessing non-existent user
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

        app.dependency_overrides.clear()


class TestUpdateUser:
    """Test cases for PATCH /users/{user_id} endpoint"""

    def test_update_own_profile_success(self, session: Session):
        """Test user updating their own profile"""
        user = User(
            name="Original Name",
            email="original@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        update_data = {"name": "Updated Name", "email": "updated@example.com"}
        response = client.patch(f"/users/{user.id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "updated@example.com"

        app.dependency_overrides.clear()

    def test_update_user_as_admin(self, session: Session):
        """Test admin updating another user's profile"""
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        target_user = User(
            name="Target User",
            email="target@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add_all([admin_user, target_user])
        session.commit()
        session.refresh(admin_user)
        session.refresh(target_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        update_data = {"name": "Updated by Admin", "role": "admin"}
        response = client.patch(f"/users/{target_user.id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated by Admin"
        assert data["role"] == "admin"

        app.dependency_overrides.clear()

    def test_update_user_duplicate_email(self, session: Session):
        """Test updating user with duplicate email"""
        user1 = User(
            name="User One",
            email="user1@example.com",
            password=auth_methods.hash_password("password1"),
            role=RoleEnum.USER,
        )
        user2 = User(
            name="User Two",
            email="user2@example.com",
            password=auth_methods.hash_password("password2"),
            role=RoleEnum.USER,
        )
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user1.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        update_data = {"email": "user2@example.com"}  # Duplicate email
        response = client.patch(f"/users/{user1.id}", json=update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

        app.dependency_overrides.clear()


class TestDeleteUser:
    """Test cases for DELETE /users/{user_id} endpoint"""

    def test_delete_user_as_admin_success(self, session: Session):
        """Test admin successfully deleting a user"""
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        target_user = User(
            name="Target User",
            email="target@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add_all([admin_user, target_user])
        session.commit()
        session.refresh(admin_user)
        session.refresh(target_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.delete(f"/users/{target_user.id}")

        assert response.status_code == status.HTTP_200_OK
        assert "User deleted successfully" in response.json()["message"]

        app.dependency_overrides.clear()

    def test_delete_user_as_regular_user_forbidden(self, session: Session):
        """Test regular user trying to delete another user"""
        user1 = User(
            name="User One",
            email="user1@example.com",
            password=auth_methods.hash_password("password1"),
            role=RoleEnum.USER,
        )
        user2 = User(
            name="User Two",
            email="user2@example.com",
            password=auth_methods.hash_password("password2"),
            role=RoleEnum.USER,
        )
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user1.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.delete(f"/users/{user2.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Only admins can delete users" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_delete_user_self_deletion_forbidden(self, session: Session):
        """Test admin trying to delete their own account"""
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.delete(f"/users/{admin_user.id}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot delete your own account" in response.json()["detail"]

        app.dependency_overrides.clear()


class TestBanUser:
    """Test cases for POST /users/{user_id}/ban endpoint"""

    def test_ban_user_as_admin_success(self, session: Session):
        """Test admin successfully banning a user"""
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        target_user = User(
            name="Target User",
            email="target@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add_all([admin_user, target_user])
        session.commit()
        session.refresh(admin_user)
        session.refresh(target_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        ban_data = {"reason": "Violation of terms"}
        response = client.post(f"/users/{target_user.id}/ban", json=ban_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_deleted"] == True

        app.dependency_overrides.clear()

    def test_ban_user_as_regular_user_forbidden(self, session: Session):
        """Test regular user trying to ban another user"""
        user1 = User(
            name="User One",
            email="user1@example.com",
            password=auth_methods.hash_password("password1"),
            role=RoleEnum.USER,
        )
        user2 = User(
            name="User Two",
            email="user2@example.com",
            password=auth_methods.hash_password("password2"),
            role=RoleEnum.USER,
        )
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user1.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        ban_data = {"reason": "Some reason"}
        response = client.post(f"/users/{user2.id}/ban", json=ban_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Only admins can ban users" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_ban_user_self_ban_forbidden(self, session: Session):
        """Test admin trying to ban themselves"""
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        ban_data = {"reason": "Self ban"}
        response = client.post(f"/users/{admin_user.id}/ban", json=ban_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot ban your own account" in response.json()["detail"]

        app.dependency_overrides.clear()


class TestUnbanUser:
    """Test cases for POST /users/{user_id}/unban endpoint"""

    def test_unban_user_as_admin_success(self, session: Session):
        """Test admin successfully unbanning a user"""
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        banned_user = User(
            name="Banned User",
            email="banned@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
            is_deleted=True,  # Already banned
        )
        session.add_all([admin_user, banned_user])
        session.commit()
        session.refresh(admin_user)
        session.refresh(banned_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.post(f"/users/{banned_user.id}/unban")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_deleted"] == False

        app.dependency_overrides.clear()

    def test_unban_user_as_regular_user_forbidden(self, session: Session):
        """Test regular user trying to unban another user"""
        user = User(
            name="Regular User",
            email="user@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        banned_user = User(
            name="Banned User",
            email="banned@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
            is_deleted=True,
        )
        session.add_all([user, banned_user])
        session.commit()
        session.refresh(user)
        session.refresh(banned_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.post(f"/users/{banned_user.id}/unban")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Only admins can unban users" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_unban_user_not_banned(self, session: Session):
        """Test unbanning a user who is not banned"""
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        regular_user = User(
            name="Regular User",
            email="regular@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
            is_deleted=False,  # Not banned
        )
        session.add_all([admin_user, regular_user])
        session.commit()
        session.refresh(admin_user)
        session.refresh(regular_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)
        response = client.post(f"/users/{regular_user.id}/unban")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "User is not banned" in response.json()["detail"]

        app.dependency_overrides.clear()


class TestUserIntegration:
    """Integration tests for user endpoints"""

    def test_complete_user_lifecycle(self, session: Session):
        """Test complete user lifecycle: create, update, ban, unban, delete"""
        # Create admin user
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=auth_methods.hash_password("adminpass"),
            role=RoleEnum.ADMIN,
        )
        # Create target user
        target_user = User(
            name="Target User",
            email="target@example.com",
            password=auth_methods.hash_password("password"),
            role=RoleEnum.USER,
        )
        session.add_all([admin_user, target_user])
        session.commit()
        session.refresh(admin_user)
        session.refresh(target_user)

        from backend.main import app
        from backend.models.engine import db_session

        def get_session_override():
            return session

        def get_current_user_override():
            return admin_user.id

        app.dependency_overrides[db_session] = get_session_override
        app.dependency_overrides[auth_methods.get_current_user] = get_current_user_override

        client = TestClient(app)

        # 1. Get user profile
        response = client.get(f"/users/{target_user.id}")
        assert response.status_code == status.HTTP_200_OK

        # 2. Update user
        update_data = {"name": "Updated Target User"}
        response = client.patch(f"/users/{target_user.id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated Target User"

        # 3. Ban user
        ban_data = {"reason": "Test ban"}
        response = client.post(f"/users/{target_user.id}/ban", json=ban_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_deleted"] == True

        # 4. Unban user
        response = client.post(f"/users/{target_user.id}/unban")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_deleted"] == False

        # 5. Delete user
        response = client.delete(f"/users/{target_user.id}")
        assert response.status_code == status.HTTP_200_OK
        assert "User deleted successfully" in response.json()["message"]

        app.dependency_overrides.clear()
