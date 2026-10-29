from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DB_URL

_args = {"pool_pre_ping": True, "pool_recycle": 1800}
if DB_URL.startswith("sqlite"):
    # SQLite 仅用于本地演示：关闭线程检查，并加长超时避免并发写锁冲突
    _args["connect_args"] = {"check_same_thread": False, "timeout": 15}
else:
    # MySQL：显式设定连接池，避免默认 5 连接在高并发下排队等待
    _args.update({"pool_size": 10, "max_overflow": 20, "pool_timeout": 30})

engine = create_engine(DB_URL, **_args)

if DB_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_pragma(dbapi_conn, _):
        """SQLite 默认不开启外键约束，也不支持并发写；显式打开外键并启用 WAL。"""
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI 依赖：每请求一个会话，异常时回滚，最终必关闭。"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
