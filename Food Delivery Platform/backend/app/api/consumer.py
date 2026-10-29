import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models
from ..config import SECRET_KEY
from ..db import get_db
from ..deps import get_current_user, require_roles
from ..api.ws import push_to_merchant

router = APIRouter(tags=["C端"])

PAYABLE_STATUSES = ("pending_accept", "preparing", "delivering", "completed")


def _verify_pay_sign(order_no: str, sign: str) -> bool:
    """模拟支付网关回调验签：sign = HMAC-SHA256(order_no, SECRET_KEY) 的前 32 位十六进制。"""
    if not sign:
        return False
    expect = hmac.new(SECRET_KEY.encode(), order_no.encode(), hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(expect, sign)



def get_shop_or_404(db: Session, shop_id: int) -> models.Shop:
    shop = db.get(models.Shop, shop_id)
    if not shop:
        raise HTTPException(404, "店铺不存在")
    return shop


def _shop_card(s: models.Shop) -> dict:
    return {
        "id": s.id, "name": s.name, "logo": s.logo, "cover": s.cover,
        "description": s.description, "rating": s.rating, "sales": s.sales,
        "min_price": s.min_price, "delivery_fee": s.delivery_fee,
        "delivery_range": s.delivery_range, "business_hours": s.business_hours,
        "is_open": s.is_open, "status": s.status, "category_id": s.category_id,
    }


# ================= 首页 =================
@router.get("/home")
def home(db: Session = Depends(get_db)):
    banners = db.query(models.Banner).filter_by(status=1).order_by(models.Banner.sort).all()
    categories = db.query(models.ShopCategory).all()
    hot_shops = (db.query(models.Shop).filter_by(status="approved", is_open=True)
                 .order_by(models.Shop.sales.desc()).limit(6).all())
    foods = (db.query(models.Food, models.Shop.name.label("shop_name"))
             .join(models.Shop, models.Food.shop_id == models.Shop.id)
             .filter(models.Food.status == 1, models.Shop.status == "approved", models.Shop.is_open == True)
             .order_by(models.Food.sales.desc()).limit(8).all())
    return {
        "banners": [b.to_dict() for b in banners],
        "categories": [c.to_dict() for c in categories],
        "hot_shops": [_shop_card(s) for s in hot_shops],
        "recommend_foods": [
            {**f.to_dict(), "shop_name": name} for f, name in foods
        ],
    }


# ================= 店铺 =================
@router.get("/shops")
def shop_list(keyword: str = "", category_id: int = 0, sort: str = "sales",
              page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    q = db.query(models.Shop).filter_by(status="approved", is_open=True)
    if keyword:
        food_shop_ids = [r[0] for r in db.query(models.Food.shop_id)
                         .filter(models.Food.name.like(f"%{keyword}%")).distinct()]
        q = q.filter(or_(models.Shop.name.like(f"%{keyword}%"),
                         models.Shop.description.like(f"%{keyword}%"),
                         models.Shop.id.in_(food_shop_ids)))
    if category_id:
        q = q.filter_by(category_id=category_id)
    order = {"sales": models.Shop.sales.desc(), "rating": models.Shop.rating.desc(),
             "delivery_fee": models.Shop.delivery_fee.asc()}.get(sort, models.Shop.sales.desc())
    total = q.count()
    items = q.order_by(order).offset((page - 1) * size).limit(size).all()
    return {"list": [_shop_card(s) for s in items], "total": total}


@router.get("/shops/{shop_id}")
def shop_detail(shop_id: int, db: Session = Depends(get_db)):
    shop = get_shop_or_404(db, shop_id)
    if shop.status != "approved":
        raise HTTPException(400, "店铺暂不可用")
    cats = (db.query(models.FoodCategory).filter_by(shop_id=shop_id)
            .order_by(models.FoodCategory.sort, models.FoodCategory.id).all())
    foods = (db.query(models.Food).filter_by(shop_id=shop_id, status=1)
             .order_by(models.Food.sales.desc()).all())
    menu = []
    for c in cats:
        menu.append({"id": c.id, "name": c.name,
                     "foods": [f.to_dict() for f in foods if f.category_id == c.id]})
    uncategorized = [f.to_dict() for f in foods if not any(c.id == f.category_id for c in cats)]
    if uncategorized:
        menu.insert(0, {"id": 0, "name": "其他", "foods": uncategorized})
    eval_count = db.query(models.Evaluation).filter_by(shop_id=shop_id).count()
    return {**shop.to_dict(), "menu": menu, "eval_count": eval_count}


@router.get("/foods/{food_id}")
def food_detail(food_id: int, db: Session = Depends(get_db)):
    food = db.get(models.Food, food_id)
    if not food:
        raise HTTPException(404, "菜品不存在")
    shop = db.get(models.Shop, food.shop_id)
    return {**food.to_dict(), "shop_name": shop.name if shop else ""}


# ================= 购物车（需登录） =================
def _spec_delta(food: models.Food, spec: str) -> float:
    """根据规格名称计算加价"""
    for g in (food.specs or []):
        for opt in g.get("options", []):
            if opt.get("name") == spec:
                return float(opt.get("price", 0))
    return 0


def func_sum_cart(db: Session, user_id: int) -> int:
    from sqlalchemy import func
    return int(db.query(func.coalesce(func.sum(models.Cart.quantity), 0))
               .filter_by(user_id=user_id).scalar())


class CartAddIn(BaseModel):
    food_id: int
    quantity: int = 1
    spec: str = ""


class CartUpdateIn(BaseModel):
    quantity: int


@router.get("/cart")
def cart_list(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    items = db.query(models.Cart).filter_by(user_id=user.id).order_by(models.Cart.id).all()
    shops = {}
    for it in items:
        food = db.get(models.Food, it.food_id)
        shop = db.get(models.Shop, it.shop_id)
        key = it.shop_id
        shops.setdefault(key, {
            "shop_id": key, "shop_name": shop.name if shop else "",
            "is_open": shop.is_open if shop else False,
            "min_price": shop.min_price if shop else 0,
            "delivery_fee": shop.delivery_fee if shop else 0,
            "items": [],
        })
        shops[key]["items"].append({
            "id": it.id, "food_id": it.food_id, "name": food.name if food else "已下架",
            "image": food.image if food else "", "spec": it.spec,
            "unit_price": it.unit_price, "quantity": it.quantity,
        })
    return {"list": list(shops.values()), "count": sum(len(v["items"]) for v in shops.values())}


@router.post("/cart")
def cart_add(data: CartAddIn, db: Session = Depends(get_db),
             user: models.User = Depends(get_current_user)):
    if data.quantity <= 0:
        raise HTTPException(400, "数量必须大于 0")
    food = db.get(models.Food, data.food_id)
    if not food or food.status != 1:
        raise HTTPException(400, "菜品已下架")
    shop = get_shop_or_404(db, food.shop_id)
    if not shop.is_open:
        raise HTTPException(400, "商家已打烊，暂不接受订单")
    unit_price = round(food.price + _spec_delta(food, data.spec), 2)
    item = (db.query(models.Cart)
            .filter_by(user_id=user.id, food_id=food.id, spec=data.spec).first())
    # 修正：加购时校验库存，避免购物车数量超过可售库存
    already = item.quantity if item else 0
    if already + data.quantity > food.stock:
        raise HTTPException(400, f"库存不足，当前仅剩 {food.stock} 份")
    if item:
        item.quantity += data.quantity
    else:
        db.add(models.Cart(user_id=user.id, shop_id=food.shop_id, food_id=food.id,
                           quantity=data.quantity, spec=data.spec, unit_price=unit_price))
    db.commit()
    return {"count": func_sum_cart(db, user.id)}



@router.put("/cart/{item_id}")
def cart_update(item_id: int, data: CartUpdateIn, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    item = db.get(models.Cart, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(404, "购物车项不存在")
    if data.quantity <= 0:
        db.delete(item)
    else:
        food = db.get(models.Food, item.food_id)
        # 修正：修改数量时同样校验库存上限
        if food and data.quantity > food.stock:
            raise HTTPException(400, f"库存不足，当前仅剩 {food.stock} 份")
        item.quantity = data.quantity
    db.commit()
    return {"count": func_sum_cart(db, user.id)}



@router.delete("/cart/{item_id}")
def cart_remove(item_id: int, db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    item = db.get(models.Cart, item_id)
    if item and item.user_id == user.id:
        db.delete(item)
        db.commit()
    return {"count": func_sum_cart(db, user.id)}


@router.delete("/cart")
def cart_clear(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db.query(models.Cart).filter_by(user_id=user.id).delete()
    db.commit()
    return {"count": 0}


# ================= 订单 =================
class OrderCreateIn(BaseModel):
    address_id: int
    shop_id: int
    remark: str = ""
    pay_type: str = "wechat"
    coupon_id: int = 0   # UserCoupon.id


class PayIn(BaseModel):
    pay_type: str = "wechat"


def order_detail(db: Session, o: models.Order) -> dict:
    d = o.to_dict()
    d["items"] = [i.to_dict() for i in db.query(models.OrderItem).filter_by(order_id=o.id).all()]
    shop = db.get(models.Shop, o.shop_id)
    d["shop_name"] = shop.name if shop else ""
    d["shop_logo"] = shop.logo if shop else ""
    d["has_evaluation"] = db.query(models.Evaluation).filter_by(order_id=o.id).count() > 0
    return d


def order_details(db: Session, orders: list[models.Order]) -> list[dict]:
    """批量组装订单详情，修正 N+1：一次查完所有明细/店铺/评价。"""
    if not orders:
        return []
    ids = [o.id for o in orders]
    shop_ids = {o.shop_id for o in orders}

    items_map: dict[int, list] = {}
    for it in db.query(models.OrderItem).filter(models.OrderItem.order_id.in_(ids)).all():
        items_map.setdefault(it.order_id, []).append(it.to_dict())

    shops = {s.id: s for s in db.query(models.Shop)
             .filter(models.Shop.id.in_(shop_ids)).all()}

    evaluated = {row[0] for row in db.query(models.Evaluation.order_id)
                 .filter(models.Evaluation.order_id.in_(ids)).all()}

    result = []
    for o in orders:
        shop = shops.get(o.shop_id)
        d = o.to_dict()
        d["items"] = items_map.get(o.id, [])
        d["shop_name"] = shop.name if shop else ""
        d["shop_logo"] = shop.logo if shop else ""
        d["has_evaluation"] = o.id in evaluated
        result.append(d)
    return result



def _gen_order_no() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S") + secrets.token_hex(3).upper()


def do_pay(db: Session, order: models.Order, pay_type: str):
    """模拟支付回调核心逻辑"""
    if order.status != "pending_pay":
        raise HTTPException(400, "订单状态不正确，无法支付")
    order.status = "pending_accept"
    order.pay_time = datetime.now()
    if pay_type in ("wechat", "alipay"):
        order.pay_type = pay_type
    shop = db.get(models.Shop, order.shop_id)
    db.add(models.FinanceRecord(shop_id=order.shop_id, order_id=order.id,
                                type="order_income", amount=order.pay_amount, remark="订单收入"))
    db.add(models.Notification(user_id=order.user_id, title="订单支付成功",
                               content=f"订单 {order.order_no} 已支付 ¥{order.pay_amount}，等待商家接单"))
    db.add(models.Notification(user_id=shop.owner_id, title="您有新的外卖订单",
                               content=f"订单 {order.order_no}，实付 ¥{order.pay_amount}，请及时接单"))
    db.commit()
    return shop.owner_id


@router.post("/orders")
def create_order(data: OrderCreateIn, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("user"))):
    addr = db.get(models.Address, data.address_id)
    if not addr or addr.user_id != user.id:
        raise HTTPException(400, "收货地址无效")
    shop = get_shop_or_404(db, data.shop_id)
    if shop.status != "approved" or not shop.is_open:
        raise HTTPException(400, "商家已打烊或暂不可用")
    cart_items = db.query(models.Cart).filter_by(user_id=user.id, shop_id=data.shop_id).all()
    if not cart_items:
        raise HTTPException(400, "购物车为空")
    total = round(sum(it.unit_price * it.quantity for it in cart_items), 2)
    if total < shop.min_price:
        raise HTTPException(400, f"未达到起送价 ¥{shop.min_price}")

    # 修正：下单前逐项校验库存与上架状态，库存不足直接拒绝，避免超卖
    for it in cart_items:
        food = db.get(models.Food, it.food_id)
        if not food or food.status != 1:
            raise HTTPException(400, f"「{food.name if food else '菜品'}」已下架，请从购物车移除")
        if it.quantity > food.stock:
            raise HTTPException(
                400, f"「{food.name}」库存不足，仅剩 {food.stock} 份，请调整数量")

    # 优惠券
    discount = 0
    if data.coupon_id:
        uc = db.get(models.UserCoupon, data.coupon_id)
        if not uc or uc.user_id != user.id or uc.status != "unused":
            raise HTTPException(400, "优惠券不可用")
        cp = db.get(models.Coupon, uc.coupon_id)
        now = datetime.now()
        if not cp or cp.status != 1 or cp.end_time < now or cp.start_time > now:
            raise HTTPException(400, "优惠券已过期或已下架")
        if cp.shop_id not in (0, data.shop_id):
            raise HTTPException(400, "优惠券不适用于该店铺")
        if total < cp.threshold:
            raise HTTPException(400, f"未达到优惠券使用门槛 ¥{cp.threshold}")
        discount = cp.amount
        uc.status = "used"
        uc.used_order_id = 0  # 稍后回填

    order = models.Order(
        order_no=_gen_order_no(), user_id=user.id, shop_id=data.shop_id,
        address={"name": addr.name, "phone": addr.phone, "region": addr.region, "detail": addr.detail},
        status="pending_pay", total_amount=total, delivery_fee=shop.delivery_fee,
        discount_amount=discount, pay_amount=round(total + shop.delivery_fee - discount, 2),
        pay_type=data.pay_type, remark=data.remark,
    )
    db.add(order)
    db.flush()
    if data.coupon_id:
        uc = db.get(models.UserCoupon, data.coupon_id)
        uc.used_order_id = order.id
    for it in cart_items:
        food = db.get(models.Food, it.food_id)
        db.add(models.OrderItem(order_id=order.id, food_id=it.food_id,
                                food_name=food.name if food else "已下架菜品",
                                image=food.image if food else "", price=it.unit_price,
                                quantity=it.quantity, spec=it.spec))
        if food:
            food.sales += it.quantity
            # 修正：前面已校验库存充足，这里直接扣减即可（不再用 max(0,...) 掩盖超卖）
            food.stock = food.stock - it.quantity
    shop.sales += 1
    db.query(models.Cart).filter_by(user_id=user.id, shop_id=data.shop_id).delete()
    db.commit()
    return order_detail(db, order)


@router.get("/orders")
def my_orders(status: str = "", page: int = 1, size: int = 10,
              db: Session = Depends(get_db), user: models.User = Depends(require_roles("user"))):
    q = db.query(models.Order).filter_by(user_id=user.id)
    if status:
        q = q.filter_by(status=status)
    total = q.count()
    items = q.order_by(models.Order.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"list": order_details(db, items), "total": total}


@router.get("/orders/{order_id}")
def order_info(order_id: int, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    """订单详情：普通用户仅可查看自己的订单；商家仅可查看本店订单；管理员可查看全部。"""
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "订单不存在")

    if user.role == "admin":
        pass
    elif user.role == "merchant":
        shop = db.query(models.Shop).filter_by(owner_id=user.id).first()
        if not shop or o.shop_id != shop.id:
            raise HTTPException(403, "无权查看该订单")
    elif o.user_id != user.id:
        raise HTTPException(403, "无权查看该订单")

    return order_detail(db, o)


@router.post("/pay/notify")
def pay_notify(data: PayIn, order_no: str, sign: str = "",
               db: Session = Depends(get_db)):
    """支付回调（模拟网关）。

    修正：原实现无任何校验，任何人凭订单号即可把订单置为已支付。
    现要求携带与 SECRET_KEY 派生的回调签名 sign，签名不符一律拒绝。
    真实接入时这里应替换为微信/支付宝的验签逻辑。
    """
    order = db.query(models.Order).filter_by(order_no=order_no).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if not _verify_pay_sign(order_no, sign):
        raise HTTPException(403, "支付回调签名校验失败")
    owner_id = do_pay(db, order, data.pay_type)
    return {"ok": True, "order_no": order.order_no, "owner_id": owner_id}


@router.post("/orders/{order_id}/pay")
async def pay_order(order_id: int, data: PayIn, db: Session = Depends(get_db),
                    user: models.User = Depends(require_roles("user"))):
    o = db.get(models.Order, order_id)
    if not o or o.user_id != user.id:
        raise HTTPException(404, "订单不存在")
    owner_id = do_pay(db, o, data.pay_type)
    await push_to_merchant(owner_id, {
        "type": "new_order", "order_id": o.id, "order_no": o.order_no,
        "pay_amount": o.pay_amount, "shop_id": o.shop_id,
        "created_at": o.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    })
    return order_detail(db, o)


@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("user"))):
    o = db.get(models.Order, order_id)
    if not o or o.user_id != user.id:
        raise HTTPException(404, "订单不存在")
    if o.status not in ("pending_pay", "pending_accept"):
        raise HTTPException(400, "当前状态不可取消")
    paid = o.status == "pending_accept"
    o.status = "cancelled"
    o.cancel_reason = "用户取消"
    if paid:  # 已支付：退款流水 + 优惠券返还
        db.add(models.FinanceRecord(shop_id=o.shop_id, order_id=o.id,
                                    type="refund", amount=-o.pay_amount, remark="用户取消退款"))
        _return_coupon(db, o)
    db.add(models.Notification(user_id=o.user_id, title="订单已取消",
                               content=f"订单 {o.order_no} 已取消" + ("，退款将原路退回" if paid else "")))
    db.commit()
    return order_detail(db, o)


def _return_coupon(db: Session, order: models.Order):
    uc = db.query(models.UserCoupon).filter_by(used_order_id=order.id, status="used").first()
    if uc:
        uc.status = "unused"
        uc.used_order_id = 0


@router.post("/orders/{order_id}/confirm")
def confirm_order(order_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(require_roles("user"))):
    o = db.get(models.Order, order_id)
    if not o or o.user_id != user.id:
        raise HTTPException(404, "订单不存在")
    if o.status != "delivering":
        raise HTTPException(400, "当前状态不可确认收货")
    o.status = "completed"
    db.add(models.Notification(user_id=o.user_id, title="订单已完成",
                               content=f"订单 {o.order_no} 已完成，快去评价吧"))
    db.commit()
    return order_detail(db, o)


@router.post("/orders/{order_id}/refund")
def apply_refund(order_id: int, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("user"))):
    o = db.get(models.Order, order_id)
    if not o or o.user_id != user.id:
        raise HTTPException(404, "订单不存在")
    if o.status not in ("pending_accept", "preparing", "delivering"):
        raise HTTPException(400, "当前状态不可申请退款")
    o.status = "refunding"
    db.add(models.Notification(user_id=o.user_id, title="退款申请已提交",
                               content=f"订单 {o.order_no} 退款申请已提交，等待商家处理"))
    db.commit()
    return order_detail(db, o)


# ================= 评价 =================
class EvalIn(BaseModel):
    shop_rating: float = 5
    rider_rating: float = 5
    content: str = ""


@router.post("/orders/{order_id}/evaluation")
def create_evaluation(order_id: int, data: EvalIn, db: Session = Depends(get_db),
                      user: models.User = Depends(require_roles("user"))):
    o = db.get(models.Order, order_id)
    if not o or o.user_id != user.id:
        raise HTTPException(404, "订单不存在")
    if o.status != "completed":
        raise HTTPException(400, "订单完成后才能评价")
    if db.query(models.Evaluation).filter_by(order_id=order_id).count():
        raise HTTPException(400, "该订单已评价")
    ev = models.Evaluation(order_id=order_id, user_id=user.id, shop_id=o.shop_id,
                           shop_rating=data.shop_rating, rider_rating=data.rider_rating,
                           content=data.content)
    db.add(ev)
    db.flush()   # 修正：先 flush 让新评价进入本次事务，否则平均分漏算当前这条
    # 更新店铺评分
    shop = db.get(models.Shop, o.shop_id)
    if shop:
        avg = db.query(func_avg_eval()).filter_by(shop_id=shop.id).scalar()
        shop.rating = round(float(avg), 1) if avg else 5.0
    db.commit()
    return ev.to_dict()



def func_avg_eval():
    from sqlalchemy import func
    return func.avg(models.Evaluation.shop_rating)


@router.get("/shops/{shop_id}/evaluations")
def shop_evaluations(shop_id: int, page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    q = (db.query(models.Evaluation, models.User.nickname, models.User.avatar)
         .join(models.User, models.Evaluation.user_id == models.User.id)
         .filter(models.Evaluation.shop_id == shop_id)
         .order_by(models.Evaluation.id.desc()))
    total = q.count()
    rows = q.offset((page - 1) * size).limit(size).all()
    return {"list": [{**ev.to_dict(), "nickname": nk, "avatar": av} for ev, nk, av in rows],
            "total": total}


# ================= 优惠券 =================
@router.get("/coupons")
def receivable_coupons(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    now = datetime.now()
    cps = (db.query(models.Coupon)
           .filter(models.Coupon.status == 1, models.Coupon.end_time > now,
                   models.Coupon.start_time <= now, models.Coupon.received < models.Coupon.total)
           .order_by(models.Coupon.id.desc()).all())
    my_coupon_ids = {uc.coupon_id for uc in db.query(models.UserCoupon)
                     .filter_by(user_id=user.id).all()}
    result = []
    for cp in cps:
        d = cp.to_dict()
        d["shop_name"] = "平台通用" if not cp.shop_id else (db.get(models.Shop, cp.shop_id).name or "")
        d["received_by_me"] = cp.id in my_coupon_ids
        result.append(d)
    return {"list": result}


@router.post("/coupons/{coupon_id}/receive")
def receive_coupon(coupon_id: int, db: Session = Depends(get_db),
                   user: models.User = Depends(get_current_user)):
    cp = db.get(models.Coupon, coupon_id)
    now = datetime.now()
    if not cp or cp.status != 1 or cp.end_time < now:
        raise HTTPException(400, "优惠券不可领取")
    if cp.received >= cp.total:
        raise HTTPException(400, "优惠券已抢光")
    exists = db.query(models.UserCoupon).filter_by(user_id=user.id, coupon_id=coupon_id).count()
    if exists:
        raise HTTPException(400, "已领取过该优惠券")
    db.add(models.UserCoupon(user_id=user.id, coupon_id=coupon_id))
    cp.received += 1
    db.commit()
    return {"ok": True}
