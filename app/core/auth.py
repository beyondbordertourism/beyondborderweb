from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
import config
from app.crud.admin import admin_crud

security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

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
    except JWTError:
        return None

async def authenticate_admin(username: str, password: str):
    """Authenticate admin using MongoDB"""
    admin_user = await admin_crud.authenticate(username, password)
    if admin_user:
        return admin_user
    
    # Fallback to config-based authentication for backward compatibility
    if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
        # Try to create/get admin user in MongoDB
        try:
            existing_admin = await admin_crud.get_by_username(username)
            if not existing_admin:
                # Create admin user in MongoDB
                from app.models.admin import AdminUserCreate
                admin_data = AdminUserCreate(
                    username=username,
                    email="admin@visaguide.com",
                    full_name="System Administrator",
                    password=password,
                    is_super_admin=True
                )
                await admin_crud.create(admin_data)
        except Exception as e:
            print(f"Warning: Could not create admin user in MongoDB: {e}")
        
        # Return a mock admin user for backward compatibility
        from app.models.admin import AdminUser
        return AdminUser(
            username=username,
            email="admin@visaguide.com",
            full_name="System Administrator",
            password_hash="",
            is_super_admin=True
        )
    
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
    
    # Try to get admin from MongoDB
    admin_user = await admin_crud.get_by_username(username)
    if admin_user and admin_user.is_active:
        return {
            "username": admin_user.username,
            "email": admin_user.email,
            "full_name": admin_user.full_name,
            "is_super_admin": admin_user.is_super_admin,
            "id": str(admin_user.id)
        }
    
    # Fallback for config-based admin
    if username == config.ADMIN_USERNAME:
        return {
            "username": username,
            "email": "admin@visaguide.com",
            "full_name": "System Administrator",
            "is_super_admin": True,
            "id": "config_admin"
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

async def admin_required(current_admin: dict = Depends(get_current_admin)):
    return current_admin 