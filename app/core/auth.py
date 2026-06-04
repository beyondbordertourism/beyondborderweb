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
    """Authenticate admin — fully async, no sync wrapper."""
    try:
        collection = _get_admin_collection()
        admin = await collection.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
        if not admin:
            return None
        if not admin.get('is_active', True):
            return None
        if not pwd_context.verify(password, admin['password_hash']):
            return None
        await collection.update_one(
            {"username": username},
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
        print(f"Auth error: {e}")
        return None

async def get_current_admin(request: Request, admin_token: Optional[str] = Cookie(None)):
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(admin_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    try:
        collection = _get_admin_collection()
        admin = await collection.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
    except Exception as e:
        print(f"get_current_admin DB error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if not admin or not admin.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

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
