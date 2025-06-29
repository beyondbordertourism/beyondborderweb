from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models.country import Country
from app.crud.country import country_crud
from app.core.database import get_database

router = APIRouter()

@router.get("/", response_model=List[Country])
async def get_countries(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    region: Optional[str] = None,
    visa_required: Optional[bool] = None
):
    """Get all published countries with optional filtering"""
    return await country_crud.get_all(
        skip=skip, 
        limit=limit, 
        published_only=True,
        region=region,
        visa_required=visa_required
    )

@router.get("/featured", response_model=List[Country])
async def get_featured_countries(limit: int = Query(6, ge=1, le=20)):
    """Get featured countries for homepage"""
    return await country_crud.get_featured(limit=limit)

@router.get("/regions")
async def get_regions():
    """Get all available regions"""
    regions = await country_crud.get_regions()
    return {"regions": regions}

@router.get("/search", response_model=List[Country])
async def search_countries(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50)
):
    """Search countries by name or content"""
    return await country_crud.search(query=q, limit=limit)

@router.get("/stats")
async def get_stats():
    """Get public statistics about countries"""
    stats = await country_crud.get_stats()
    
    # Debug information
    db = get_database()
    debug_info = {
        "database_type": "MongoDB" if hasattr(db, 'database') else "File Storage",
        "raw_stats": stats
    }
    
    # Return only public stats with debug info
    return {
        "total_countries": stats["published_countries"],
        "regions": len(stats["region_distribution"]),
        "visa_required": stats["visa_required"],
        "visa_free": stats["visa_free"],
        "debug": debug_info
    }

