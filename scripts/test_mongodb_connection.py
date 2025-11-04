#!/usr/bin/env python3

import os
import sys
import asyncio

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import connect_to_mongo, close_mongo_connection, db
from app.core.db import db as db_operations
from app.crud.country import country_crud

async def test_database_operations():
    """Test that all database operations are using MongoDB"""
    print("🧪 Testing Database Operations...")
    print("=" * 50)
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    if db.adapter is None:
        print("❌ Failed to connect to MongoDB")
        return
    
    # Check if we're using MongoDB or file storage
    adapter_type = type(db.adapter).__name__
    print(f"📊 Database Adapter Type: {adapter_type}")
    
    if adapter_type == "FileStorageAdapter":
        print("⚠️  WARNING: Using File Storage Adapter, not MongoDB!")
        await close_mongo_connection()
        return
    
    print("✅ Using MongoDB DatabaseAdapter\n")
    
    # Test 1: Get all countries through db.get_all_countries()
    print("Test 1: Testing db.get_all_countries()...")
    try:
        countries = db_operations.get_all_countries()
        print(f"   ✅ Retrieved {len(countries)} countries")
        if countries:
            print(f"   Sample: {countries[0].get('name')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Get country by ID through db.get_country_by_id()
    print("\nTest 2: Testing db.get_country_by_id()...")
    try:
        country = db_operations.get_country_by_id("singapore")
        if country:
            print(f"   ✅ Retrieved country: {country.get('name')}")
        else:
            print("   ❌ Country not found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Test country_crud.get_all()
    print("\nTest 3: Testing country_crud.get_all() (used by admin)...")
    try:
        countries = country_crud.get_all()
        print(f"   ✅ Retrieved {len(countries)} countries via CRUD")
        if countries:
            print(f"   Sample: {countries[0].get('name')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Test country_crud.get_by_id()
    print("\nTest 4: Testing country_crud.get_by_id() (used by admin)...")
    try:
        country = country_crud.get_by_id("singapore")
        if country:
            print(f"   ✅ Retrieved country via CRUD: {country.get('name')}")
        else:
            print("   ❌ Country not found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Test search
    print("\nTest 5: Testing search functionality...")
    try:
        results = db_operations.search_countries("singapore")
        print(f"   ✅ Search found {len(results)} results")
        if results:
            print(f"   Sample: {results[0].get('name')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Verify data is coming from MongoDB
    print("\n📊 Database Verification:")
    collection = db.adapter['countries']
    mongo_count = await collection.count_documents({})
    print(f"   MongoDB collection count: {mongo_count}")
    
    # Check if data matches
    db_count = len(db_operations.get_all_countries())
    print(f"   db.get_all_countries() count: {db_count}")
    
    if mongo_count == db_count:
        print("   ✅ Data matches! Website is using MongoDB")
    else:
        print("   ⚠️  Count mismatch - may be using cached or different data")
    
    await close_mongo_connection()
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_database_operations())

