import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import connect_to_mongo, close_mongo_connection, get_database

async def fix_published_status():
    """Check and fix published status of countries"""
    
    # Connect to database
    await connect_to_mongo()
    db = get_database()
    
    if hasattr(db, 'database'):
        # MongoDB connection
        collection = db.database.countries
        
        # Get all countries
        total = await collection.count_documents({})
        published = await collection.count_documents({"published": True})
        unpublished = await collection.count_documents({"published": False})
        
        print(f"📊 Country Status:")
        print(f"   Total countries: {total}")
        print(f"   Published: {published}")
        print(f"   Unpublished: {unpublished}")
        
        if unpublished > 0:
            print(f"\n📝 Unpublished countries:")
            async for country in collection.find({"published": False}, {"name": 1, "slug": 1, "published": 1}):
                print(f"   - {country.get('name')} ({country.get('slug')}) - published: {country.get('published')}")
            
            # Update all unpublished countries to published
            result = await collection.update_many(
                {"published": False}, 
                {"$set": {"published": True}}
            )
            
            print(f"\n✅ Updated {result.modified_count} countries to published=True")
        
        # Check final status
        final_published = await collection.count_documents({"published": True})
        print(f"\n🎉 Final result: {final_published} published countries")
        
    else:
        # File storage
        print("🗂️  Using file storage")
        current_data = db.load_collection('countries')
        
        unpublished_count = 0
        for country in current_data:
            if not country.get('published', True):
                print(f"   - {country.get('name')} ({country.get('slug')}) - published: {country.get('published')}")
                country['published'] = True
                unpublished_count += 1
        
        if unpublished_count > 0:
            db.save_collection('countries', current_data)
            print(f"✅ Updated {unpublished_count} countries to published=True in file storage")
        
        print(f"🎉 Total countries in file storage: {len(current_data)}")
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(fix_published_status()) 