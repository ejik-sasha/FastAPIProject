from fastapi import FastAPI
from pydantic_settings import BaseSettings

from .database import engine
from .models import Base
from app.routes import users, auth, posts

class Settings(BaseSettings):
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    class Config:
        env_file = ".env"

settings = Settings()


Base.metadata.create_all(bind=engine)
app = FastAPI()


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(posts.router)

