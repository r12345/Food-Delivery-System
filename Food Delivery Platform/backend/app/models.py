from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)

from .db import Base


class Mixin:
    def to_dict(self) -> dict:
        d = {}
        for c in self.__table__.columns:
            v = getattr(self, c.name)
            if isinstance(v, datetime):
                v = v.strftime("%Y-%m-%d %H:%M:%S")
            d[c.name] = v
        return d


# ================= 用户 / 管理员（role 区分：user / merchant / admin） =================
class User(Mixin, Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    nickname = Column(String(50), default="")
    phone = Column(String(20), default="")
    email = Column(String(100), default="")
    avatar = Column(String(255), default="")
    role = Column(String(20), default="user")   # user 普通用户 / merchant 商家 / admin 管理员
    status = Column(Integer, default=1)         # 1 正常 0 禁用
    created_at = Column(DateTime, default=datetime.now)


# ================= 店铺 =================
class ShopCategory(Mixin, Base):
    __tablename__ = "shop_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(255), default="")


class Shop(Mixin, Base):
    __tablename__ = "shops"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)
    category_id = Column(Integer, default=0)
    name = Column(String(100), nullable=False)
    logo = Column(String(255), default="")
    cover = Column(String(255), default="")
    description = Column(String(500), default="")
    phone = Column(String(20), default="")
    address = Column(String(255), default="")
    business_hours = Column(String(50), default="09:00-21:00")
    min_price = Column(Float, default=0)        # 起送价
    delivery_fee = Column(Float, default=0)     # 配送费
    delivery_range = Column(Float, default=3)   # 配送范围(km)
    rating = Column(Float, default=5.0)
    sales = Column(Integer, default=0)          # 月售订单数
    status = Column(String(20), default="pending")  # pending 待审核 / approved 通过 / rejected 驳回 / banned 封禁
    is_open = Column(Boolean, default=True)     # 营业中
    created_at = Column(DateTime, default=datetime.now)


# ================= 菜品 =================
class FoodCategory(Mixin, Base):
    __tablename__ = "food_categories"
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), index=True)
    name = Column(String(50), nullable=False)
    sort = Column(Integer, default=0)


class Food(Mixin, Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), index=True)
    category_id = Column(Integer, ForeignKey("food_categories.id"))
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float, default=0)
    image = Column(String(255), default="")
    description = Column(String(500), default="")
    stock = Column(Integer, default=100)
    sales = Column(Integer, default=0)
    specs = Column(JSON, default=list)          # 多规格/加料: [{"name":"份量","options":[{"name":"大份","price":3}]}]
    status = Column(Integer, default=1)         # 1 上架 0 下架
    created_at = Column(DateTime, default=datetime.now)


# ================= 购物车 =================
class Cart(Mixin, Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    food_id = Column(Integer, ForeignKey("foods.id"))
    quantity = Column(Integer, default=1)
    spec = Column(String(100), default="")      # 所选规格文本
    unit_price = Column(Float, default=0)       # 含规格加价的单价


# ================= 收货地址 =================
class Address(Mixin, Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    gender = Column(String(10), default="先生")
    region = Column(String(100), default="")
    detail = Column(String(255), nullable=False)
    is_default = Column(Boolean, default=False)


class Favorite(Mixin, Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    created_at = Column(DateTime, default=datetime.now)


# ================= 订单 =================
class Order(Mixin, Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), index=True)
    address = Column(JSON)                      # 下单时地址快照 {name,phone,region,detail}
    status = Column(String(20), default="pending_pay", index=True)
    # pending_pay待付款 / pending_accept待接单 / preparing备餐中 / delivering配送中
    # completed已完成 / cancelled已取消 / refunding退款中 / refunded已退款
    total_amount = Column(Float, default=0)     # 菜品合计
    delivery_fee = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    pay_amount = Column(Float, default=0)       # 实付
    pay_type = Column(String(20), default="")   # wechat / alipay
    pay_time = Column(DateTime)
    remark = Column(String(255), default="")
    cancel_reason = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.now)


class OrderItem(Mixin, Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True)
    food_id = Column(Integer, default=0)
    food_name = Column(String(100))
    image = Column(String(255), default="")
    price = Column(Float, default=0)
    quantity = Column(Integer, default=1)
    spec = Column(String(100), default="")


# ================= 优惠券 =================
class Coupon(Mixin, Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, index=True, default=0)  # 0=平台券，>0=店铺券（不设FK，MySQL不允许shop_id=0）
    name = Column(String(100), nullable=False)
    type = Column(String(20), default="full")   # full 满减
    threshold = Column(Float, default=0)        # 使用门槛
    amount = Column(Float, default=0)           # 优惠金额
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)
    total = Column(Integer, default=100)        # 发放总量
    received = Column(Integer, default=0)       # 已领取
    status = Column(Integer, default=1)         # 1 上架


class UserCoupon(Mixin, Base):
    __tablename__ = "user_coupons"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"))
    status = Column(String(20), default="unused")  # unused / used
    used_order_id = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


# ================= 评价 =================
class Evaluation(Mixin, Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    shop_id = Column(Integer, ForeignKey("shops.id"), index=True)
    shop_rating = Column(Float, default=5)
    rider_rating = Column(Float, default=5)
    content = Column(Text, default="")
    reply = Column(String(500), default="")     # 商家回复
    created_at = Column(DateTime, default=datetime.now)


# ================= 平台运营 =================
class Banner(Mixin, Base):
    __tablename__ = "banners"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), default="")
    image = Column(String(255), default="")
    link = Column(String(255), default="")
    sort = Column(Integer, default=0)
    status = Column(Integer, default=1)


class Rider(Mixin, Base):
    __tablename__ = "riders"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), default="")
    status = Column(Integer, default=1)         # 1 接单中 0 停用
    orders_count = Column(Integer, default=0)
    income = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)


class Notification(Mixin, Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String(100), default="")
    content = Column(String(500), default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class FinanceRecord(Mixin, Base):
    __tablename__ = "finance_records"
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), index=True)
    order_id = Column(Integer, default=0)
    type = Column(String(20))                   # order_income 收入 / refund 退款 / withdraw 提现
    amount = Column(Float, default=0)
    remark = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.now)
