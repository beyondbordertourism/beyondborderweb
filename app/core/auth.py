from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer
import jwt
import config

security = HTTPBearer(auto_error=False)

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

async def authenticate_admin(username: str, password: str):
    """Authenticate admin using MongoDB."""
    from app.crud.admin import admin_crud
    
    try:
        admin = admin_crud.get_by_username(username)
        if not admin:
            return None
        
        if not admin.get('is_active'):
            return None
        
        if not admin_crud.verify_password(password, admin['password_hash']):
            return None
        
        admin_crud.update_last_login(username)
        
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
    from app.crud.admin import admin_crud
    
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
    
    admin = admin_crud.get_by_username(username)
    if not admin or not admin.get('is_active'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    return {
        "id": admin['id'],
        "username": admin['username'],
        "email": admin['email'],
        "full_name": admin.get('full_name'),
        "is_super_admin": admin.get('is_super_admin', False)
    }

async def admin_required(current_admin: dict = Depends(get_current_admin)):
    return current_admin 