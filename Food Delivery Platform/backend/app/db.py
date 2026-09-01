from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DB_URL

_args = {"pool_pre_ping": True, "pool_recycle": 1800}
if DB_URL.startswith("sqlite"):
    _args["connect_args"] = {"check_same_thread": False}

engine = create_engine(DB_URL, **_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
