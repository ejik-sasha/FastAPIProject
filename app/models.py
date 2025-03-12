from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum

Follow = Table(
    'follows',
    Base.metadata,
    Column('follower_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('followee_id', Integer, ForeignKey('users.id'), primary_key=True),
)



class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER)

    posts = relationship('Post', back_populates='owner')
    followers = relationship(
        'User',
        secondary=Follow,
        primaryjoin=id == Follow.c.followee_id,
        secondaryjoin=id == Follow.c.follower_id,
        backref='following',
    )




class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(280), nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    owner = relationship('User', back_populates='posts')
    likes = relationship('Like', back_populates='post')
    retweets = relationship('Retweet', back_populates='post')

class Like(Base):
    __tablename__ = 'likes'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), primary_key=True)

    user = relationship('User')
    post = relationship('Post', back_populates='likes')

class Retweet(Base):
    __tablename__ = 'retweets'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), primary_key=True)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    user = relationship('User')
    post = relationship('Post', back_populates='retweets')