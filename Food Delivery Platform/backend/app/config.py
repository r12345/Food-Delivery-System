import os
from urllib.parse import quote_plus

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 安全提示：生产环境必须通过环境变量覆盖 SECRET_KEY，否则 JWT 可被伪造
SECRET_KEY = os.getenv("SECRET_KEY", "food-delivery-platform-secret-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 30 * 60          # access token 30分钟
REFRESH_TOKEN_EXPIRE = 7 * 24 * 3600   # refresh token 7天

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "food")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "food123")
MYSQL_DB = os.getenv("MYSQL_DB", "food")

# 优先使用 MySQL；可通过 DB_DRIVER=sqlite 切回 SQLite
driver = os.getenv("DB_DRIVER", "mysql").lower()
if driver == "mysql":
    # 账号密码做 URL 编码，避免密码中含 @ : / 等字符时连接串被截断
    DB_URL = (
        f"mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )
else:
    DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'food.db')}"

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# 上传限制
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(5 * 1024 * 1024)))  # 单文件最大 5MB
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# CORS：默认仅放行本地前端开发端口；生产用真实域名覆盖
CORS_ORIGINS = [
    o.strip() for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",") if o.strip()
]

# 启动时若为默认密钥则给出警告（生产必须覆盖）
IS_DEFAULT_SECRET = "SECRET_KEY" not in os.environ
