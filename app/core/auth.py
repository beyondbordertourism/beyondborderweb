from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer
from passlib.context import CryptContext
import jwt
import config

security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.exceptions.InvalidTokenError:
        return None

def _get_admin_collection():
    from app.core.database import db
    if db.adapter is None:
        raise RuntimeError("Database not connected")
    return db.adapter["admin_users"]

def _normalize(doc: dict) -> dict:
    if doc and '_id' in doc:
        doc['id'] = str(doc['_id'])
        del doc['_id']
    return doc

async def authenticate_admin(username: str, password: str):
    """Authenticate admin — DB lookup with env-var fallback."""
    import re as _re

    # --- 1. Try MongoDB ---
    try:
        collection = _get_admin_collection()
        safe = _re.escape(username)
        admin = await collection.find_one({"username": {"$regex": f"^{safe}$", "$options": "i"}})
        if admin:
            print(f"[auth] Found DB user: {admin.get('username')}, active={admin.get('is_active')}")
            if not admin.get('is_active', True):
                print("[auth] User inactive")
                return None
            match = pwd_context.verify(password, admin['password_hash'])
            print(f"[auth] Password match: {match}")
            if not match:
                # password in DB is stale — try env-var fallback before giving up
                cfg_user = getattr(config, 'ADMIN_USERNAME', '')
                cfg_pass = getattr(config, 'ADMIN_PASSWORD', '')
                if username.lower() == cfg_user.lower() and password == cfg_pass:
                    print("[auth] DB hash stale, matched env-var credentials — updating hash")
                    new_hash = pwd_context.hash(password)
                    await collection.update_one({"_id": admin["_id"]}, {"$set": {"password_hash": new_hash}})
                else:
                    return None
            await collection.update_one(
                {"_id": admin["_id"]},
                {"$set": {"last_login": datetime.utcnow(), "updated_at": datetime.utcnow()},
                 "$inc": {"login_count": 1}}
            )
            admin = _normalize(admin)
            return {
                "id": admin['id'],
                "username": admin['username'],
                "email": admin['email'],
                "full_name": admin.get('full_name'),
                "is_super_admin": admin.get('is_super_admin', False)
            }
    except Exception as e:
        print(f"[auth] DB lookup error: {e}")

    # --- 2. Fallback: match directly against env vars ---
    cfg_user = getattr(config, 'ADMIN_USERNAME', '')
    cfg_pass = getattr(config, 'ADMIN_PASSWORD', '')
    print(f"[auth] No DB user found, trying env-var fallback. cfg_user={cfg_user!r}")
    if username.lower() == cfg_user.lower() and password == cfg_pass:
        print("[auth] Env-var fallback matched — seeding user into DB")
        try:
            collection = _get_admin_collection()
            await collection.update_one(
                {"username": cfg_user},
                {"$set": {
                    "username": cfg_user,
                    "email": "admin@beyondborders.com",
                    "password_hash": pwd_context.hash(cfg_pass),
                    "full_name": "System Administrator",
                    "is_active": True,
                    "is_super_admin": True,
                    "updated_at": datetime.utcnow(),
                },
                 "$setOnInsert": {"login_count": 0, "created_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as e:
            print(f"[auth] Failed to seed user during fallback: {e}")
        return {
            "id": "env_admin",
            "username": cfg_user,
            "email": "admin@beyondborders.com",
            "full_name": "System Administrator",
            "is_super_admin": True,
        }

    print("[auth] All auth methods failed")
    return None

async def get_current_admin(request: Request, admin_token: Optional[str] = Cookie(None)):
    import re as _re
    if not admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = verify_token(admin_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    # Try DB lookup
    admin = None
    try:
        collection = _get_admin_collection()
        safe = _re.escape(username)
        admin = await collection.find_one({"username": {"$regex": f"^{safe}$", "$options": "i"}})
        print(f"[get_current_admin] DB lookup for '{username}': {'found' if admin else 'not found'}")
    except Exception as e:
        print(f"[get_current_admin] DB error: {e}")

    # Fallback: if token username matches env-var admin, trust the token
    if not admin:
        cfg_user = getattr(config, 'ADMIN_USERNAME', '')
        if username.lower() == cfg_user.lower():
            print(f"[get_current_admin] No DB user, but token matches env-var admin — allowing")
            return {
                "id": "env_admin",
                "username": cfg_user,
                "email": "admin@beyondborders.com",
                "full_name": "System Administrator",
                "is_super_admin": True,
            }
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    if not admin.get('is_active', True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    admin = _normalize(admin)
    return {
        "id": admin['id'],
        "username": admin['username'],
        "email": admin['email'],
        "full_name": admin.get('full_name'),
        "is_super_admin": admin.get('is_super_admin', False)
    }

async def admin_required(current_admin: dict = Depends(get_current_admin)):
    return current_admin
