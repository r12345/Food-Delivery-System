from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..deps import get_current_user
from ..security import (check_captcha, create_token, decode_token,
                        hash_password, make_captcha, verify_password)

router = APIRouter(prefix="/auth", tags=["认证"])


def _user_info(db: Session, user: models.User) -> dict:
    shop = db.query(models.Shop).filter_by(owner_id=user.id).first() if user.role == "merchant" else None
    return {
        "id": user.id, "username": user.username, "nickname": user.nickname,
        "phone": user.phone, "email": user.email, "avatar": user.avatar,
        "role": user.role,
        "shop_id": shop.id if shop else 0,
        "shop_status": shop.status if shop else "",
    }


class RegisterIn(BaseModel):
    username: str
    password: str
    phone: str = ""
    nickname: str = ""
    role: str = "user"
    shop_name: str = ""


class LoginIn(BaseModel):
    username: str
    password: str
    captcha_id: str = ""
    captcha_code: str = ""


class RefreshIn(BaseModel):
    refresh_token: str


class ForgotIn(BaseModel):
    username: str
    phone: str
    new_password: str


@router.get("/captcha")
def get_captcha():
    cid, img = make_captcha()
    return {"captcha_id": cid, "image": img}


@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if data.role not in ("user", "merchant"):
        raise HTTPException(400, "无效的角色")
    if len(data.password) < 6:
        raise HTTPException(400, "密码至少6位")
    if data.role == "merchant" and not data.shop_name.strip():
        raise HTTPException(400, "请填写店铺名称")
    if db.query(models.User).filter_by(username=data.username).first():
        raise HTTPException(400, "用户名已存在")
    user = models.User(
        username=data.username, password_hash=hash_password(data.password),
        phone=data.phone, nickname=data.nickname or data.username, role=data.role,
    )
    db.add(user)
    db.flush()
    if data.role == "merchant":
        db.add(models.Shop(owner_id=user.id, name=data.shop_name.strip(), status="pending"))
    db.commit()
    return {"id": user.id, "message": "商家注册成功，等待平台审核" if data.role == "merchant" else "注册成功"}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    if not check_captcha(data.captcha_id, data.captcha_code):
        raise HTTPException(400, "验证码错误或已过期")
    user = db.query(models.User).filter_by(username=data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(400, "用户名或密码错误")
    if user.status != 1:
        raise HTTPException(403, "账号已被禁用，请联系平台")
    return {
        "access_token": create_token(user.id, user.role),
        "refresh_token": create_token(user.id, user.role, "refresh"),
        "user": _user_info(db, user),
    }


@router.post("/refresh")
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
    except Exception:
        raise HTTPException(401, "刷新令牌无效或已过期")
    if payload.get("type") != "refresh":
        raise HTTPException(401, "无效令牌")
    user = db.get(models.User, int(payload["sub"]))
    if not user or user.status != 1:
        raise HTTPException(401, "账号不可用")
    return {
        "access_token": create_token(user.id, user.role),
        "refresh_token": create_token(user.id, user.role, "refresh"),
        "user": _user_info(db, user),
    }


@router.post("/logout")
def logout(user: models.User = Depends(get_current_user)):
    return {"ok": True}


@router.post("/forgot-password")
def forgot_password(data: ForgotIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=data.username, phone=data.phone).first()
    if not user:
        raise HTTPException(400, "账号与手机号不匹配")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"ok": True}
