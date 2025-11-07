import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import connect_to_mongo, close_mongo_connection
from app.crud.admin import admin_crud
from app.models.admin import AdminUserCreate
import config

async def create_admin():
    print("👤 Creating admin user in MongoDB...")
    
    await connect_to_mongo()
    
    try:
        username = getattr(config, 'ADMIN_USERNAME', 'admin')
        password = getattr(config, 'ADMIN_PASSWORD', 'admin123')
        
        existing = admin_crud.get_by_username(username)
        if existing:
            print(f"⚠️  Admin user '{username}' already exists!")
            print(f"   Email: {existing.get('email')}")
            print(f"   Full Name: {existing.get('full_name', 'N/A')}")
            print(f"   Super Admin: {existing.get('is_super_admin', False)}")
            print(f"   Active: {existing.get('is_active', False)}")
            print(f"   Last Login: {existing.get('last_login', 'Never')}")
            print(f"   Login Count: {existing.get('login_count', 0)}")
        else:
            admin_data = AdminUserCreate(
                username=username,
                email="admin@beyondborders.com",
                password=password,
                full_name="System Administrator",
                is_super_admin=True
            )
            
            admin = admin_crud.create(admin_data)
            print(f"✅ Admin user created successfully!")
            print(f"   Username: {username}")
            print(f"   Email: {admin['email']}")
            print(f"   Password: {password}")
            print(f"   Super Admin: Yes")
            print(f"\n🔐 Please change the default password after first login!")
    
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(create_admin())

