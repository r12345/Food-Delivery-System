"""演示种子数据：账号 / 店铺 / 菜品 / 轮播 / 优惠券"""
from datetime import datetime, timedelta
from urllib.parse import quote

from . import models
from .security import hash_password


def img(prompt: str, size: str = "square") -> str:
    """通过文生图接口生成真实图片 URL"""
    return f"https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt={quote(prompt)}&image_size={size}"


def seed(db):
    if db.query(models.User).count():
        return

    # ---------- 商家分类 ----------
    cat_names = ["快餐便当", "奶茶甜品", "火锅烤肉", "面食小吃", "果蔬生鲜"]
    scs = [models.ShopCategory(name=n, icon=img(f"{n}店铺分类图标，扁平插画", "square")) for n in cat_names]
    db.add_all(scs)
    db.flush()

    # ---------- 账号 ----------
    admin = models.User(username="admin", password_hash=hash_password("admin123"),
                        nickname="平台管理员", role="admin")
    m1 = models.User(username="merchant1", password_hash=hash_password("123456"),
                     nickname="川湘居老板", phone="13800000001", role="merchant")
    m2 = models.User(username="merchant2", password_hash=hash_password("123456"),
                     nickname="茶语时光老板", phone="13800000002", role="merchant")
    m3 = models.User(username="merchant3", password_hash=hash_password("123456"),
                     nickname="渝味火锅老板", phone="13800000003", role="merchant")
    u1 = models.User(username="user1", password_hash=hash_password("123456"),
                     nickname="小明", phone="13900000001", role="user")
    u2 = models.User(username="user2", password_hash=hash_password("123456"),
                     nickname="小红", phone="13900000002", role="user")
    db.add_all([admin, m1, m2, m3, u1, u2])
    db.flush()

    # ---------- 店铺 ----------
    now = datetime.now()
    shop1 = models.Shop(
        owner_id=m1.id, category_id=scs[0].id, name="川湘居·家常菜",
        logo=img("川菜餐馆logo，红灯笼水墨风", "square"),
        cover=img("川菜餐厅门头，红灯笼热闹街景", "landscape_4_3"),
        description="地道川湘风味，每日现炒，食材新鲜直达", phone="010-88886666",
        address="北京市朝阳区幸福路12号", business_hours="09:00-21:30",
        min_price=20, delivery_fee=3, delivery_range=5, rating=4.8, sales=1286,
        status="approved", is_open=True)
    shop2 = models.Shop(
        owner_id=m2.id, category_id=scs[1].id, name="茶语时光·鲜果茶",
        logo=img("奶茶店logo，清新绿茶色调", "square"),
        cover=img("奶茶店柜台，鲜果茶杯特写", "landscape_4_3"),
        description="鲜果现萃，好茶新生", phone="010-66668888",
        address="北京市海淀区中关村大街8号", business_hours="10:00-22:00",
        min_price=15, delivery_fee=2, delivery_range=4, rating=4.9, sales=2310,
        status="approved", is_open=True)
    shop3 = models.Shop(
        owner_id=m3.id, category_id=scs[2].id, name="渝味火锅·市井店",
        logo=img("火锅店logo，红辣色调", "square"),
        cover=img("重庆火锅沸腾红汤特写", "landscape_4_3"),
        description="九宫格老火锅，市井味道", phone="010-33334444",
        address="北京市朝阳区望京街9号", business_hours="11:00-23:00",
        min_price=50, delivery_fee=5, delivery_range=6, rating=4.6, sales=0,
        status="pending", is_open=False)  # 待审核入驻
    db.add_all([shop1, shop2, shop3])
    db.flush()

    # ---------- 菜品分类 ----------
    fc1 = [models.FoodCategory(shop_id=shop1.id, name=n, sort=i)
           for i, n in enumerate(["热销推荐", "招牌小炒", "主食", "饮品"])]
    fc2 = [models.FoodCategory(shop_id=shop2.id, name=n, sort=i)
           for i, n in enumerate(["招牌奶茶", "鲜果茶", "小食甜品"])]
    db.add_all(fc1 + fc2)
    db.flush()

    def food(shop, cat, name, price, orig, desc, sales, specs=None, stock=100):
        return models.Food(
            shop_id=shop.id, category_id=cat.id, name=name, price=price,
            original_price=orig, image=img(f"{name}美食摄影，俯拍，诱人光线"),
            description=desc, stock=stock, sales=sales, specs=specs or [], status=1)

    db.add_all([
        food(shop1, fc1[0], "宫保鸡丁", 28, 32, "经典川味，花生脆香", 356),
        food(shop1, fc1[0], "鱼香肉丝", 26, 30, "酸甜适口，下饭神器", 289),
        food(shop1, fc1[1], "麻婆豆腐", 22, 0, "麻辣鲜香，嫩滑入味", 198),
        food(shop1, fc1[1], "酸辣土豆丝", 14, 16, "爽脆开胃", 176),
        food(shop1, fc1[2], "扬州炒饭", 18, 0, "粒粒分明，配料丰富", 240),
        food(shop1, fc1[2], "手工水饺(12只)", 20, 0, "现包现煮", 122,
             specs=[{"name": "馅料", "options": [{"name": "猪肉白菜", "price": 0}, {"name": "韭菜鸡蛋", "price": 1}]}]),
        food(shop1, fc1[3], "冰镇酸梅汤", 6, 8, "解辣解腻", 310),
        food(shop2, fc2[0], "珍珠奶茶", 12, 15, "Q弹珍珠，醇香奶茶", 520,
             specs=[{"name": "温度", "options": [{"name": "常温", "price": 0}, {"name": "去冰", "price": 0}, {"name": "少冰", "price": 0}]},
                    {"name": "甜度", "options": [{"name": "标准糖", "price": 0}, {"name": "半糖", "price": 0}, {"name": "三分糖", "price": 0}]}]),
        food(shop2, fc2[0], "芝士奶盖茶", 16, 18, "浓郁芝士，茶香四溢", 344,
             specs=[{"name": "甜度", "options": [{"name": "标准糖", "price": 0}, {"name": "半糖", "price": 0}]}]),
        food(shop2, fc2[1], "杨枝甘露", 18, 0, "芒果西柚西米露", 410),
        food(shop2, fc2[1], "满杯百香果", 13, 0, "维C满满", 288),
        food(shop2, fc2[2], "葡式蛋挞(2只)", 8, 10, "酥皮嫩滑", 199),
    ])

    # ---------- 轮播 ----------
    db.add_all([
        models.Banner(title="新品上市 鲜果茶第二杯半价", image=img("奶茶促销广告横幅，鲜果茶与清新背景", "landscape_16_9"), link="", sort=0),
        models.Banner(title="川湘居 招牌小炒满30减5", image=img("川菜促销广告横幅，辣椒炒菜热烈氛围", "landscape_16_9"), link="", sort=1),
        models.Banner(title="夜宵狂欢 火锅烧烤5折起", image=img("夜宵烧烤促销广告横幅，霓虹灯氛围", "landscape_16_9"), link="", sort=2),
    ])

    # ---------- 优惠券 ----------
    db.add_all([
        models.Coupon(shop_id=0, name="平台新人券 满30减8", threshold=30, amount=8,
                      start_time=now - timedelta(days=1), end_time=now + timedelta(days=30),
                      total=500, received=0),
        models.Coupon(shop_id=shop1.id, name="川湘居 满25减5", threshold=25, amount=5,
                      start_time=now - timedelta(days=1), end_time=now + timedelta(days=15),
                      total=100, received=0),
        models.Coupon(shop_id=shop2.id, name="茶语时光 满20减4", threshold=20, amount=4,
                      start_time=now - timedelta(days=1), end_time=now + timedelta(days=15),
                      total=200, received=0),
    ])

    # ---------- 地址 / 收藏 / 骑手 / 通知 ----------
    db.add_all([
        models.Address(user_id=u1.id, name="小明", phone="13900000001", gender="先生",
                       region="北京市 朝阳区", detail="幸福路12号院3号楼502", is_default=True),
        models.Address(user_id=u1.id, name="小明(公司)", phone="13900000001", gender="先生",
                       region="北京市 海淀区", detail="中关村大街8号A座1101", is_default=False),
        models.Address(user_id=u2.id, name="小红", phone="13900000002", gender="女士",
                       region="北京市 朝阳区", detail="望京街9号花园小区6-1-301", is_default=True),
        models.Favorite(user_id=u1.id, shop_id=shop2.id),
        models.Rider(name="王师傅", phone="13700000001", status=1),
        models.Rider(name="李师傅", phone="13700000002", status=1),
        models.Notification(user_id=u1.id, title="欢迎使用乐享外卖",
                            content="新用户注册即领 ¥8 平台券，下单立减"),
    ])

    db.commit()
