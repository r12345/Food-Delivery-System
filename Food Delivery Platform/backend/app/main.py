import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import UPLOAD_DIR
from .db import Base, SessionLocal, engine
from .seed import seed

os.makedirs(UPLOAD_DIR, exist_ok=True)

Base.metadata.create_all(bind=engine)
_db = SessionLocal()
try:
    seed(_db)
finally:
    _db.close()

app = FastAPI(title="外卖平台 API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
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
    return {"status": "ok", "time": os.environ.get("TZ", "")}
