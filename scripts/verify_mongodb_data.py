#!/usr/bin/env python3

import os
import sys
import asyncio

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import connect_to_mongo, close_mongo_connection, db

async def verify_data():
    """Verify data in MongoDB"""
    print("🔍 Verifying MongoDB data...")
    print("=" * 50)
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    if db.adapter is None:
        print("❌ Failed to connect to MongoDB")
        return
    
    print("✅ Connected to MongoDB\n")
    
    collection = db.adapter['countries']
    
    # Count documents
    total_count = await collection.count_documents({})
    print(f"📊 Total countries in MongoDB: {total_count}")
    
    if total_count == 0:
        print("\n⚠️  No data found in MongoDB!")
        print("   Please run the migration script: python scripts/migrate_to_mongodb.py")
        await close_mongo_connection()
        return
    
    # Get published count
    published_count = await collection.count_documents({"published": True})
    print(f"📊 Published countries: {published_count}")
    
    # Get featured count
    featured_count = await collection.count_documents({"featured": True})
    print(f"📊 Featured countries: {featured_count}")
    
    # List all countries
    print("\n📋 Countries in database:")
    cursor = collection.find({}, {"name": 1, "id": 1, "published": 1, "region": 1})
    countries = await cursor.to_list(length=100)
    
    for i, country in enumerate(countries, 1):
        status = "✅ Published" if country.get('published') else "📝 Draft"
        print(f"   {i}. {country.get('name')} ({country.get('id')}) - {status}")
    
    # Show sample country
    if countries:
        print("\n📄 Sample country data (first country):")
        sample = countries[0]
        sample_full = await collection.find_one({"id": sample.get('id')})
        print(f"   Name: {sample_full.get('name')}")
        print(f"   Region: {sample_full.get('region')}")
        print(f"   Visa Required: {sample_full.get('visa_required')}")
        print(f"   Visa Types: {len(sample_full.get('visa_types', []))}")
        print(f"   Documents: {len(sample_full.get('documents', []))}")
    
    await close_mongo_connection()
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    asyncio.run(verify_data())

