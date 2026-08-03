import hashlib
import secrets

from fastapi import Cookie, Depends, HTTPException, status
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

_serializer = URLSafeTimedSerializer(settings.secret_key, salt="iqc-session")
SESSION_MAX_AGE = 60 * 60 * 12  # 12 小時


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, _digest = stored.split("$", 1)
    return secrets.compare_digest(hash_password(password, salt), stored)


def create_session_token(user_id: int) -> str:
    return _serializer.dumps({"uid": user_id})


def get_current_user(
    session: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登入")
    try:
        data = _serializer.loads(session, max_age=SESSION_MAX_AGE)
    except BadSignature:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登入已失效,請重新登入") from None
    user = db.get(User, data["uid"])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "帳號不存在")
    return user


def require_supervisor(user: User = Depends(get_current_user)) -> User:
    if user.role != "supervisor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要主管權限")
    return user