@router.get("/fix-missing")
async def fix_missing_countries():
    """Fix missing countries by adding them directly to file storage"""
    try:
        from app.core.database import FileStorageAdapter
        from datetime import datetime
        
        # Force file storage
        file_db = FileStorageAdapter()
        
        # Load current data
        current_data = file_db.load_collection('countries')
        current_slugs = {country.get('slug') for country in current_data}
        
        # Define the 5 missing countries with minimal data
        missing_countries = [
            {
                "slug": "china",
                "name": "China", 
                "flag": "🇨🇳",
                "region": "East Asia",
                "visa_required": True,
                "published": True,
                "featured": False,
                "last_updated": datetime.now().isoformat(),
                "summary": "All Indian passport holders require a visa to enter China.",
                "visa_types": [{"name": "Tourist Visa", "purpose": "Tourism", "entry_type": "Single", "validity": "30 days", "stay_duration": "30 days", "extendable": False, "fees": [], "conditions": [], "notes": ""}],
                "documents": [{"name": "Passport", "required": True, "category": "mandatory", "details": "Valid passport"}],
                "photo_requirements": {"size": "35mm x 45mm", "background": "white", "specifications": ["Recent photo"]},
                "processing_times": [{"type": "regular", "duration": "3-5 days", "notes": ""}],
                "fees": [{"type": "Visa Fee", "amount_inr": 2900, "notes": ""}],
                "application_methods": [{"name": "embassy", "description": "Apply through embassy", "requirements": [], "available": True}],
                "embassies": [],
                "important_notes": []
            },
            {
                "slug": "philippines",
                "name": "Philippines",
                "flag": "🇵🇭", 
                "region": "Southeast Asia",
                "visa_required": True,
                "published": True,
                "featured": False,
                "last_updated": datetime.now().isoformat(),
                "summary": "Indian citizens need a visa to enter the Philippines.",
                "visa_types": [{"name": "Tourist Visa", "purpose": "Tourism", "entry_type": "Single", "validity": "30 days", "stay_duration": "30 days", "extendable": False, "fees": [], "conditions": [], "notes": ""}],
                "documents": [{"name": "Passport", "required": True, "category": "mandatory", "details": "Valid passport"}],
                "photo_requirements": {"size": "35mm x 45mm", "background": "white", "specifications": ["Recent photo"]},
                "processing_times": [{"type": "regular", "duration": "3-5 days", "notes": ""}],
                "fees": [{"type": "Visa Fee", "amount_inr": 2500, "notes": ""}],
                "application_methods": [{"name": "embassy", "description": "Apply through embassy", "requirements": [], "available": True}],
                "embassies": [],
                "important_notes": []
            },
            {
                "slug": "cambodia",
                "name": "Cambodia",
                "flag": "🇰🇭",
                "region": "Southeast Asia", 
                "visa_required": True,
                "published": True,
                "featured": False,
                "last_updated": datetime.now().isoformat(),
                "summary": "Indian passport holders can get a visa on arrival or apply for an e-visa to enter Cambodia.",
                "visa_types": [{"name": "Tourist Visa", "purpose": "Tourism", "entry_type": "Single", "validity": "30 days", "stay_duration": "30 days", "extendable": False, "fees": [], "conditions": [], "notes": ""}],
                "documents": [{"name": "Passport", "required": True, "category": "mandatory", "details": "Valid passport"}],
                "photo_requirements": {"size": "35mm x 45mm", "background": "white", "specifications": ["Recent photo"]},
                "processing_times": [{"type": "regular", "duration": "3-5 days", "notes": ""}],
                "fees": [{"type": "Visa Fee", "amount_inr": 2000, "notes": ""}],
                "application_methods": [{"name": "embassy", "description": "Apply through embassy", "requirements": [], "available": True}],
                "embassies": [],
                "important_notes": []
            },
            {
                "slug": "indonesia",
                "name": "Indonesia",
                "flag": "🇮🇩",
                "region": "Southeast Asia",
                "visa_required": False,
                "published": True,
                "featured": False,
                "last_updated": datetime.now().isoformat(),
                "summary": "Indian citizens can enter Indonesia visa-free for 30 days for tourism purposes.",
                "visa_types": [{"name": "Visa Free", "purpose": "Tourism", "entry_type": "Single", "validity": "30 days", "stay_duration": "30 days", "extendable": False, "fees": [], "conditions": [], "notes": ""}],
                "documents": [{"name": "Passport", "required": True, "category": "mandatory", "details": "Valid passport"}],
                "photo_requirements": {"size": "35mm x 45mm", "background": "white", "specifications": ["Recent photo"]},
                "processing_times": [{"type": "visa_free", "duration": "At arrival", "notes": ""}],
                "fees": [],
                "application_methods": [{"name": "arrival", "description": "Visa free entry", "requirements": [], "available": True}],
                "embassies": [],
                "important_notes": []
            },
            {
                "slug": "vietnam",
                "name": "Vietnam",
                "flag": "🇻🇳",
                "region": "Southeast Asia",
                "visa_required": True,
                "published": True,
                "featured": False,
                "last_updated": datetime.now().isoformat(),
                "summary": "Indian passport holders require a visa to enter Vietnam. E-visa and visa on arrival options are available.",
                "visa_types": [{"name": "Tourist Visa", "purpose": "Tourism", "entry_type": "Single", "validity": "30 days", "stay_duration": "30 days", "extendable": False, "fees": [], "conditions": [], "notes": ""}],
                "documents": [{"name": "Passport", "required": True, "category": "mandatory", "details": "Valid passport"}],
                "photo_requirements": {"size": "35mm x 45mm", "background": "white", "specifications": ["Recent photo"]},
                "processing_times": [{"type": "regular", "duration": "3-5 days", "notes": ""}],
                "fees": [{"type": "Visa Fee", "amount_inr": 2000, "notes": ""}],
                "application_methods": [{"name": "embassy", "description": "Apply through embassy", "requirements": [], "available": True}],
                "embassies": [],
                "important_notes": []
            }
        ]
        
        added_count = 0
        for country in missing_countries:
            if country["slug"] not in current_slugs:
                current_data.append(country)
                added_count += 1
        
        # Save the updated data
        if added_count > 0:
            file_db.save_collection('countries', current_data)
        
        return {
            "status": "success",
            "message": f"Added {added_count} missing countries",
            "total_countries": len(current_data),
            "added_countries": [c["name"] for c in missing_countries if c["slug"] not in current_slugs]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/{slug}", response_model=Country)
async def get_country_by_slug(slug: str):
    """Get a specific country by slug"""
    country = await country_crud.get_by_slug(slug)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    if not country.published:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return country 