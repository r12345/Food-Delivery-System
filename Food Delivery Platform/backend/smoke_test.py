"""端到端冒烟测试：登录 → 下单 → 支付 → 接单 → 出餐 → 完成 → 评价"""
import base64
import json
import re
import urllib.request

BASE = "http://127.0.0.1:8000"


def req(method, path, data=None, token=None, q=""):
    from urllib.parse import quote
    url = BASE + path + (f"?{quote(q, safe='=&')}" if q else "")
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())


def login(username, password):
    cap = req("GET", "/api/auth/captcha")
    svg = base64.b64decode(cap["image"].split(",")[1]).decode()
    code = re.search(r">(\d{4})<", svg).group(1)
    res = req("POST", "/api/auth/login", {
        "username": username, "password": password,
        "captcha_id": cap["captcha_id"], "captcha_code": code})
    return res["access_token"], res["user"]


ok, fail = 0, 0


def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"[PASS] {name}")
    else:
        fail += 1
        print(f"[FAIL] {name} {detail}")


# 1. 健康检查 & 首页
check("health", req("GET", "/api/health")["status"] == "ok")
home = req("GET", "/api/home")
check("home", len(home["hot_shops"]) >= 1 and len(home["banners"]) >= 1)

# 2. 用户登录
ut, user = login("user1", "123456")
check("user login", user["role"] == "user")

# 3. 店铺列表/详情
shops = req("GET", "/api/shops", q="keyword=川湘")
check("shop search", shops["total"] >= 1)
sid = shops["list"][0]["id"]
shop = req("GET", f"/api/shops/{sid}")
check("shop detail", len(shop["menu"]) >= 1)
food = shop["menu"][0]["foods"][0]

# 4. 购物车
req("POST", "/api/cart", {"food_id": food["id"], "quantity": 2}, ut)
req("POST", "/api/cart", {"food_id": food["id"], "quantity": 1,
                          "spec": (food.get("specs") or [{}])[0].get("options", [{}])[0].get("name", "")}, ut)
cart = req("GET", "/api/cart", token=ut)
check("cart", len(cart["list"]) >= 1)

# 5. 地址 + 优惠券 + 下单
addr = req("GET", "/api/user/addresses", token=ut)["list"][0]
cps = req("GET", "/api/user/coupons", q="status=unused", token=ut)["list"]
cp_id = cps[0]["uc_id"] if cps else 0
order = req("POST", "/api/orders", {
    "address_id": addr["id"], "shop_id": sid, "remark": "少辣",
    "pay_type": "wechat", "coupon_id": cp_id}, ut)
check("create order", order["status"] == "pending_pay" and order["items"], order)

# 6. 支付
paid = req("POST", f"/api/orders/{order['id']}/pay", {"pay_type": "wechat"}, ut)
check("pay order", paid["status"] == "pending_accept")

# 7. 商家接单 → 出餐
mt, muser = login("merchant1", "123456")
check("merchant login", muser["role"] == "merchant")
morders = req("GET", "/api/merchant/orders", q="status=pending_accept", token=mt)
check("merchant sees order", morders["total"] >= 1)
acc = req("POST", f"/api/merchant/orders/{order['id']}/accept", {}, mt)
check("accept", acc["status"] == "preparing")
dlv = req("POST", f"/api/merchant/orders/{order['id']}/deliver", {}, mt)
check("deliver", dlv["status"] == "delivering")

# 8. 用户确认收货 → 评价
cfm = req("POST", f"/api/orders/{order['id']}/confirm", {}, ut)
check("confirm", cfm["status"] == "completed")
ev = req("POST", f"/api/orders/{order['id']}/evaluation",
         {"shop_rating": 5, "rider_rating": 4.5, "content": "很好吃"}, ut)
check("evaluate", ev["shop_rating"] == 5)
evs = req("GET", f"/api/shops/{sid}/evaluations")
check("shop evaluations", evs["total"] >= 1)
reply = req("POST", f"/api/merchant/evaluations/{ev['id']}/reply", {"reply": "欢迎再来"}, mt)
check("merchant reply", reply["reply"] == "欢迎再来")

# 9. 商家财务 + 优惠券
fin = req("GET", "/api/merchant/finance/summary", token=mt)
check("finance", fin["today_amount"] > 0, fin)
mcp = req("POST", "/api/merchant/coupons", {
    "name": "测试券 满50减10", "threshold": 50, "amount": 10,
    "start_time": "2026-01-01 00:00:00", "end_time": "2026-12-31 23:59:59", "total": 10}, mt)
check("merchant coupon", mcp["shop_id"] == sid)

# 10. 管理端
at, auser = login("admin", "admin123")
check("admin login", auser["role"] == "admin")
pending = req("GET", "/api/admin/shops", q="status=pending", token=at)
check("pending shops", pending["total"] >= 1)
audited = req("POST", f"/api/admin/shops/{pending['list'][0]['id']}/audit", {"action": "approved"}, at)
check("audit shop", audited["status"] == "approved")
ov = req("GET", "/api/admin/stats/overview", token=at)
check("stats overview", ov["total_orders"] >= 1)
trend = req("GET", "/api/admin/stats/trend", token=at)
check("stats trend", len(trend["list"]) == 7)
users = req("GET", "/api/admin/users", q="role=user", token=at)
check("admin users", users["total"] >= 2)
riders = req("POST", "/api/admin/riders", {"name": "测试骑手", "phone": "13000000000"}, at)
check("add rider", riders["id"] > 0)
banners = req("GET", "/api/admin/banners", token=at)
check("admin banners", len(banners["list"]) >= 1)

print(f"\n===== 冒烟测试完成: {ok} 通过, {fail} 失败 =====")
