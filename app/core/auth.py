from datetime import datetime, timedelta
from typing import Optional
import re as _re
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
import jwt
import config

security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.exceptions.InvalidTokenError:
        return None


def _get_col():
    from app.core.database import db
    if db.adapter is None:
        raise RuntimeError("Database not connected")
    return db.adapter["admin_users"]


def _fmt(doc: dict) -> dict:
    """Return a plain dict with 'id' instead of '_id'."""
    if not doc:
        return doc
    doc = dict(doc)          # don't mutate the original
    if '_id' in doc:
        doc['id'] = str(doc.pop('_id'))
    return doc


async def _find_admin(username: str):
    """Case-insensitive username lookup. Returns raw doc or None."""
    col = _get_col()
    safe = _re.escape(username)
    return await col.find_one({"username": {"$regex": f"^{safe}$", "$options": "i"}})


async def _upsert_admin(username: str, password: str) -> dict:
    """Create or overwrite the admin record with a fresh bcrypt hash."""
    col = _get_col()
    now = datetime.utcnow()
    new_hash = pwd_context.hash(password)
    # update_one with upsert is simpler and doesn't need ReturnDocument
    await col.update_one(
        {"username": username},
        {
            "$set": {
                "username": username,
                "email": "admin@beyondborders.com",
                "password_hash": new_hash,
                "full_name": "System Administrator",
                "is_active": True,
                "is_super_admin": True,
                "updated_at": now,
            },
            "$setOnInsert": {"login_count": 0, "created_at": now},
        },
        upsert=True,
    )
    # read back what we just wrote
    doc = await col.find_one({"username": username})
    return _fmt(doc) if doc else {}


async def authenticate_admin(username: str, password: str):
    cfg_user = getattr(config, 'ADMIN_USERNAME', 'admin')
    cfg_pass = getattr(config, 'ADMIN_PASSWORD', 'admin123')

    try:
        # --- 1. Look up in DB ---
        admin = await _find_admin(username)

        if admin:
            print(f"[auth] DB user found: {admin.get('username')}")
            if not admin.get('is_active', True):
                print("[auth] User is inactive")
                return None

            if pwd_context.verify(password, admin['password_hash']):
                # Correct password — update last_login and return
                col = _get_col()
                await col.update_one(
                    {"_id": admin["_id"]},
                    {"$set": {"last_login": datetime.utcnow(), "updated_at": datetime.utcnow()},
                     "$inc": {"login_count": 1}},
                )
                admin = _fmt(admin)
                return {
                    "id": admin['id'],
                    "username": admin['username'],
                    "email": admin.get('email', ''),
                    "full_name": admin.get('full_name'),
                    "is_super_admin": admin.get('is_super_admin', False),
                }

            # Hash is stale — only accept if env-var credentials match
            print("[auth] bcrypt mismatch — checking env-var credentials")
            if username.lower() == cfg_user.lower() and password == cfg_pass:
                print("[auth] Env-var match — refreshing hash in DB")
                doc = await _upsert_admin(cfg_user, cfg_pass)
                return {
                    "id": doc.get('id', 'admin'),
                    "username": cfg_user,
                    "email": doc.get('email', 'admin@beyondborders.com'),
                    "full_name": doc.get('full_name', 'System Administrator'),
                    "is_super_admin": True,
                }
            return None

        # --- 2. No DB record — fall back to env vars ---
        print(f"[auth] No DB record, trying env-var fallback (cfg_user={cfg_user!r})")
        if username.lower() == cfg_user.lower() and password == cfg_pass:
            print("[auth] Env-var match — seeding DB")
            doc = await _upsert_admin(cfg_user, cfg_pass)
            return {
                "id": doc.get('id', 'admin'),
                "username": cfg_user,
                "email": "admin@beyondborders.com",
                "full_name": "System Administrator",
                "is_super_admin": True,
            }

    except Exception as e:
        print(f"[auth] authenticate_admin error: {e}")

    print("[auth] Authentication failed")
    return None


async def get_current_admin(request: Request, admin_token: Optional[str] = Cookie(None)):
    if not admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = verify_token(admin_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        admin = await _find_admin(username)
        print(f"[get_current_admin] '{username}': {'found' if admin else 'not found'}")
    except Exception as e:
        print(f"[get_current_admin] DB error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if not admin or not admin.get('is_active', True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    admin = _fmt(admin)
    return {
        "id": admin['id'],
        "username": admin['username'],
        "email": admin.get('email', ''),
        "full_name": admin.get('full_name'),
        "is_super_admin": admin.get('is_super_admin', False),
    }


async def admin_required(current_admin: dict = Depends(get_current_admin)):
    return current_admin
