from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..deps import require_roles
from ..security import hash_password

router = APIRouter(prefix="/admin", tags=["平台管理端"],
                   dependencies=[Depends(require_roles("admin"))])

VALID_ORDER_STATUSES = ("pending_pay", "pending_accept", "preparing", "delivering",
                        "completed", "cancelled", "refunding", "refunded")


# ================= 用户管理 =================
@router.get("/users")
def user_list(keyword: str = "", role: str = "", page: int = 1, size: int = 10,
              db: Session = Depends(get_db)):
    q = db.query(models.User)
    if keyword:
        q = q.filter(or_(models.User.username.like(f"%{keyword}%"),
                         models.User.nickname.like(f"%{keyword}%"),
                         models.User.phone.like(f"%{keyword}%")))
    if role:
        q = q.filter_by(role=role)
    total = q.count()
    items = q.order_by(models.User.id.desc()).offset((page - 1) * size).limit(size).all()
    result = []
    for u in items:
        d = u.to_dict()
        d.pop("password_hash", None)
        result.append(d)
    return {"list": result, "total": total}


class StatusIn(BaseModel):
    status: int


@router.post("/users/{user_id}/status")
def user_set_status(user_id: int, data: StatusIn, db: Session = Depends(get_db)):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.role == "admin":
        raise HTTPException(400, "不能禁用管理员账号")
    user.status = 1 if data.status else 0
    db.commit()
    return {"ok": True, "status": user.status}


# ================= 商家/店铺审核管理 =================
@router.get("/shops")
def shop_list(status: str = "", keyword: str = "", page: int = 1, size: int = 10,
              db: Session = Depends(get_db)):
    q = db.query(models.Shop)
    if status:
        q = q.filter_by(status=status)
    if keyword:
        q = q.filter(models.Shop.name.like(f"%{keyword}%"))
    total = q.count()
    items = q.order_by(models.Shop.id.desc()).offset((page - 1) * size).limit(size).all()
    result = []
    for s in items:
        d = s.to_dict()
        owner = db.get(models.User, s.owner_id)
        d["owner_name"] = owner.username if owner else ""
        d["category_name"] = (db.get(models.ShopCategory, s.category_id).name
                              if s.category_id else "")
        result.append(d)
    return {"list": result, "total": total}


class AuditIn(BaseModel):
    action: str  # approved / rejected / banned


@router.post("/shops/{shop_id}/audit")
def audit_shop(shop_id: int, data: AuditIn, db: Session = Depends(get_db)):
    shop = db.get(models.Shop, shop_id)
    if not shop:
        raise HTTPException(404, "店铺不存在")
    if data.action not in ("approved", "rejected", "banned"):
        raise HTTPException(400, "无效的审核操作")
    shop.status = data.action
    if data.action == "approved":
        shop.is_open = True
    msg = {"approved": "审核通过，店铺已上线", "rejected": "入驻申请未通过审核",
           "banned": "店铺已被平台封禁"}[data.action]
    db.add(models.Notification(user_id=shop.owner_id, title="店铺审核通知",
                               content=f"店铺「{shop.name}」{msg}"))
    db.commit()
    return shop.to_dict()


# ================= 全局订单管理 =================
def admin_order_detail(db: Session, o: models.Order) -> dict:
    d = o.to_dict()
    d["items"] = [i.to_dict() for i in db.query(models.OrderItem).filter_by(order_id=o.id).all()]
    shop = db.get(models.Shop, o.shop_id)
    d["shop_name"] = shop.name if shop else ""
    u = db.get(models.User, o.user_id)
    d["user_name"] = u.nickname or u.username if u else ""
    return d


def admin_order_details(db: Session, orders: list[models.Order]) -> list[dict]:
    """批量组装，修正 N+1 查询。"""
    if not orders:
        return []
    ids = [o.id for o in orders]
    items_map: dict[int, list] = {}
    for it in db.query(models.OrderItem).filter(models.OrderItem.order_id.in_(ids)).all():
        items_map.setdefault(it.order_id, []).append(it.to_dict())
    shops = {s.id: s for s in db.query(models.Shop)
             .filter(models.Shop.id.in_({o.shop_id for o in orders})).all()}
    users = {u.id: u for u in db.query(models.User)
             .filter(models.User.id.in_({o.user_id for o in orders})).all()}
    result = []
    for o in orders:
        shop = shops.get(o.shop_id)
        u = users.get(o.user_id)
        d = o.to_dict()
        d["items"] = items_map.get(o.id, [])
        d["shop_name"] = shop.name if shop else ""
        d["user_name"] = (u.nickname or u.username) if u else ""
        result.append(d)
    return result



