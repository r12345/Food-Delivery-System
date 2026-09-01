from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/user", tags=["个人中心"])


# ================= 个人信息 =================
@router.get("/me")
def me(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    d = user.to_dict()
    d.pop("password_hash", None)
    return d


class ProfileIn(BaseModel):
    nickname: str = ""
    phone: str = ""
    email: str = ""
    avatar: str = ""


@router.put("/me")
def update_me(data: ProfileIn, db: Session = Depends(get_db),
              user: models.User = Depends(get_current_user)):
    if data.nickname:
        user.nickname = data.nickname
    user.phone = data.phone
    user.email = data.email
    user.avatar = data.avatar
    db.commit()
    d = user.to_dict()
    d.pop("password_hash", None)
    return d


# ================= 收货地址 =================
class AddressIn(BaseModel):
    name: str
    phone: str
    gender: str = "先生"
    region: str = ""
    detail: str
    is_default: bool = False


def _unset_default(db: Session, user_id: int):
    db.query(models.Address).filter_by(user_id=user_id, is_default=True).update({"is_default": False})


@router.get("/addresses")
def address_list(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    items = (db.query(models.Address).filter_by(user_id=user.id)
             .order_by(models.Address.is_default.desc(), models.Address.id.desc()).all())
    return {"list": [a.to_dict() for a in items]}


@router.post("/addresses")
def address_create(data: AddressIn, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    if data.is_default:
        _unset_default(db, user.id)
    elif db.query(models.Address).filter_by(user_id=user.id).count() == 0:
        data.is_default = True
    addr = models.Address(user_id=user.id, **data.model_dump())
    db.add(addr)
    db.commit()
    return addr.to_dict()


@router.put("/addresses/{addr_id}")
def address_update(addr_id: int, data: AddressIn, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    addr = db.get(models.Address, addr_id)
    if not addr or addr.user_id != user.id:
        raise HTTPException(404, "地址不存在")
    if data.is_default:
        _unset_default(db, user.id)
    for k, v in data.model_dump().items():
        setattr(addr, k, v)
    db.commit()
    return addr.to_dict()


@router.delete("/addresses/{addr_id}")
def address_delete(addr_id: int, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    addr = db.get(models.Address, addr_id)
    if addr and addr.user_id == user.id:
        db.delete(addr)
        db.commit()
    return {"ok": True}


# ================= 收藏店铺 =================
@router.get("/favorites")
def favorites(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    rows = (db.query(models.Shop, models.Favorite.id)
            .join(models.Favorite, models.Favorite.shop_id == models.Shop.id)
            .filter(models.Favorite.user_id == user.id)
            .order_by(models.Favorite.id.desc()).all())
    return {"list": [{**s.to_dict(), "favorite_id": fid} for s, fid in rows]}


@router.post("/favorites/{shop_id}")
def favorite_add(shop_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    if not db.get(models.Shop, shop_id):
        raise HTTPException(404, "店铺不存在")
    exists = db.query(models.Favorite).filter_by(user_id=user.id, shop_id=shop_id).first()
    if not exists:
        db.add(models.Favorite(user_id=user.id, shop_id=shop_id))
        db.commit()
    return {"ok": True, "favorited": True}


@router.delete("/favorites/{shop_id}")
def favorite_remove(shop_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    db.query(models.Favorite).filter_by(user_id=user.id, shop_id=shop_id).delete()
    db.commit()
    return {"ok": True, "favorited": False}


@router.get("/favorites/{shop_id}/status")
def favorite_status(shop_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    exists = db.query(models.Favorite).filter_by(user_id=user.id, shop_id=shop_id).count()
    return {"favorited": exists > 0}


# ================= 我的优惠券 =================
@router.get("/coupons")
def my_coupons(status: str = "", db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    from datetime import datetime
    q = (db.query(models.UserCoupon, models.Coupon)
         .join(models.Coupon, models.UserCoupon.coupon_id == models.Coupon.id)
         .filter(models.UserCoupon.user_id == user.id)
         .order_by(models.UserCoupon.id.desc()))
    if status:
        q = q.filter(models.UserCoupon.status == status)
    result = []
    for uc, cp in q.all():
        d = cp.to_dict()
        d["uc_id"] = uc.id
        d["uc_status"] = uc.status
        d["expired"] = cp.end_time < datetime.now()
        d["shop_name"] = "平台通用" if not cp.shop_id else ((db.get(models.Shop, cp.shop_id).name) or "")
        result.append(d)
    return {"list": result}


# ================= 我的评价 =================
@router.get("/evaluations")
def my_evaluations(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    rows = (db.query(models.Evaluation, models.Shop.name.label("shop_name"),
                     models.Order.order_no)
            .join(models.Shop, models.Evaluation.shop_id == models.Shop.id)
            .join(models.Order, models.Evaluation.order_id == models.Order.id)
            .filter(models.Evaluation.user_id == user.id)
            .order_by(models.Evaluation.id.desc()).all())
    return {"list": [{**ev.to_dict(), "shop_name": sn, "order_no": ono} for ev, sn, ono in rows]}
