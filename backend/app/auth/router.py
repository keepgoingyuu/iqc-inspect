from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.service import (
    SESSION_MAX_AGE,
    create_session_token,
    get_current_user,
    verify_password,
)
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.username == body.username))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "帳號或密碼錯誤")
    response.set_cookie(
        "session",
        create_session_token(user.id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return user


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie("session")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
