from typing import List, Optional
from bson import ObjectId
from pymongo import ReturnDocument
from passlib.context import CryptContext
from app.core.database import get_database
from app.models.admin import AdminUser, AdminUserCreate, AdminUserUpdate, AdminUserResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AdminUserCRUD:
    pass

admin_crud = AdminUserCRUD() 