@router.get("/orders")
def all_orders(status: str = "", keyword: str = "", page: int = 1, size: int = 10,
               db: Session = Depends(get_db)):
    q = db.query(models.Order)
    if status:
        q = q.filter_by(status=status)
    if keyword:
        q = q.filter(models.Order.order_no.like(f"%{keyword}%"))
    total = q.count()
    items = q.order_by(models.Order.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"list": admin_order_details(db, items), "total": total}


@router.post("/orders/{order_id}/refund-agree")
def admin_refund(order_id: int, db: Session = Depends(get_db)):
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "订单不存在")
    if o.status != "refunding":
        raise HTTPException(400, "该订单不在退款申请状态")
    o.status = "refunded"
    o.cancel_reason = o.cancel_reason or "平台处理退款"
    db.add(models.FinanceRecord(shop_id=o.shop_id, order_id=o.id,
                                type="refund", amount=-o.pay_amount, remark="平台退款"))
    uc = db.query(models.UserCoupon).filter_by(used_order_id=o.id, status="used").first()
    if uc:
        uc.status = "unused"
        uc.used_order_id = 0
    shop = db.get(models.Shop, o.shop_id)
    db.add(models.Notification(user_id=o.user_id, title="退款成功",
                               content=f"订单 {o.order_no} 退款 ¥{o.pay_amount} 已原路退回"))
    if shop:
        db.add(models.Notification(user_id=shop.owner_id, title="订单退款",
                                   content=f"订单 {o.order_no} 已由平台同意退款"))
    db.commit()
    return admin_order_detail(db, o)


