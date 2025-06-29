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
    def __init__(self):
        self.collection_name = "admin_users"

    def get_collection(self):
        db = get_database()
        if db is None:
            logger.warning("Database not available")
            return None
        return db[self.collection_name]

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def create(self, admin_data: AdminUserCreate) -> AdminUser:
        collection = self.get_collection()
        if collection is None:
            raise Exception("Database not available")
        
        # Check if username or email already exists
        existing_user = await collection.find_one({
            "$or": [
                {"username": admin_data.username},
                {"email": admin_data.email}
            ]
        })
        
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Hash password and create user
        admin_dict = admin_data.model_dump(exclude={"password"})
        admin_dict["password_hash"] = self.hash_password(admin_data.password)
        admin_dict["created_at"] = datetime.utcnow()
        admin_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(admin_dict)
        
        # Fetch the created document
        created_admin = await collection.find_one({"_id": result.inserted_id})
        return AdminUser(**created_admin)

    async def get_by_id(self, admin_id: str) -> Optional[AdminUser]:
        collection = self.get_collection()
        if collection is None:
            return None
            
        if not ObjectId.is_valid(admin_id):
            return None
            
        admin = await collection.find_one({"_id": ObjectId(admin_id)})
        return AdminUser(**admin) if admin else None

    async def get_by_username(self, username: str) -> Optional[AdminUser]:
        collection = self.get_collection()
        if collection is None:
            return None
        admin = await collection.find_one({"username": username})
        return AdminUser(**admin) if admin else None

    async def get_by_email(self, email: str) -> Optional[AdminUser]:
        collection = self.get_collection()
        if collection is None:
            return None
        admin = await collection.find_one({"email": email})
        return AdminUser(**admin) if admin else None

    async def authenticate(self, username: str, password: str) -> Optional[AdminUser]:
        admin = await self.get_by_username(username)
        if not admin:
            return None
        
        if not admin.is_active:
            return None
            
        if not self.verify_password(password, admin.password_hash):
            return None
        
        # Update login info
        await self.update_login_info(str(admin.id))
        return admin

    async def update_login_info(self, admin_id: str) -> bool:
        collection = self.get_collection()
        if collection is None:
            return False
        
        if not ObjectId.is_valid(admin_id):
            return False
        
        result = await collection.update_one(
            {"_id": ObjectId(admin_id)},
            {
                "$set": {"last_login": datetime.utcnow()},
                "$inc": {"login_count": 1}
            }
        )
        
        return result.modified_count > 0

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[AdminUserResponse]:
        collection = self.get_collection()
        if collection is None:
            return []
        
        cursor = collection.find({}, {"password_hash": 0}).skip(skip).limit(limit).sort("created_at", -1)
        admins = await cursor.to_list(length=limit)
        
        return [AdminUserResponse(**{**admin, "id": str(admin["_id"])}) for admin in admins]

    async def update(self, admin_id: str, admin_data: AdminUserUpdate) -> Optional[AdminUser]:
        collection = self.get_collection()
        if collection is None:
            return None
        
        if not ObjectId.is_valid(admin_id):
            return None
        
        # Prepare update data
        update_dict = {k: v for k, v in admin_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        updated_admin = await collection.find_one_and_update(
            {"_id": ObjectId(admin_id)},
            {"$set": update_dict},
            return_document=ReturnDocument.AFTER
        )
        
        return AdminUser(**updated_admin) if updated_admin else None

    async def update_password(self, admin_id: str, new_password: str) -> bool:
        collection = self.get_collection()
        if collection is None:
            return False
        
        if not ObjectId.is_valid(admin_id):
            return False
        
        hashed_password = self.hash_password(new_password)
        
        result = await collection.update_one(
            {"_id": ObjectId(admin_id)},
            {
                "$set": {
                    "password_hash": hashed_password,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0

    async def delete(self, admin_id: str) -> bool:
        collection = self.get_collection()
        if collection is None:
            return False
        
        if not ObjectId.is_valid(admin_id):
            return False
        
        result = await collection.delete_one({"_id": ObjectId(admin_id)})
        return result.deleted_count > 0

    async def count(self) -> int:
        collection = self.get_collection()
        if collection is None:
            return 0
        return await collection.count_documents({})

    async def create_default_admin(self) -> Optional[AdminUser]:
        """Create default admin user if none exists"""
        collection = self.get_collection()
        if collection is None:
            return None
        
        # Check if any admin exists
        admin_count = await collection.count_documents({})
        if admin_count > 0:
            return None
        
        # Create default admin
        default_admin = AdminUserCreate(
            username="admin",
            email="admin@visaguide.com",
            full_name="System Administrator",
            password="admin123",
            is_super_admin=True
        )
        
        try:
            return await self.create(default_admin)
        except Exception as e:
            logger.error(f"Error creating default admin: {e}")
            return None

# Create instance
admin_crud = AdminUserCRUD() 