from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.models.engine import db_session
from backend.modules.auth.auth_methods import get_current_user
from backend.modules.users.user_methods import (
    ban_user,
    create_user,
    delete_user,
    get_user_by_id,
    get_users,
    unban_user,
    update_user,
    user_to_response,
)
from backend.modules.users.user_schema import (
    UserBanRequest,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post("/", response_model=UserResponse)
async def create_new_user(
    user_data: UserCreate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Create a new user. Only admins can create users."""
    try:
        # Check if current user is admin
        current_user_obj = get_user_by_id(session, current_user)
        if not current_user_obj or current_user_obj.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can create users")

        user = create_user(session, user_data)
        return user_to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@user_router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    include_deleted: bool = Query(False),
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Get a list of users with optional filtering and search. Only admins can access this."""
    try:
        # Check if current user is admin
        current_user_obj = get_user_by_id(session, current_user)
        if not current_user_obj or current_user_obj.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can list users")

        users, total = get_users(
            session=session,
            skip=skip,
            limit=limit,
            search_query=search,
            role=role,
            include_deleted=include_deleted
        )

        user_responses = [user_to_response(user) for user in users]

        return UserListResponse(
            users=user_responses,
            total=total,
            page=(skip // limit) + 1,
            per_page=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Get a user by ID. Users can only access their own profile unless they are admin."""
    try:
        # Check if current user is admin or accessing their own profile
        current_user_obj = get_user_by_id(session, current_user)
        if not current_user_obj:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if user_id != current_user and current_user_obj.role != "admin":
            raise HTTPException(status_code=403, detail="Permission denied")

        user = get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user_to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@user_router.patch("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: str,
    user_data: UserUpdate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Update a user. Users can only update their own profile unless they are admin."""
    try:
        user = update_user(session, user_id, user_data, current_user)
        return user_to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@user_router.delete("/{user_id}")
async def delete_user_endpoint(
    user_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Delete a user. Only admins can delete users."""
    try:
        success = delete_user(session, user_id, current_user)
        if success:
            return {"message": "User deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete user")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@user_router.post("/{user_id}/ban", response_model=UserResponse)
async def ban_user_endpoint(
    user_id: str,
    ban_request: UserBanRequest,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Ban a user. Only admins can ban users."""
    try:
        user = ban_user(session, user_id, current_user, ban_request.reason)
        return user_to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@user_router.post("/{user_id}/unban", response_model=UserResponse)
async def unban_user_endpoint(
    user_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user)
):
    """Unban a user. Only admins can unban users."""
    try:
        user = unban_user(session, user_id, current_user)
        return user_to_response(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
