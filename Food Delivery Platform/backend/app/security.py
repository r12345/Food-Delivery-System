import base64
import hashlib
import random
import secrets
import string
import time

import jwt

from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE, REFRESH_TOKEN_EXPIRE


# ---------- 密码加密(PBKDF2-SHA256) ----------
def hash_password(pwd: str) -> str:
    salt = secrets.token_hex(8)
    h = hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt.encode(), 100000).hex()
    return f"{salt}${h}"


def verify_password(pwd: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$", 1)
    except ValueError:
        return False
    return hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt.encode(), 100000).hex() == h


# ---------- JWT ----------
def create_token(user_id: int, role: str, token_type: str = "access") -> str:
    expire = int(time.time()) + (ACCESS_TOKEN_EXPIRE if token_type == "access" else REFRESH_TOKEN_EXPIRE)
    return jwt.encode(
        {"sub": str(user_id), "role": role, "type": token_type, "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ---------- 图形验证码(SVG) ----------
_CAPTCHAS: dict[str, tuple[str, float]] = {}


def make_captcha() -> tuple[str, str]:
    code = "".join(random.choices(string.digits, k=4))
    cid = secrets.token_hex(8)
    _CAPTCHAS[cid] = (code, time.time() + 300)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="34">'
        '<rect width="100%" height="100%" fill="#f0f2f5"/>'
        f'<text x="12" y="25" font-size="22" letter-spacing="7" fill="#409eff" '
        f'font-family="Arial">{code}</text></svg>'
    )
    b64 = base64.b64encode(svg.encode()).decode()
    return cid, "data:image/svg+xml;base64," + b64


def check_captcha(cid: str, code: str) -> bool:
    if not cid:
        return False
    item = _CAPTCHAS.pop(cid, None)
    return bool(item and item[1] > time.time() and item[0] == code)
