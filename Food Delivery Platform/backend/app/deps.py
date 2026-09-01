from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import models
from .db import get_db
from .security import decode_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "未登录")
    try:
        payload = decode_token(auth[7:])
    except Exception:
        raise HTTPException(401, "登录已过期，请重新登录")
    if payload.get("type") != "access":
        raise HTTPException(401, "无效令牌")
    user = db.get(models.User, int(payload["sub"]))
    if not user or user.status != 1:
        raise HTTPException(401, "账号不可用")
    return user


def require_roles(*roles):
    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in roles:
            raise HTTPException(403, "无权限访问")
        return user
    return checker
