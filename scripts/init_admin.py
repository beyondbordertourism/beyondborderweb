#!/usr/bin/env python3
"""
Script to initialize admin users in MongoDB
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import connect_to_mongo, close_mongo_connection
from app.crud.admin import admin_crud
from app.models.admin import AdminUserCreate

async def create_default_admin():
    """Create default admin user if none exists"""
    print("🔧 Initializing Admin Users...")
    
    try:
        # Connect to database
        await connect_to_mongo()
        
        # Check if any admin users exist
        admin_count = await admin_crud.count()
        print(f"📊 Current admin count: {admin_count}")
        
        if admin_count == 0:
            # Create default admin
            print("👤 Creating default admin user...")
            
            default_admin = AdminUserCreate(
                username="admin",
                email="admin@visaguide.com",
                full_name="System Administrator",
                password="admin123",
                is_super_admin=True
            )
            
            created_admin = await admin_crud.create(default_admin)
            print(f"✅ Created admin user: {created_admin.username} ({created_admin.email})")
            
        else:
            print("ℹ️  Admin users already exist. Listing current users:")
            admins = await admin_crud.get_all(limit=10)
            for admin in admins:
                status = "🟢 Active" if admin.is_active else "🔴 Inactive"
                super_admin = "👑 Super Admin" if admin.is_super_admin else "👤 Admin"
                print(f"   • {admin.username} ({admin.email}) - {status} - {super_admin}")
        
        print("\n🎉 Admin initialization completed!")
        
        # Display login info
        print("\n📋 Login Information:")
        print("   • URL: http://localhost:8000/admin/login")
        print("   • Username: admin")
        print("   • Password: admin123")
        
    except Exception as e:
        print(f"❌ Error initializing admin users: {e}")
        return False
    
    finally:
        await close_mongo_connection()
    
    return True

async def list_admins():
    """List all admin users"""
    print("\n👥 Current Admin Users")
    print("=" * 40)
    
    try:
        await connect_to_mongo()
        
        admins = await admin_crud.get_all(limit=50)
        
        if not admins:
            print("No admin users found.")
            return
        
        for i, admin in enumerate(admins, 1):
            status = "🟢 Active" if admin.is_active else "🔴 Inactive"
            super_admin = "👑 Super Admin" if admin.is_super_admin else "👤 Admin"
            last_login = admin.last_login.strftime("%Y-%m-%d %H:%M") if admin.last_login else "Never"
            
            print(f"{i:2d}. {admin.username}")
            print(f"    Email: {admin.email}")
            print(f"    Name: {admin.full_name}")
            print(f"    Status: {status}")
            print(f"    Role: {super_admin}")
            print(f"    Last Login: {last_login}")
            print(f"    Login Count: {admin.login_count}")
            print(f"    Created: {admin.created_at.strftime('%Y-%m-%d %H:%M')}")
            print()
    
    except Exception as e:
        print(f"❌ Error listing admin users: {e}")
    
    finally:
        await close_mongo_connection()

def main():
    """Main function"""
    print("🚀 Admin User Management")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "init":
            asyncio.run(create_default_admin())
        elif command == "list":
            asyncio.run(list_admins())
        else:
            print(f"❌ Unknown command: {command}")
            show_help()
    else:
        # Default action: initialize
        asyncio.run(create_default_admin())

def show_help():
    """Show help information"""
    print("\nUsage:")
    print("  python scripts/init_admin.py [command]")
    print("\nCommands:")
    print("  init    Initialize default admin user (default)")
    print("  list    List all admin users")
    print("\nExamples:")
    print("  python scripts/init_admin.py")
    print("  python scripts/init_admin.py init")
    print("  python scripts/init_admin.py list")

if __name__ == "__main__":
    main() 
 