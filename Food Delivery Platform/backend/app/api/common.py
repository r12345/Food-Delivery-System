import os
import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models
from ..config import UPLOAD_DIR
from ..db import get_db
from ..deps import get_current_user

router = APIRouter(tags=["公共"])

# ---------- 省市区字典 ----------
REGIONS = [
    {"name": "北京市", "children": [{"name": "北京市", "children": ["东城区", "西城区", "朝阳区", "海淀区", "丰台区"]}]},
    {"name": "上海市", "children": [{"name": "上海市", "children": ["黄浦区", "徐汇区", "静安区", "浦东新区", "杨浦区"]}]},
    {"name": "广东省", "children": [
        {"name": "广州市", "children": ["天河区", "越秀区", "海珠区", "白云区"]},
        {"name": "深圳市", "children": ["南山区", "福田区", "罗湖区", "宝安区"]}]},
    {"name": "浙江省", "children": [
        {"name": "杭州市", "children": ["西湖区", "滨江区", "拱墅区", "余杭区"]},
        {"name": "宁波市", "children": ["海曙区", "江北区", "鄞州区"]}]},
    {"name": "四川省", "children": [
        {"name": "成都市", "children": ["锦江区", "青羊区", "武侯区", "高新区"]},
        {"name": "绵阳市", "children": ["涪城区", "游仙区"]}]},
]

DICTS = {
    "order_status": [
        {"value": "pending_pay", "label": "待付款"}, {"value": "pending_accept", "label": "待接单"},
        {"value": "preparing", "label": "备餐中"}, {"value": "delivering", "label": "配送中"},
        {"value": "completed", "label": "已完成"}, {"value": "cancelled", "label": "已取消"},
        {"value": "refunding", "label": "退款中"}, {"value": "refunded", "label": "已退款"},
    ],
    "pay_type": [{"value": "wechat", "label": "微信支付"}, {"value": "alipay", "label": "支付宝"}],
    "shop_status": [
        {"value": "pending", "label": "待审核"}, {"value": "approved", "label": "已通过"},
        {"value": "rejected", "label": "已驳回"}, {"value": "banned", "label": "已封禁"},
    ],
    "coupon_type": [{"value": "full", "label": "满减券"}],
}


@router.post("/upload", tags=["文件上传"])
async def upload(file: UploadFile, user: models.User = Depends(get_current_user)):
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"):
        raise HTTPException(400, "仅支持图片格式")
    name = f"{int(time.time() * 1000)}_{user.id}{ext}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
        f.write(await file.read())
    return {"url": f"/uploads/{name}"}


@router.get("/regions")
def regions():
    return REGIONS


@router.get("/dicts/{key}")
def dicts(key: str):
    return DICTS.get(key, [])


# ---------- 站内消息 ----------
@router.get("/notifications")
def notifications(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    q = db.query(models.Notification).filter_by(user_id=user.id).order_by(models.Notification.id.desc())
    items = q.limit(50).all()
    unread = q.filter_by(is_read=False).count()
    return {"list": [n.to_dict() for n in items], "unread": unread}


@router.post("/notifications/read")
def read_notifications(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db.query(models.Notification).filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.commit()
    return {"ok": True}
