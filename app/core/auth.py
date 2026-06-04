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


def _cfg_admin():
    return (
        getattr(config, 'ADMIN_USERNAME', 'admin'),
        getattr(config, 'ADMIN_PASSWORD', 'admin123'),
    )


def _get_col():
    from app.core.database import db
    if db.adapter is None:
        raise RuntimeError("Database not connected")
    return db.adapter["admin_users"]


def _fmt(doc: dict) -> dict:
    if not doc:
        return {}
    doc = dict(doc)
    if '_id' in doc:
        doc['id'] = str(doc.pop('_id'))
    return doc


async def _find_admin(username: str):
    col = _get_col()
    safe = _re.escape(username)
    return await col.find_one({"username": {"$regex": f"^{safe}$", "$options": "i"}})


async def authenticate_admin(username: str, password: str):
    cfg_user, cfg_pass = _cfg_admin()

    # --- 1. Check env-var credentials first (always works, no DB needed) ---
    env_match = (username.lower() == cfg_user.lower() and password == cfg_pass)
    print(f"[auth] env_match={env_match} for username={username!r}")

    # --- 2. Try DB lookup and bcrypt verify ---
    try:
        admin = await _find_admin(username)
        if admin:
            print(f"[auth] DB user found: {admin.get('username')}")
            if admin.get('is_active', True) and pwd_context.verify(password, admin['password_hash']):
                # Update last login (best-effort)
                try:
                    col = _get_col()
                    await col.update_one(
                        {"_id": admin["_id"]},
                        {"$set": {"last_login": datetime.utcnow()}, "$inc": {"login_count": 1}},
                    )
                except Exception:
                    pass
                admin = _fmt(admin)
                return {
                    "id": admin['id'],
                    "username": admin['username'],
                    "email": admin.get('email', ''),
                    "full_name": admin.get('full_name'),
                    "is_super_admin": admin.get('is_super_admin', False),
                }
    except Exception as e:
        print(f"[auth] DB lookup error: {e}")

    # --- 3. Fall back to env-var credentials ---
    if env_match:
        print("[auth] Env-var credentials matched — issuing token")
        # Best-effort DB seed so future logins can use bcrypt
        try:
            col = _get_col()
            await col.update_one(
                {"username": cfg_user},
                {"$set": {
                    "username": cfg_user,
                    "email": "admin@beyondborders.com",
                    "password_hash": pwd_context.hash(cfg_pass),
                    "full_name": "System Administrator",
                    "is_active": True,
                    "is_super_admin": True,
                    "updated_at": datetime.utcnow(),
                }},
                upsert=True,
            )
            print("[auth] DB seed succeeded")
        except Exception as e:
            print(f"[auth] DB seed failed (non-fatal): {e}")

        return {
            "id": "env_admin",
            "username": cfg_user,
            "email": "admin@beyondborders.com",
            "full_name": "System Administrator",
            "is_super_admin": True,
        }

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

    # Try DB first
    try:
        admin = await _find_admin(username)
        if admin and admin.get('is_active', True):
            admin = _fmt(admin)
            return {
                "id": admin['id'],
                "username": admin['username'],
                "email": admin.get('email', ''),
                "full_name": admin.get('full_name'),
                "is_super_admin": admin.get('is_super_admin', False),
            }
    except Exception as e:
        print(f"[get_current_admin] DB error: {e}")

    # DB unavailable or user not seeded yet — trust the JWT if username matches env-var
    # Security: JWT is signed with SECRET_KEY; forging requires the secret.
    # Password was verified at token-issuance time.
    cfg_user, _ = _cfg_admin()
    if username.lower() == cfg_user.lower():
        print(f"[get_current_admin] DB miss, trusting valid JWT for env-var admin '{username}'")
        return {
            "id": "env_admin",
            "username": cfg_user,
            "email": "admin@beyondborders.com",
            "full_name": "System Administrator",
            "is_super_admin": True,
        }

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")


async def admin_required(current_admin: dict = Depends(get_current_admin)):
    return current_admin
