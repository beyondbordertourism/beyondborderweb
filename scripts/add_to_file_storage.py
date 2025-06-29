import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import connect_to_mongo, get_database
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

async def add_missing_to_file_storage():
    """Add missing countries directly to file storage"""
    
    # Initialize database (will use file storage if MongoDB fails)
    await connect_to_mongo()
    db = get_database()
    
    # Force file storage mode to work directly with files
    from app.core.database import FileStorageAdapter
    file_db = FileStorageAdapter()
    
    # Load current file storage data
    current_data = file_db.load_collection('countries')
    current_slugs = {country.get('slug') for country in current_data}
    
    print(f"Current countries in file storage: {len(current_data)}")
    print(f"Existing slugs: {current_slugs}")
    
    # Countries to add
    missing_countries = ["china", "philippines", "cambodia", "indonesia", "vietnam"]
    
    added_count = 0
    for country_slug in missing_countries:
        if country_slug in current_slugs:
            print(f"✅ {country_slug} already exists in file storage, skipping")
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
            
            # Add to file storage
            country_dict = country.model_dump()
            current_data.append(country_dict)
            
            print(f"✅ Added {country.name} to file storage")
            added_count += 1
            
        except Exception as e:
            print(f"❌ Error adding {country_slug}: {e}")
    
    # Save updated data back to file storage
    if added_count > 0:
        file_db.save_collection('countries', current_data)
        print(f"\n💾 Saved {len(current_data)} countries to file storage")
    
    print(f"\n🎉 Successfully added {added_count} countries to file storage!")
    print(f"Total countries now: {len(current_data)}")

if __name__ == "__main__":
    asyncio.run(add_missing_to_file_storage()) 