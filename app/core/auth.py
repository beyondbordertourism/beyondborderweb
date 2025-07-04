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
    """Authenticate admin using config."""
    if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
        return {
            "username": username,
            "email": "admin@visaguide.com",
            "full_name": "System Administrator",
            "is_super_admin": True
        }
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
    if not username or username != config.ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    return {
        "username": username,
        "email": "admin@visaguide.com",
        "full_name": "System Administrator",
        "is_super_admin": True,
        "id": "config_admin"
    }

async def admin_required(current_admin: dict = Depends(get_current_admin)):
    return current_admin 