from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Annotated
from datetime import timedelta, datetime, timezone
from app.exceptions import (
    raise_not_found_exception,
    raise_forbidden_exception,
)

from .. import models, schemas, auth
from ..database import get_db
from app.utils.notifications import send_notification

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

db_dependency = Annotated[Session, Depends(get_db)]

# Get Posts
@router.get("/", response_model=List[schemas.Post])
def read_posts(db: db_dependency, skip: int = 0, limit: int = 10):
    posts = db.query(models.Post).order_by(models.Post.timestamp.desc()).offset(skip).limit(limit).all()
    return posts

# Create New Post
@router.post("/", response_model=schemas.Post)
def create_new_post(
    post: schemas.PostCreate,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    db_post = models.Post(content=post.content, owner_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    send_notification("new_post", {"post_id": db_post.id, "user_id": current_user.id})

    return db_post

# Delete Existing Post
@router.delete("/{post_id}", status_code=204)
def delete_existing_post(
    post_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None or post.owner_id != current_user.id:
        raise_not_found_exception('Post not found')
    db.delete(post)
    db.commit()
    return

# Update Post
@router.put("/{post_id}", response_model=schemas.Post)
def update_post(
    post_id: int,
    post_update: schemas.PostUpdate,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise_not_found_exception('Post not found')
    if post.owner_id != current_user.id:
        raise_forbidden_exception('Not authorized to edit this post')

    # Check if the post is within the 10-minute edit window
    post_timestamp_aware = post.timestamp.replace(tzinfo=timezone.utc)
    time_since_creation = datetime.now(timezone.utc) - post_timestamp_aware
    if time_since_creation > timedelta(minutes=10):
        raise_not_found_exception("You can only edit a post within 10 minutes of its creation")
    post.content = post_update.content
    db.add(post)
    db.commit()
    return post

# Like Post
@router.post("/{post_id}/like", status_code=204)
def like_post(
    post_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise_not_found_exception('Post not found')
    like = db.query(models.Like).filter_by(user_id=current_user.id, post_id=post_id).first()
    if like:
        raise_not_found_exception("Already liked")
    new_like = models.Like(user_id=current_user.id, post_id=post_id)
    db.add(new_like)
    db.commit()
    send_notification("like", {"post_id": post_id, "user_id": current_user.id})
    return

# Unlike Post
@router.post("/{post_id}/unlike", status_code=204)
def unlike_post(
    post_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    like = db.query(models.Like).filter_by(user_id=current_user.id, post_id=post_id).first()
    if not like:
        raise_not_found_exception("Not liked yet")
    db.delete(like)
    db.commit()
    return

# Retweet Post
@router.post("/{post_id}/retweet", status_code=204)
def retweet_post(
    post_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise_not_found_exception('Post not found')
    retweet = db.query(models.Retweet).filter_by(user_id=current_user.id, post_id=post_id).first()
    if retweet:
        raise_not_found_exception("Already retweeted")
    new_retweet = models.Retweet(user_id=current_user.id, post_id=post_id)
    db.add(new_retweet)
    db.commit()
    send_notification("retweet", {"post_id": post_id, "user_id": current_user.id})
    return

# Unretweet
@router.post("/{post_id}/unretweet", status_code=204)
def unretweet_post(
    post_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    retweet = db.query(models.Retweet).filter_by(user_id=current_user.id, post_id=post_id).first()
    if not retweet:
        raise_not_found_exception("Not retweeted yet")
    db.delete(retweet)
    db.commit()
    return

# Get Posts with Counts
@router.get("/with_counts/", response_model=List[schemas.PostWithCounts])
def read_posts_with_counts(db: db_dependency):
    likes_subq = (
        db.query(
            models.Like.post_id,
            func.count(models.Like.user_id).label('likes_count')
        )
        .group_by(models.Like.post_id)
        .subquery()
    )

    retweets_subq = (
        db.query(
            models.Retweet.post_id,
            func.count(models.Retweet.user_id).label('retweets_count')
        )
        .group_by(models.Retweet.post_id)
        .subquery()
    )

    posts = (
        db.query(
            models.Post,
            models.User.username.label('owner_username'),
            func.coalesce(likes_subq.c.likes_count, 0).label('likes_count'),
            func.coalesce(retweets_subq.c.retweets_count, 0).label('retweets_count')
        )
        .join(models.User, models.Post.owner_id == models.User.id)
        .outerjoin(likes_subq, models.Post.id == likes_subq.c.post_id)
        .outerjoin(retweets_subq, models.Post.id == retweets_subq.c.post_id)
        .order_by(models.Post.timestamp.desc())
        .all()
    )


    response_posts = []
    for post, owner_username, likes_count, retweets_count in posts:
        response_posts.append(schemas.PostWithCounts(
            id=post.id,
            content=post.content,
            timestamp=post.timestamp,
            owner_id=post.owner_id,
            owner_username=owner_username,
            likes_count=likes_count,
            retweets_count=retweets_count
        ))

    return response_posts