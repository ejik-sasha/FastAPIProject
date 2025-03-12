from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Annotated, List

from .. import models, schemas, auth
from ..database import get_db
from ..schemas import UserRole
from ..exceptions import (
    raise_not_found_exception,
    raise_bad_request_exception,
    raise_conflict_exception,
    raise_forbidden_exception
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

db_dependency = Annotated[Session, Depends(get_db)]

# User Registration
@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: db_dependency):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise_conflict_exception("Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Follow User
@router.post("/{user_id}/follow", status_code=204)
def follow_user(
    user_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    user_to_follow = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_follow:
        raise_not_found_exception("User not found")
    if user_to_follow == current_user:
        raise_bad_request_exception("Cannot follow yourself")
    if user_to_follow in current_user.following:
        raise_bad_request_exception("Already following this user")
    current_user.following.append(user_to_follow)
    db.commit()
    return

# Unfollow User
@router.post("/{user_id}/unfollow", status_code=204)
def unfollow_user(
    user_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    user_to_unfollow = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_unfollow:
        raise_not_found_exception("User not found")
    if user_to_unfollow == current_user:
        raise_bad_request_exception("Cannot unfollow yourself")
    if user_to_unfollow not in current_user.following:
        raise_bad_request_exception("Not following this user")
    current_user.following.remove(user_to_unfollow)
    db.commit()
    return

@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    check_admin(current_user)
    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_delete:
        raise_not_found_exception("User not found")
    db.delete(user_to_delete)
    db.commit()
    return

#@router.get("/", response_model=List[schemas.User])
#def get_all_users(
#    db: db_dependency,
#    current_user: models.User = Depends(auth.get_current_user),
#):
#    check_admin(current_user)
#    users = db.query(models.User).all()
#    return users

@router.get("/", response_model=List[schemas.User])
def get_all_users(db: db_dependency):
    users = db.query(models.User).all()
    return users

@router.put("/{user_id}/role", response_model=schemas.User)
def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: db_dependency,
    current_user: models.User = Depends(auth.get_current_user),
):
    check_admin(current_user)  # Проверка, что пользователь — админ
    user_to_update = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_update:
        raise_not_found_exception("User not found")
    user_to_update.role = new_role
    db.commit()
    db.refresh(user_to_update)
    return user_to_update

def check_admin(current_user: models.User):
    if current_user.role != models.UserRole.ADMIN:
        raise_forbidden_exception("You do not have permission to perform this action")