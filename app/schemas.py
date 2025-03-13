from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

#User

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.USER

class User(UserBase):
    id: int
    created_at: datetime
    role: UserRole

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    user: User
    access_token: str
    token_type: str


#Token

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

#Post

class PostBase(BaseModel):
    content: str

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    timestamp: datetime
    owner_id: int

class PostWithCounts(Post):
    likes_count: int
    retweets_count: int
    owner_username: str

class PostUpdate(BaseModel):
    content: str

    class Config:
        from_attributes = True

#Like

class Like(BaseModel):
    user_id: int
    post_id: int

    class Config:
        from_attributes = True

#Retweet

class Retweet(BaseModel):
    user_id: int
    post_id: int

    class Config:
        from_attributes = True