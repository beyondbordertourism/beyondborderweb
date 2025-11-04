import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import connect_to_mongo, close_mongo_connection, db as core_db_instance

HERO_IMAGES = {
    "singapore": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&w=1350&q=80",
    "japan": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1350&q=80",
    "thailand": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1350&q=80",
    "maldives": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?auto=format&fit=crop&w=1350&q=80",
    "china": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?auto=format&fit=crop&w=1350&q=80",
    "south-korea": "https://images.unsplash.com/photo-1517154421773-0529f29ea451?auto=format&fit=crop&w=1350&q=80",
    "vietnam": "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1350&q=80",
    "malaysia": "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?auto=format&fit=crop&w=1350&q=80",
    "indonesia": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1350&q=80",
    "philippines": "https://images.unsplash.com/photo-1518509562904-e7ef99cdcc86?auto=format&fit=crop&w=1350&q=80",
    "cambodia": "https://images.unsplash.com/photo-1563911302283-d2bc129e7570?auto=format&fit=crop&w=1350&q=80",
    "united-arab-emirates": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1350&q=80",
    "mauritius": "https://images.unsplash.com/photo-1538708591342-2dcd6706e028?auto=format&fit=crop&w=1350&q=80",
}

async def add_hero_images():
    print("🖼️  Adding hero images to countries...")
    
    await connect_to_mongo()
    
    if core_db_instance.adapter is None:
        print("❌ Database not connected.")
        return
    
    collection = core_db_instance.adapter['countries']
    
    updated_count = 0
    not_found = []
    
    for country_id, hero_url in HERO_IMAGES.items():
        result = await collection.update_one(
            {"id": country_id},
            {"$set": {"hero_image_url": hero_url}}
        )
        
        if result.matched_count > 0:
            print(f"✅ Updated {country_id}")
            updated_count += 1
        else:
            print(f"⚠️  Country not found: {country_id}")
            not_found.append(country_id)
    
    print(f"\n✨ Updated {updated_count} countries")
    if not_found:
        print(f"⚠️  Not found: {', '.join(not_found)}")
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(add_hero_images())