# ================= 骑手管理 =================
@router.get("/riders")
def rider_list(keyword: str = "", page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    q = db.query(models.Rider)
    if keyword:
        q = q.filter(or_(models.Rider.name.like(f"%{keyword}%"),
                         models.Rider.phone.like(f"%{keyword}%")))
    total = q.count()
    items = q.order_by(models.Rider.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"list": [r.to_dict() for r in items], "total": total}


class RiderIn(BaseModel):
    name: str
    phone: str = ""
    status: int = 1


@router.post("/riders")
def rider_create(data: RiderIn, db: Session = Depends(get_db)):
    rider = models.Rider(name=data.name.strip(), phone=data.phone, status=data.status)
    db.add(rider)
    db.commit()
    return rider.to_dict()


@router.post("/riders/{rider_id}/status")
def rider_status(rider_id: int, data: StatusIn, db: Session = Depends(get_db)):
    rider = db.get(models.Rider, rider_id)
    if not rider:
        raise HTTPException(404, "骑手不存在")
    rider.status = 1 if data.status else 0
    db.commit()
    return rider.to_dict()


# ================= 营销管理 =================
@router.get("/banners")
def banner_list(db: Session = Depends(get_db)):
    items = db.query(models.Banner).order_by(models.Banner.sort, models.Banner.id).all()
    return {"list": [b.to_dict() for b in items]}


class BannerIn(BaseModel):
    title: str = ""
    image: str
    link: str = ""
    sort: int = 0
    status: int = 1


@router.post("/banners")
def banner_create(data: BannerIn, db: Session = Depends(get_db)):
    b = models.Banner(**data.model_dump())
    db.add(b)
    db.commit()
    return b.to_dict()


@router.delete("/banners/{banner_id}")
def banner_delete(banner_id: int, db: Session = Depends(get_db)):
    b = db.get(models.Banner, banner_id)
    if b:
        db.delete(b)
        db.commit()
    return {"ok": True}


@router.get("/coupons")
def platform_coupons(db: Session = Depends(get_db)):
    items = (db.query(models.Coupon).filter(models.Coupon.shop_id == 0)
             .order_by(models.Coupon.id.desc()).all())
    return {"list": [c.to_dict() for c in items]}


class PlatformCouponIn(BaseModel):
    name: str
    threshold: float = 0
    amount: float
    start_time: str
    end_time: str
    total: int = 100


@router.post("/coupons")
def create_platform_coupon(data: PlatformCouponIn, db: Session = Depends(get_db)):
    try:
        start = datetime.strptime(data.start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(data.end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(400, "时间格式不正确")
    if data.amount <= 0 or end <= start:
        raise HTTPException(400, "参数无效")
    cp = models.Coupon(shop_id=0, name=data.name, type="full", threshold=data.threshold,
                       amount=data.amount, start_time=start, end_time=end, total=data.total)
    db.add(cp)
    db.commit()
    return cp.to_dict()


# ================= 数据统计 =================
@router.get("/stats/overview")
def stats_overview(db: Session = Depends(get_db)):
    today = datetime.now().strftime("%Y-%m-%d")
    valid = ~models.Order.status.in_(["pending_pay", "cancelled"])

    def money(q):
        return round(float(q.scalar() or 0), 2)

    total_income = money(db.query(func.coalesce(func.sum(models.FinanceRecord.amount), 0))
                         .filter(models.FinanceRecord.type.in_(["order_income", "refund"])))
    today_income = money(db.query(func.coalesce(func.sum(models.FinanceRecord.amount), 0))
                         .filter(models.FinanceRecord.type.in_(["order_income", "refund"]),
                                 func.date(models.FinanceRecord.created_at) == today))
    total_orders = db.query(models.Order).filter(valid).count()
    today_orders = db.query(models.Order).filter(valid, func.date(models.Order.created_at) == today).count()
    today_users = db.query(models.User).filter(func.date(models.User.created_at) == today,
                                               models.User.role == "user").count()
    return {
        "total_income": total_income, "total_orders": total_orders,
        "today_income": today_income, "today_orders": today_orders,
        "user_count": db.query(models.User).filter_by(role="user").count(),
        "today_users": today_users,
        "merchant_count": db.query(models.Shop).filter_by(status="approved").count(),
        "pending_merchants": db.query(models.Shop).filter_by(status="pending").count(),
        "rider_count": db.query(models.Rider).count(),
    }


@router.get("/stats/trend")
def stats_trend(days: int = 7, db: Session = Depends(get_db)):
    result = []
    for i in range(days - 1, -1, -1):
        day = datetime.now() - timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        valid = ~models.Order.status.in_(["pending_pay", "cancelled"])
        q = (db.query(func.coalesce(func.sum(models.Order.pay_amount), 0),
                      func.count(models.Order.id))
             .filter(valid, func.date(models.Order.created_at) == key).first())
        result.append({"date": key[5:], "amount": round(float(q[0] or 0), 2), "orders": q[1]})
    return {"list": result}


@router.get("/stats/hot-shops")
def stats_hot_shops(db: Session = Depends(get_db)):
    items = (db.query(models.Shop).filter_by(status="approved")
             .order_by(models.Shop.sales.desc()).limit(5).all())
    return {"list": [{"name": s.name, "sales": s.sales, "rating": s.rating} for s in items]}


@router.get("/stats/status")
def stats_status(db: Session = Depends(get_db)):
    rows = (db.query(models.Order.status, func.count(models.Order.id))
            .group_by(models.Order.status).all())
    label = {s["value"]: s["label"] for s in [
        {"value": "pending_pay", "label": "待付款"}, {"value": "pending_accept", "label": "待接单"},
        {"value": "preparing", "label": "备餐中"}, {"value": "delivering", "label": "配送中"},
        {"value": "completed", "label": "已完成"}, {"value": "cancelled", "label": "已取消"},
        {"value": "refunding", "label": "退款中"}, {"value": "refunded", "label": "已退款"}]}
    return {"list": [{"status": s, "label": label.get(s, s), "count": c} for s, c in rows]}


# ================= 管理员账号 =================
@router.get("/admins")
def admin_list(db: Session = Depends(get_db)):
    items = db.query(models.User).filter_by(role="admin").order_by(models.User.id).all()
    result = []
    for u in items:
        d = u.to_dict()
        d.pop("password_hash", None)
        result.append(d)
    return {"list": result}


class AdminIn(BaseModel):
    username: str
    password: str
    nickname: str = ""


@router.post("/admins")
def admin_create(data: AdminIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(username=data.username).count():
        raise HTTPException(400, "用户名已存在")
    if len(data.password) < 6:
        raise HTTPException(400, "密码至少6位")
    u = models.User(username=data.username, password_hash=hash_password(data.password),
                    nickname=data.nickname or data.username, role="admin")
    db.add(u)
    db.commit()
    return {"id": u.id, "username": u.username}
