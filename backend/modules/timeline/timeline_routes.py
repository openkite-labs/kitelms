from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from backend.models.engine import db_session
from backend.modules.auth.auth_methods import get_current_user
from backend.modules.timeline.timeline_methods import (
    comment_to_response,
    create_comment,
    create_post,
    delete_comment,
    delete_post,
    get_comment_by_id,
    get_comments,
    get_post_by_id,
    get_posts,
    post_to_response,
    update_comment,
    update_post,
)
from backend.modules.timeline.timeline_schema import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
    CommentUpdate,
    PostCreate,
    PostListResponse,
    PostResponse,
    PostUpdate,
)

timeline_router = APIRouter(prefix="/timeline", tags=["timeline"])


# Post endpoints
@timeline_router.post("/posts", response_model=PostResponse)
def create_post_endpoint(
    post_data: PostCreate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user),
):
    """
    Create a new post in the timeline.
    """
    try:
        post = create_post(session, post_data, current_user)
        return post_to_response(post)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@timeline_router.get("/posts", response_model=PostListResponse)
def get_posts_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    include_user_info: bool = Query(True),
    include_comments: bool = Query(False),
    session: Session = Depends(db_session),
):
    """
    Get posts from the timeline with pagination.
    """
    try:
        posts, total = get_posts(session, skip, limit, include_user_info, include_comments)
        return PostListResponse(
            posts=[post_to_response(p, include_user_info, include_comments) for p in posts],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@timeline_router.get("/posts/{post_id}", response_model=PostResponse)
def get_post_endpoint(
    post_id: str,
    include_user_info: bool = Query(True),
    include_comments: bool = Query(True),
    session: Session = Depends(db_session),
):
    """
    Get a specific post by ID with optional comments.
    """
    post = get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Load comments if requested
    if include_comments:
        comments, _ = get_comments(session, post_id=post_id, include_user_info=include_user_info)
        post.comments = comments

    return post_to_response(post, include_user_info, include_comments)


@timeline_router.put("/posts/{post_id}", response_model=PostResponse)
def update_post_endpoint(
    post_id: str,
    post_data: PostUpdate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user),
):
    """
    Update a post. Only the owner can update their post.
    """
    try:
        post = update_post(session, post_id, post_data, current_user)
        return post_to_response(post)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@timeline_router.delete("/posts/{post_id}")
def delete_post_endpoint(
    post_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user),
):
    """
    Delete a post. Only the owner can delete their post.
    """
    try:
        success = delete_post(session, post_id, current_user)
        if success:
            return {"message": "Post deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete post")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Comment endpoints
@timeline_router.post("/comments", response_model=CommentResponse)
def create_comment_endpoint(
    comment_data: CommentCreate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user),
):
    """
    Create a new comment on a post.
    """
    try:
        comment = create_comment(session, comment_data, current_user)
        return comment_to_response(comment)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@timeline_router.get("/comments", response_model=CommentListResponse)
def get_comments_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    post_id: Optional[str] = Query(None),
    include_user_info: bool = Query(True),
    session: Session = Depends(db_session),
):
    """
    Get comments with optional filtering by post_id.
    """
    try:
        comments, total = get_comments(session, skip, limit, post_id, include_user_info)
        return CommentListResponse(
            comments=[comment_to_response(c, include_user_info) for c in comments],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@timeline_router.get("/comments/{comment_id}", response_model=CommentResponse)
def get_comment_endpoint(
    comment_id: str,
    include_user_info: bool = Query(True),
    session: Session = Depends(db_session),
):
    """
    Get a specific comment by ID.
    """
    comment = get_comment_by_id(session, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment_to_response(comment, include_user_info)


@timeline_router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment_endpoint(
    comment_id: str,
    comment_data: CommentUpdate,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user),
):
    """
    Update a comment. Only the owner can update their comment.
    """
    try:
        comment = update_comment(session, comment_id, comment_data, current_user)
        return comment_to_response(comment)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@timeline_router.delete("/comments/{comment_id}")
def delete_comment_endpoint(
    comment_id: str,
    session: Session = Depends(db_session),
    current_user: str = Depends(get_current_user),
):
    """
    Delete a comment. Only the owner can delete their comment.
    """
    try:
        success = delete_comment(session, comment_id, current_user)
        if success:
            return {"message": "Comment deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete comment")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
