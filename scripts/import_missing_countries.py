import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.models.country import CountryCreate, VisaType, Document, PhotoRequirement, ProcessingTime, Fee, Embassy, ImportantNote, ApplicationMethod

def get_flag_emoji(country_name):
    """Get flag emoji for country"""
    flags = {
        "china": "🇨🇳",
        "philippines": "🇵🇭", 
        "cambodia": "🇰🇭",
        "indonesia": "🇮🇩",
        "vietnam": "🇻🇳"
    }
    return flags.get(country_name.lower(), "🏳️")

def convert_json_to_country(json_data, country_slug):
    """Convert JSON country data to CountryCreate model"""
    
    country_name = json_data.get("country", country_slug.title())
    
    # Convert visa types
    visa_types = []
    for vt in json_data.get("visa_types", []):
        visa_type = VisaType(
            name=vt.get("name", ""),
            purpose=vt.get("purpose", ""),
            entry_type="Single",  # Default
            validity=vt.get("validity", ""),
            stay_duration=str(vt.get("max_stay_days", "")),
            extendable=False,
            fees=[],
            conditions=[],
            notes=""
        )
        visa_types.append(visa_type)
    
    # Convert fees
    fees = []
    fee_data = json_data.get("visa_fees", {}).get("fees_in_inr", {})
    for fee_type, amount in fee_data.items():
        if isinstance(amount, (int, float)):
            fee = Fee(
                type=fee_type,
                amount_inr=float(amount),
                notes=""
            )
            fees.append(fee)
    
    # Convert documents
    documents = []
    doc_list = json_data.get("application_process", {}).get("documents_required", [])
    for doc in doc_list:
        if isinstance(doc, str):
            document = Document(
                name=doc,
                required=True,
                category="mandatory",
                details=""
            )
            documents.append(document)
    
    # Convert embassies/centers
    embassies = []
    centers = json_data.get("application_process", {}).get("centers", [])
    for center in centers:
        if isinstance(center, dict):
            embassy = Embassy(
                city=center.get("city", ""),
                address=center.get("address", ""),
                phone=center.get("phone", ""),
                email=center.get("email", "")
            )
            embassies.append(embassy)
    
    # Convert processing times
    processing_times = []
    proc_data = json_data.get("processing_time", {})
    if "regular" in proc_data:
        processing_times.append(ProcessingTime(
            type="regular",
            duration=proc_data["regular"],
            notes=""
        ))
    if "express" in proc_data:
        processing_times.append(ProcessingTime(
            type="express", 
            duration=proc_data["express"],
            notes=f"Additional fee: ₹{proc_data.get('express_additional_fee_inr', 0)}"
        ))
    
    # Convert important notes
    important_notes = []
    notes_list = json_data.get("important_notes", [])
    for note in notes_list:
        if isinstance(note, str):
            important_note = ImportantNote(
                type="tip",
                content=note,
                priority="medium"
            )
            important_notes.append(important_note)
    
    # Create country
    country = CountryCreate(
        slug=country_slug,
        name=country_name,
        flag=get_flag_emoji(country_name),
        region="Asia",  # Default for our countries
        visa_required=json_data.get("visa_required", True),
        last_updated=datetime.now().isoformat(),
        summary=json_data.get("entry_requirements", {}).get("visa_required_note", f"Visa required for {country_name}"),
        visa_types=visa_types,
        documents=documents,
        photo_requirements=PhotoRequirement(
            size="35mm x 45mm",
            background="white",
            specifications=["Recent photo", "Clear face visibility"]
        ),
        processing_times=processing_times,
        fees=fees,
        application_methods=[
            ApplicationMethod(
                name="embassy",
                description="Apply through embassy or visa center",
                requirements=[],
                available=True
            )
        ],
        embassies=embassies,
        important_notes=important_notes,
        published=True,
        featured=False
    )
    
    return country

async def import_missing_countries():
    """Import missing countries from JSON files"""
    
    # Connect to database
    await connect_to_mongo()
    db = get_database()
    
    # Check current countries
    if hasattr(db, 'database'):
        collection = db.database.countries
        existing_count = await collection.count_documents({})
        print(f"Current countries in database: {existing_count}")
        
        # Get existing slugs
        existing_slugs = set()
        async for country in collection.find({}, {"slug": 1}):
            existing_slugs.add(country["slug"])
        print(f"Existing slugs: {existing_slugs}")
    else:
        print("Using file storage")
        existing_slugs = set()
    
    # Countries to import
    missing_countries = ["china", "philippines", "cambodia", "indonesia", "vietnam"]
    
    imported_count = 0
    for country_slug in missing_countries:
        if country_slug in existing_slugs:
            print(f"✅ {country_slug} already exists, skipping")
            continue
            
        json_file = Path(__file__).parent.parent / "data" / "JSON" / f"{country_slug}.json"
        
        if not json_file.exists():
            print(f"⚠️  JSON file not found for {country_slug}")
            continue
        
        try:
            # Load JSON data
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Convert to country model
            country = convert_json_to_country(json_data, country_slug)
            
            # Insert into database
            if hasattr(db, 'database'):
                # MongoDB
                result = await collection.insert_one(country.model_dump())
                print(f"✅ Imported {country.name} (ID: {result.inserted_id})")
            else:
                # File storage
                from app.crud.country import country_crud
                result = await country_crud.create(country)
                print(f"✅ Imported {country.name} to file storage")
            
            imported_count += 1
            
        except Exception as e:
            print(f"❌ Error importing {country_slug}: {e}")
    
    print(f"\n🎉 Successfully imported {imported_count} countries!")
    
    # Check final count
    if hasattr(db, 'database'):
        final_count = await collection.count_documents({})
        print(f"Total countries now: {final_count}")
    
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(import_missing_countries()) 