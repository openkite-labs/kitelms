from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, func, select

from backend.models.database import User
from backend.modules.users.user_schema import UserResponse, UserUpdate


def user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse schema."""
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
        is_deleted=user.is_deleted
    )


def get_user_by_id(session: Session, user_id: str) -> Optional[User]:
    """
    Get a user by ID.
    """
    user = session.exec(select(User).where(User.id == user_id, User.is_deleted == False)).first()
    return user


def get_users(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    search_query: Optional[str] = None,
    role: Optional[str] = None,
    include_deleted: bool = False
) -> tuple[list[User], int]:
    """
    Get a list of users with optional filtering and search.
    """
    query = select(User)

    # Filter by deletion status
    if not include_deleted:
        query = query.where(User.is_deleted == False)

    # Filter by role
    if role:
        query = query.where(User.role == role)

    # Search functionality
    if search_query:
        search_filter = (
            User.name.contains(search_query) |
            User.email.contains(search_query)
        )
        query = query.where(search_filter)

    # Get total count
    total_query = select(func.count(User.id))
    if not include_deleted:
        total_query = total_query.where(User.is_deleted == False)
    if role:
        total_query = total_query.where(User.role == role)
    if search_query:
        total_query = total_query.where(search_filter)

    total = session.exec(total_query).one()

    # Apply pagination
    query = query.offset(skip).limit(limit)
    users = session.exec(query).all()

    return users, total


def update_user(
    session: Session,
    user_id: str,
    user_data: UserUpdate,
    current_user_id: str
) -> Optional[User]:
    """
    Update a user. Users can only update their own profile unless they are admin.
    """
    user = get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get current user to check permissions
    current_user = get_user_by_id(session, current_user_id)
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Check if user can update this profile
    if user_id != current_user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    # Update fields
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.email is not None:
        # Check if new email already exists
        existing_user = session.exec(
            select(User).where(User.email == user_data.email, User.id != user_id, User.is_deleted == False)
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = user_data.email
    if user_data.password is not None:
        user.password = user_data.password  # Note: In production, hash the password
    if user_data.role is not None and current_user.role == "admin":
        user.role = user_data.role

    user.updated_at = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, user_id: str, current_user_id: str) -> bool:
    """
    Soft delete a user. Only admins can delete users.
    """
    user = get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get current user to check permissions
    current_user = get_user_by_id(session, current_user_id)
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    # Prevent self-deletion
    if user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user.is_deleted = True
    user.updated_at = datetime.now()
    session.add(user)
    session.commit()
    return True


def ban_user(session: Session, user_id: str, current_user_id: str, reason: Optional[str] = None) -> User:
    """
    Ban a user by setting is_deleted to True. Only admins can ban users.
    """
    user = get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get current user to check permissions
    current_user = get_user_by_id(session, current_user_id)
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can ban users")

    # Prevent self-banning
    if user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Cannot ban your own account")

    if user.is_deleted:
        raise HTTPException(status_code=400, detail="User is already banned")

    user.is_deleted = True
    user.updated_at = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def unban_user(session: Session, user_id: str, current_user_id: str) -> User:
    """
    Unban a user by setting is_deleted to False. Only admins can unban users.
    """
    # Get user even if deleted
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get current user to check permissions
    current_user = get_user_by_id(session, current_user_id)
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can unban users")

    if not user.is_deleted:
        raise HTTPException(status_code=400, detail="User is not banned")

    user.is_deleted = False
    user.updated_at = datetime.now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    """
    user = session.exec(select(User).where(User.email == email, User.is_deleted == False)).first()
    return user
