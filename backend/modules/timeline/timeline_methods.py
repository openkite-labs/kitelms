from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlmodel import Session, func, select

from backend.models.database import Comment, Post, User
from backend.modules.timeline.timeline_schema import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    PostCreate,
    PostResponse,
    PostUpdate,
)


def create_post(session: Session, post_data: PostCreate, user_id: str) -> Post:
    """
    Create a new post.
    """
    post = Post(
        content=post_data.content,
        image_url=post_data.image_url or "",
        user_id=user_id,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


def get_posts(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    include_user_info: bool = False,
    include_comments: bool = False,
) -> Tuple[List[Post], int]:
    """
    Get posts with pagination and optional user info and comments.
    """
    # Get total count
    total_query = select(func.count(Post.id)).where(Post.is_deleted == False)
    total = session.exec(total_query).one()

    # Get posts with optional user join
    query = select(Post).where(Post.is_deleted == False)

    if include_user_info:
        query = query.join(User)

    query = query.order_by(Post.created_at.desc()).offset(skip).limit(limit)
    posts = session.exec(query).all()

    # Load user info if requested
    if include_user_info:
        for post in posts:
            if not hasattr(post, "user") or post.user is None:
                user = session.get(User, post.user_id)
                post.user = user

    # Load comments if requested
    if include_comments:
        for post in posts:
            comments_query = (
                select(Comment)
                .where(Comment.post_id == post.id, Comment.is_deleted == False)
                .order_by(Comment.created_at.asc())
            )
            post.comments = session.exec(comments_query).all()

    return posts, total


def get_post_by_id(session: Session, post_id: str) -> Optional[Post]:
    """
    Get a post by ID.
    """
    query = select(Post).where(Post.id == post_id, Post.is_deleted == False)
    return session.exec(query).first()


def update_post(session: Session, post_id: str, post_data: PostUpdate, user_id: str) -> Post:
    """
    Update a post. Only the owner can update their post.
    """
    post = get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")

    if post_data.content is not None:
        post.content = post_data.content
    if post_data.image_url is not None:
        post.image_url = post_data.image_url

    post.updated_at = datetime.now()
    session.add(post)
    session.commit()
    session.refresh(post)
    return post


def delete_post(session: Session, post_id: str, user_id: str) -> bool:
    """
    Soft delete a post. Only the owner can delete their post.
    """
    post = get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    post.is_deleted = True
    post.updated_at = datetime.now()
    session.add(post)
    session.commit()
    return True


def create_comment(session: Session, comment_data: CommentCreate, user_id: str) -> Comment:
    """
    Create a new comment on a post.
    """
    # Verify post exists
    post = get_post_by_id(session, comment_data.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment(
        content=comment_data.content,
        post_id=comment_data.post_id,
        user_id=user_id,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def get_comments(
    session: Session,
    skip: int = 0,
    limit: int = 10,
    post_id: Optional[str] = None,
    include_user_info: bool = False,
) -> Tuple[List[Comment], int]:
    """
    Get comments with pagination and optional filtering by post_id.
    """
    # Build query conditions
    conditions = [Comment.is_deleted == False]
    if post_id:
        conditions.append(Comment.post_id == post_id)

    # Get total count
    total_query = select(func.count(Comment.id)).where(*conditions)
    total = session.exec(total_query).one()

    # Get comments
    query = select(Comment).where(*conditions)

    if include_user_info:
        query = query.join(User)

    query = query.order_by(Comment.created_at.asc()).offset(skip).limit(limit)
    comments = session.exec(query).all()

    # Load user info if requested
    if include_user_info:
        for comment in comments:
            if not hasattr(comment, "user") or comment.user is None:
                user = session.get(User, comment.user_id)
                comment.user = user

    return comments, total


def get_comment_by_id(session: Session, comment_id: str) -> Optional[Comment]:
    """
    Get a comment by ID.
    """
    query = select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)
    return session.exec(query).first()


def update_comment(session: Session, comment_id: str, comment_data: CommentUpdate, user_id: str) -> Comment:
    """
    Update a comment. Only the owner can update their comment.
    """
    comment = get_comment_by_id(session, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this comment")

    if comment_data.content is not None:
        comment.content = comment_data.content

    comment.updated_at = datetime.now()
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def delete_comment(session: Session, comment_id: str, user_id: str) -> bool:
    """
    Soft delete a comment. Only the owner can delete their comment.
    """
    comment = get_comment_by_id(session, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    comment.is_deleted = True
    comment.updated_at = datetime.now()
    session.add(comment)
    session.commit()
    return True


def post_to_response(post: Post, include_user_info: bool = False, include_comments: bool = False) -> PostResponse:
    """
    Convert a Post model to PostResponse.
    """
    response_data = {
        "id": post.id,
        "content": post.content,
        "image_url": post.image_url,
        "user_id": post.user_id,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
    }

    if include_user_info and hasattr(post, "user") and post.user:
        response_data["user_name"] = post.user.name
        response_data["user_email"] = post.user.email

    if include_comments and hasattr(post, "comments"):
        response_data["comments"] = [comment_to_response(comment, include_user_info) for comment in post.comments]
        response_data["comments_count"] = len(post.comments)

    return PostResponse(**response_data)


def comment_to_response(comment: Comment, include_user_info: bool = False) -> CommentResponse:
    """
    Convert a Comment model to CommentResponse.
    """
    response_data = {
        "id": comment.id,
        "content": comment.content,
        "post_id": comment.post_id,
        "user_id": comment.user_id,
        "created_at": comment.created_at.isoformat(),
        "updated_at": comment.updated_at.isoformat(),
    }

    if include_user_info and hasattr(comment, "user") and comment.user:
        response_data["user_name"] = comment.user.name
        response_data["user_email"] = comment.user.email

    return CommentResponse(**response_data)
