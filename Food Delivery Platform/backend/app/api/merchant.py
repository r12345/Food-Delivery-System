from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..deps import require_roles

router = APIRouter(prefix="/merchant", tags=["商家端"],
                   dependencies=[Depends(require_roles("merchant"))])


def get_my_shop(db: Session, user: models.User) -> models.Shop:
    shop = db.query(models.Shop).filter_by(owner_id=user.id).first()
    if not shop:
        raise HTTPException(404, "店铺不存在，请先完成入驻")
    return shop


# ================= 店铺管理 =================
@router.get("/shop")
def shop_info(db: Session = Depends(get_db), user: models.User = Depends(require_roles("merchant"))):
    return get_my_shop(db, user).to_dict()


class ShopIn(BaseModel):
    name: str = ""
    logo: str = ""
    cover: str = ""
    description: str = ""
    category_id: int = 0
    phone: str = ""
    address: str = ""
    business_hours: str = "09:00-21:00"
    min_price: float = 0
    delivery_fee: float = 0
    delivery_range: float = 3


@router.put("/shop")
def update_shop(data: ShopIn, db: Session = Depends(get_db),
                user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    for k, v in data.model_dump().items():
        if k == "name" and not v.strip():
            continue
        setattr(shop, k, v)
    db.commit()
    return shop.to_dict()


class OpenIn(BaseModel):
    is_open: bool


@router.post("/shop/open")
def open_or_close(data: OpenIn, db: Session = Depends(get_db),
                  user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    if shop.status != "approved":
        raise HTTPException(400, "店铺未通过审核，无法营业")
    shop.is_open = data.is_open
    db.commit()
    return shop.to_dict()


# ================= 菜品分类 =================
class CategoryIn(BaseModel):
    name: str
    sort: int = 0


@router.get("/categories")
def category_list(db: Session = Depends(get_db), user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    items = (db.query(models.FoodCategory).filter_by(shop_id=shop.id)
             .order_by(models.FoodCategory.sort, models.FoodCategory.id).all())
    return {"list": [c.to_dict() for c in items]}


@router.post("/categories")
def category_create(data: CategoryIn, db: Session = Depends(get_db),
                    user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    cat = models.FoodCategory(shop_id=shop.id, name=data.name.strip(), sort=data.sort)
    db.add(cat)
    db.commit()
    return cat.to_dict()


@router.put("/categories/{cat_id}")
def category_update(cat_id: int, data: CategoryIn, db: Session = Depends(get_db),
                    user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    cat = db.get(models.FoodCategory, cat_id)
    if not cat or cat.shop_id != shop.id:
        raise HTTPException(404, "分类不存在")
    cat.name = data.name.strip()
    cat.sort = data.sort
    db.commit()
    return cat.to_dict()


@router.delete("/categories/{cat_id}")
def category_delete(cat_id: int, db: Session = Depends(get_db),
                    user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    cat = db.get(models.FoodCategory, cat_id)
    if not cat or cat.shop_id != shop.id:
        raise HTTPException(404, "分类不存在")
    count = db.query(models.Food).filter_by(category_id=cat_id).count()
    if count:
        raise HTTPException(400, "该分类下还有菜品，无法删除")
    db.delete(cat)
    db.commit()
    return {"ok": True}


# ================= 菜品管理 =================
class FoodIn(BaseModel):
    category_id: int = 0
    name: str
    price: float
    original_price: float = 0
    image: str = ""
    description: str = ""
    stock: int = 100
    specs: list = []
    status: int = 1


@router.get("/foods")
def food_list(keyword: str = "", category_id: int = 0, page: int = 1, size: int = 20,
              db: Session = Depends(get_db), user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    q = db.query(models.Food).filter_by(shop_id=shop.id)
    if keyword:
        q = q.filter(models.Food.name.like(f"%{keyword}%"))
    if category_id:
        q = q.filter_by(category_id=category_id)
    total = q.count()
    items = (q.order_by(models.Food.id.desc()).offset((page - 1) * size).limit(size).all())
    return {"list": [f.to_dict() for f in items], "total": total}


@router.post("/foods")
def food_create(data: FoodIn, db: Session = Depends(get_db),
                user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    food = models.Food(shop_id=shop.id, **data.model_dump())
    db.add(food)
    db.commit()
    return food.to_dict()


@router.put("/foods/{food_id}")
def food_update(food_id: int, data: FoodIn, db: Session = Depends(get_db),
                user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    food = db.get(models.Food, food_id)
    if not food or food.shop_id != shop.id:
        raise HTTPException(404, "菜品不存在")
    for k, v in data.model_dump().items():
        setattr(food, k, v)
    db.commit()
    return food.to_dict()


@router.delete("/foods/{food_id}")
def food_delete(food_id: int, db: Session = Depends(get_db),
                user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    food = db.get(models.Food, food_id)
    if not food or food.shop_id != shop.id:
        raise HTTPException(404, "菜品不存在")
    db.delete(food)
    db.commit()
    return {"ok": True}


# ================= 订单处理 =================
def m_order_detail(db: Session, o: models.Order) -> dict:
    d = o.to_dict()
    d["items"] = [i.to_dict() for i in db.query(models.OrderItem).filter_by(order_id=o.id).all()]
    u = db.get(models.User, o.user_id)
    d["user_name"] = u.nickname if u else ""
    return d


def m_order_details(db: Session, orders: list[models.Order]) -> list[dict]:
    """批量组装，修正 N+1 查询。"""
    if not orders:
        return []
    ids = [o.id for o in orders]
    items_map: dict[int, list] = {}
    for it in db.query(models.OrderItem).filter(models.OrderItem.order_id.in_(ids)).all():
        items_map.setdefault(it.order_id, []).append(it.to_dict())
    users = {u.id: u for u in db.query(models.User)
             .filter(models.User.id.in_({o.user_id for o in orders})).all()}
    result = []
    for o in orders:
        u = users.get(o.user_id)
        d = o.to_dict()
        d["items"] = items_map.get(o.id, [])
        d["user_name"] = u.nickname if u else ""
        result.append(d)
    return result



@router.get("/orders")
def merchant_orders(status: str = "", page: int = 1, size: int = 10,
                    db: Session = Depends(get_db), user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    q = db.query(models.Order).filter_by(shop_id=shop.id)
    if status:
        q = q.filter_by(status=status)
    total = q.count()
    items = q.order_by(models.Order.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"list": m_order_details(db, items), "total": total}


@router.get("/orders/{order_id}")
def merchant_order_detail(order_id: int, db: Session = Depends(get_db),
                          user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    o = db.get(models.Order, order_id)
    if not o or o.shop_id != shop.id:
        raise HTTPException(404, "订单不存在")
    return m_order_detail(db, o)


def _get_shop_order(db: Session, user: models.User, order_id: int) -> models.Order:
    shop = get_my_shop(db, user)
    o = db.get(models.Order, order_id)
    if not o or o.shop_id != shop.id:
        raise HTTPException(404, "订单不存在")
    return o


@router.post("/orders/{order_id}/accept")
def accept_order(order_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("merchant"))):
    o = _get_shop_order(db, user, order_id)
    if o.status != "pending_accept":
        raise HTTPException(400, "订单状态不正确")
    o.status = "preparing"
    db.add(models.Notification(user_id=o.user_id, title="商家已接单",
                               content=f"订单 {o.order_no} 商家已接单，正在备餐"))
    db.commit()
    return m_order_detail(db, o)


class RejectIn(BaseModel):
    reason: str = "商家无法接单"


@router.post("/orders/{order_id}/reject")
def reject_order(order_id: int, data: RejectIn, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("merchant"))):
    o = _get_shop_order(db, user, order_id)
    if o.status != "pending_accept":
        raise HTTPException(400, "订单状态不正确")
    o.status = "refunded"
    o.cancel_reason = data.reason
    db.add(models.FinanceRecord(shop_id=o.shop_id, order_id=o.id,
                                type="refund", amount=-o.pay_amount, remark="商家拒单退款"))
    uc = db.query(models.UserCoupon).filter_by(used_order_id=o.id, status="used").first()
    if uc:
        uc.status = "unused"
        uc.used_order_id = 0
    db.add(models.Notification(user_id=o.user_id, title="商家已拒单",
                               content=f"订单 {o.order_no} 被拒单：{data.reason}，退款将原路退回"))
    db.commit()
    return m_order_detail(db, o)


@router.post("/orders/{order_id}/deliver")
def deliver_order(order_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(require_roles("merchant"))):
    o = _get_shop_order(db, user, order_id)
    if o.status != "preparing":
        raise HTTPException(400, "订单状态不正确")
    o.status = "delivering"
    db.add(models.Notification(user_id=o.user_id, title="订单配送中",
                               content=f"订单 {o.order_no} 已出餐，骑手配送中"))
    db.commit()
    return m_order_detail(db, o)


@router.post("/orders/{order_id}/finish")
def finish_order(order_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("merchant"))):
    o = _get_shop_order(db, user, order_id)
    if o.status != "delivering":
        raise HTTPException(400, "订单状态不正确")
    o.status = "completed"
    db.add(models.Notification(user_id=o.user_id, title="订单已送达",
                               content=f"订单 {o.order_no} 已送达，欢迎评价"))
    db.commit()
    return m_order_detail(db, o)


@router.post("/orders/{order_id}/refund-agree")
def agree_refund(order_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("merchant"))):
    o = _get_shop_order(db, user, order_id)
    if o.status != "refunding":
        raise HTTPException(400, "订单状态不正确")
    o.status = "refunded"
    o.cancel_reason = o.cancel_reason or "商家同意退款"
    db.add(models.FinanceRecord(shop_id=o.shop_id, order_id=o.id,
                                type="refund", amount=-o.pay_amount, remark="退款"))
    uc = db.query(models.UserCoupon).filter_by(used_order_id=o.id, status="used").first()
    if uc:
        uc.status = "unused"
        uc.used_order_id = 0
    db.add(models.Notification(user_id=o.user_id, title="退款成功",
                               content=f"订单 {o.order_no} 退款 ¥{o.pay_amount} 已原路退回"))
    db.commit()
    return m_order_detail(db, o)


# ================= 财务管理 =================
@router.get("/finance/summary")
def finance_summary(db: Session = Depends(get_db), user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    today = datetime.now().strftime("%Y-%m-%d")
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def income_sum(q):
        return round(float(q.scalar() or 0), 2)

    today_amount = income_sum(db.query(func.coalesce(func.sum(models.FinanceRecord.amount), 0))
                              .filter(models.FinanceRecord.shop_id == shop.id,
                                      models.FinanceRecord.type == "order_income",
                                      func.date(models.FinanceRecord.created_at) == today))
    total_income = income_sum(db.query(func.coalesce(func.sum(models.FinanceRecord.amount), 0))
                              .filter(models.FinanceRecord.shop_id == shop.id,
                                      models.FinanceRecord.type.in_(["order_income", "refund"])))
    month_amount = income_sum(db.query(func.coalesce(func.sum(models.FinanceRecord.amount), 0))
                              .filter(models.FinanceRecord.shop_id == shop.id,
                                      models.FinanceRecord.type.in_(["order_income", "refund"]),
                                      models.FinanceRecord.created_at >= month_start))
    withdraw_amount = income_sum(db.query(func.coalesce(func.sum(models.FinanceRecord.amount), 0))
                                 .filter(models.FinanceRecord.shop_id == shop.id,
                                         models.FinanceRecord.type == "withdraw"))
    today_orders = db.query(models.Order).filter(
        models.Order.shop_id == shop.id,
        models.Order.status.in_(["pending_accept", "preparing", "delivering", "completed", "refunding", "refunded"]),
        func.date(models.Order.created_at) == today).count()
    pending = db.query(models.Order).filter_by(shop_id=shop.id, status="pending_accept").count()
    return {
        "today_amount": today_amount, "today_orders": today_orders,
        "month_amount": month_amount, "total_income": total_income,
        "withdraw_amount": withdraw_amount, "balance": round(total_income - abs(withdraw_amount), 2),
        "pending_orders": pending,
    }


@router.get("/finance/records")
def finance_records(page: int = 1, size: int = 15, db: Session = Depends(get_db),
                    user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    q = db.query(models.FinanceRecord).filter_by(shop_id=shop.id)
    total = q.count()
    items = q.order_by(models.FinanceRecord.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"list": [r.to_dict() for r in items], "total": total}


class WithdrawIn(BaseModel):
    amount: float


@router.post("/finance/withdraw")
def withdraw(data: WithdrawIn, db: Session = Depends(get_db),
             user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    if data.amount <= 0:
        raise HTTPException(400, "提现金额无效")
    summary = finance_summary(db, user)
    if data.amount > summary["balance"]:
        raise HTTPException(400, "超出可提现余额")
    rec = models.FinanceRecord(shop_id=shop.id, type="withdraw", amount=data.amount, remark="提现申请")
    db.add(rec)
    db.commit()
    return rec.to_dict()


# ================= 评价管理 =================
@router.get("/evaluations")
def merchant_evaluations(page: int = 1, size: int = 10, db: Session = Depends(get_db),
                         user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    q = (db.query(models.Evaluation, models.User.nickname, models.Order.order_no)
         .join(models.User, models.Evaluation.user_id == models.User.id)
         .join(models.Order, models.Evaluation.order_id == models.Order.id)
         .filter(models.Evaluation.shop_id == shop.id)
         .order_by(models.Evaluation.id.desc()))
    total = q.count()
    rows = q.offset((page - 1) * size).limit(size).all()
    return {"list": [{**ev.to_dict(), "nickname": nk, "order_no": ono} for ev, nk, ono in rows],
            "total": total}


class ReplyIn(BaseModel):
    reply: str


@router.post("/evaluations/{eval_id}/reply")
def reply_evaluation(eval_id: int, data: ReplyIn, db: Session = Depends(get_db),
                     user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    ev = db.get(models.Evaluation, eval_id)
    if not ev or ev.shop_id != shop.id:
        raise HTTPException(404, "评价不存在")
    ev.reply = data.reply
    db.commit()
    return ev.to_dict()


# ================= 店铺优惠券 =================
class CouponIn(BaseModel):
    name: str
    threshold: float = 0
    amount: float
    start_time: str
    end_time: str
    total: int = 100


@router.get("/coupons")
def merchant_coupons(db: Session = Depends(get_db), user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    items = (db.query(models.Coupon).filter(models.Coupon.shop_id == shop.id)
             .order_by(models.Coupon.id.desc()).all())
    return {"list": [c.to_dict() for c in items]}


@router.post("/coupons")
def create_coupon(data: CouponIn, db: Session = Depends(get_db),
                  user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    try:
        start = datetime.strptime(data.start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(data.end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(400, "时间格式不正确")
    if data.amount <= 0:
        raise HTTPException(400, "优惠金额无效")
    if end <= start:
        raise HTTPException(400, "结束时间需晚于开始时间")
    cp = models.Coupon(shop_id=shop.id, name=data.name, type="full", threshold=data.threshold,
                       amount=data.amount, start_time=start, end_time=end, total=data.total)
    db.add(cp)
    db.commit()
    return cp.to_dict()


# ================= 商家工作台 =================
@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: models.User = Depends(require_roles("merchant"))):
    shop = get_my_shop(db, user)
    summary = finance_summary(db, user)
    recent = (db.query(models.Order).filter_by(shop_id=shop.id)
              .order_by(models.Order.id.desc()).limit(5).all())
    return {"summary": summary, "shop": shop.to_dict(),
            "recent_orders": m_order_details(db, recent)}
