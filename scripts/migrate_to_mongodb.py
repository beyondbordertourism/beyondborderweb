#!/usr/bin/env python3

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import connect_to_mongo, close_mongo_connection, db

async def migrate_from_storage_file():
    """Migrate data from data_storage/countries.json to MongoDB"""
    storage_file = Path(__file__).parent.parent / "data_storage" / "countries.json"
    
    if not storage_file.exists():
        print(f"❌ Storage file not found: {storage_file}")
        return False
    
    print(f"📂 Loading data from {storage_file}...")
    
    with open(storage_file, 'r', encoding='utf-8') as f:
        countries_data = json.load(f)
    
    if not isinstance(countries_data, list):
        print("❌ Expected list of countries in JSON file")
        return False
    
    print(f"✅ Loaded {len(countries_data)} countries from storage file")
    
    if db.adapter is None:
        print("❌ Database not connected")
        return False
    
    collection = db.adapter['countries']
    
    # Check if collection has data
    existing_count = await collection.count_documents({})
    if existing_count > 0:
        print(f"⚠️  Collection already has {existing_count} documents")
        print("🗑️  Deleting existing data to re-import...")
        result = await collection.delete_many({})
        print(f"🗑️  Deleted {result.deleted_count} existing documents")
    
    imported = 0
    skipped = 0
    
    for country in countries_data:
        try:
            # Ensure we have an 'id' field (use slug if no id)
            if 'id' not in country and 'slug' in country:
                country['id'] = country['slug']
            
            # Check if country already exists
            existing = await collection.find_one({"id": country.get('id')})
            if existing:
                print(f"⏭️  Skipping {country.get('name')} - already exists")
                skipped += 1
                continue
            
            # Ensure all required fields exist with defaults
            country.setdefault('published', True)
            country.setdefault('featured', False)
            country.setdefault('visa_types', [])
            country.setdefault('documents', [])
            country.setdefault('processing_times', [])
            country.setdefault('application_methods', [])
            country.setdefault('embassies', [])
            country.setdefault('important_notes', [])
            country.setdefault('photo_requirements', {})
            
            # Insert country
            result = await collection.insert_one(country)
            print(f"✅ Imported {country.get('name')} (ID: {country.get('id')})")
            imported += 1
            
        except Exception as e:
            print(f"❌ Error importing {country.get('name', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Migration completed!")
    print(f"   • Imported: {imported} countries")
    print(f"   • Skipped: {skipped} countries")
    
    # Display summary
    total_count = await collection.count_documents({})
    published_count = await collection.count_documents({"published": True})
    featured_count = await collection.count_documents({"featured": True})
    
    print(f"\n📊 MongoDB Summary:")
    print(f"   • Total countries: {total_count}")
    print(f"   • Published: {published_count}")
    print(f"   • Featured: {featured_count}")
    
    return True

async def migrate_from_json_files():
    """Migrate data from individual JSON files in data/JSON/ to MongoDB"""
    json_dir = Path(__file__).parent.parent / "data" / "JSON"
    
    if not json_dir.exists():
        print(f"❌ JSON directory not found: {json_dir}")
        return False
    
    json_files = list(json_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ No JSON files found in {json_dir}")
        return False
    
    print(f"📂 Found {len(json_files)} JSON files to process...")
    
    if db.adapter is None:
        print("❌ Database not connected")
        return False
    
    collection = db.adapter['countries']
    
    imported = 0
    errors = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Extract country name and create slug
            country_name = json_data.get('country', json_file.stem.replace('-', ' ').title())
            slug = json_file.stem.lower().replace(' ', '-')
            
            # Check if already exists
            existing = await collection.find_one({"id": slug})
            if existing:
                print(f"⏭️  Skipping {country_name} - already exists")
                continue
            
            # Convert to MongoDB format
            country_doc = {
                "id": slug,
                "name": country_name,
                "flag": json_data.get('flag', ''),
                "region": json_data.get('region', 'Asia'),
                "visa_required": json_data.get('visa_required', True),
                "last_updated": datetime.utcnow().isoformat(),
                "summary": json_data.get('entry_requirements', {}).get('visa_required_note', ''),
                "published": True,
                "featured": False,
                "visa_types": json_data.get('visa_types', []),
                "documents": json_data.get('documents_required', {}).get('common', []),
                "processing_times": [],
                "application_methods": [],
                "embassies": [],
                "important_notes": [],
                "photo_requirements": {}
            }
            
            # Insert country
            await collection.insert_one(country_doc)
            print(f"✅ Imported {country_name} (ID: {slug})")
            imported += 1
            
        except Exception as e:
            print(f"❌ Error importing {json_file.name}: {e}")
            errors += 1
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Migration completed!")
    print(f"   • Imported: {imported} countries")
    print(f"   • Errors: {errors} countries")
    
    return True

async def main():
    """Main migration function"""
    print("🚀 Starting MongoDB Migration...")
    print("=" * 50)
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    if db.adapter is None:
        print("❌ Failed to connect to MongoDB")
        return
    
    print("✅ Connected to MongoDB\n")
    
    # Try to migrate from storage file first (preferred)
    storage_file = Path(__file__).parent.parent / "data_storage" / "countries.json"
    if storage_file.exists():
        print("📦 Found data_storage/countries.json - using this as source")
        success = await migrate_from_storage_file()
        if success:
            await close_mongo_connection()
            return
    
    # Fallback to individual JSON files
    print("\n📂 Migrating from individual JSON files...")
    await migrate_from_json_files()
    
    await close_mongo_connection()
    print("\n✅ Migration process completed!")

if __name__ == "__main__":
    asyncio.run(main())

