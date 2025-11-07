from typing import List, Optional
from bson import ObjectId
from pymongo import ReturnDocument
from passlib.context import CryptContext
from app.core.database import db as core_db_instance
from app.models.admin import AdminUser, AdminUserCreate, AdminUserUpdate, AdminUserResponse
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AdminUserCRUD:
    def __init__(self):
        self.collection_name = "admin_users"
    
    def _get_collection(self):
        if core_db_instance.adapter is None:
            raise RuntimeError("Database not connected")
        return core_db_instance.adapter[self.collection_name]
    
    def _run_async(self, coro):
        loop = getattr(core_db_instance, 'loop', None)
        if not loop or loop.is_closed():
            raise RuntimeError("Database event loop is not available")
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def _normalize_admin(self, admin_doc: dict) -> dict:
        if admin_doc and '_id' in admin_doc:
            admin_doc['id'] = str(admin_doc['_id'])
            del admin_doc['_id']
        return admin_doc
    
    def create(self, admin_data: AdminUserCreate) -> AdminUser:
        return self._run_async(self._create_async(admin_data))
    
    async def _create_async(self, admin_data: AdminUserCreate):
        collection = self._get_collection()
        
        if await collection.find_one({"username": admin_data.username}):
            raise ValueError("Username already exists")
        
        if await collection.find_one({"email": admin_data.email}):
            raise ValueError("Email already exists")
        
        now = datetime.utcnow()
        admin_dict = {
            "username": admin_data.username,
            "email": admin_data.email,
            "password_hash": self.hash_password(admin_data.password),
            "full_name": admin_data.full_name,
            "is_active": True,
            "is_super_admin": admin_data.is_super_admin,
            "last_login": None,
            "login_count": 0,
            "created_at": now,
            "updated_at": now
        }
        
        result = await collection.insert_one(admin_dict)
        admin_dict['_id'] = result.inserted_id
        return self._normalize_admin(admin_dict)
    
    def get_by_username(self, username: str) -> Optional[dict]:
        return self._run_async(self._get_by_username_async(username))
    
    async def _get_by_username_async(self, username: str):
        collection = self._get_collection()
        admin = await collection.find_one({"username": username})
        return self._normalize_admin(admin) if admin else None
    
    def get_by_email(self, email: str) -> Optional[dict]:
        return self._run_async(self._get_by_email_async(email))
    
    async def _get_by_email_async(self, email: str):
        collection = self._get_collection()
        admin = await collection.find_one({"email": email})
        return self._normalize_admin(admin) if admin else None
    
    def get_by_id(self, admin_id: str) -> Optional[dict]:
        return self._run_async(self._get_by_id_async(admin_id))
    
    async def _get_by_id_async(self, admin_id: str):
        collection = self._get_collection()
        try:
            admin = await collection.find_one({"_id": ObjectId(admin_id)})
        except Exception:
            admin = await collection.find_one({"username": admin_id})
        return self._normalize_admin(admin) if admin else None
    
    def update_last_login(self, username: str):
        return self._run_async(self._update_last_login_async(username))
    
    async def _update_last_login_async(self, username: str):
        collection = self._get_collection()
        await collection.update_one(
            {"username": username},
            {
                "$set": {"last_login": datetime.utcnow(), "updated_at": datetime.utcnow()},
                "$inc": {"login_count": 1}
            }
        )
    
    def update(self, admin_id: str, admin_data: AdminUserUpdate) -> Optional[dict]:
        return self._run_async(self._update_async(admin_id, admin_data))
    
    async def _update_async(self, admin_id: str, admin_data: AdminUserUpdate):
        collection = self._get_collection()
        
        update_dict = {k: v for k, v in admin_data.dict(exclude_unset=True).items()}
        if not update_dict:
            return await self._get_by_id_async(admin_id)
        
        update_dict["updated_at"] = datetime.utcnow()
        
        try:
            result = await collection.find_one_and_update(
                {"_id": ObjectId(admin_id)},
                {"$set": update_dict},
                return_document=ReturnDocument.AFTER
            )
        except Exception:
            result = await collection.find_one_and_update(
                {"username": admin_id},
                {"$set": update_dict},
                return_document=ReturnDocument.AFTER
            )
        
        return self._normalize_admin(result) if result else None
    def delete(self, admin_id: str) -> bool:
        return self._run_async(self._delete_async(admin_id))
    
    async def _delete_async(self, admin_id: str):
        collection = self._get_collection()
        try:
            result = await collection.delete_one({"_id": ObjectId(admin_id)})
        except Exception:
            result = await collection.delete_one({"username": admin_id})
        return result.deleted_count > 0
    
    def list_all(self) -> List[dict]:
        return self._run_async(self._list_all_async())
    
    async def _list_all_async(self):
        collection = self._get_collection()
        cursor = collection.find()
        admins = await cursor.to_list(length=100)
        return [self._normalize_admin(admin) for admin in admins]

admin_crud = AdminUserCRUD() 