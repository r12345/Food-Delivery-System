import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
    DB_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
else:
    DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'food.db')}"

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
