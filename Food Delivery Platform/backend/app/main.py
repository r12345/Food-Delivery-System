import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import CORS_ORIGINS, IS_DEFAULT_SECRET, UPLOAD_DIR
from .db import Base, SessionLocal, engine
from .seed import seed

logger = logging.getLogger("food-delivery")
logging.basicConfig(level=logging.INFO)

os.makedirs(UPLOAD_DIR, exist_ok=True)

if IS_DEFAULT_SECRET:
    logger.warning(
        "正在使用内置默认 SECRET_KEY，仅可用于本地演示；"
        "生产部署请设置环境变量 SECRET_KEY。"
    )

# 建表（若为 MySQL 存量库，建议先执行 docs/sql/schema.sql）
Base.metadata.create_all(bind=engine)

# 写入种子数据（幂等：库中已有用户则跳过）
_db = SessionLocal()
try:
    seed(_db)
except Exception:
    _db.rollback()
    logger.exception("种子数据写入失败，已回滚")
finally:
    _db.close()

app = FastAPI(title="外卖平台 API", version="1.0.0")

# 修正：allow_origins=["*"] 与 allow_credentials=True 并用不符合 CORS 规范，
# 且会导致任意站点携带用户凭据跨域调用。这里改为显式白名单。
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

from .api import admin, auth, common, consumer, merchant, user_api, ws  # noqa: E402

app.include_router(auth.router, prefix="/api")
app.include_router(common.router, prefix="/api")
app.include_router(consumer.router, prefix="/api")
app.include_router(user_api.router, prefix="/api")
app.include_router(merchant.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(ws.router)


@app.get("/api/health")
def health():
    """健康检查：顺带探测数据库连通性，便于排查连接问题。"""
    from sqlalchemy import text

    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"status": "ok", "database": "up" if db_ok else "down"}
