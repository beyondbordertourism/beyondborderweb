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
    # Return only public stats
    return {
        "total_countries": stats["published_countries"],
        "regions": len(stats["region_distribution"]),
        "visa_required": stats["visa_required"],
        "visa_free": stats["visa_free"]
    }

@router.get("/import-missing")
async def import_missing_countries():
    """Import missing countries endpoint"""
    try:
        from app.crud.country import country_crud
        from app.models.country import CountryCreate, VisaType, Document, PhotoRequirement, ProcessingTime, Fee, Embassy, ImportantNote, ApplicationMethod
        import json
        from pathlib import Path
        from datetime import datetime
        
        # Define missing countries and their data
        missing_data = {
            "china": {
                "name": "China",
                "flag": "🇨🇳",
                "summary": "All Indian passport holders require a visa to enter China. The type of visa depends on the purpose of visit.",
                "region": "East Asia"
            },
            "philippines": {
                "name": "Philippines", 
                "flag": "🇵🇭",
                "summary": "Indian citizens need a visa to enter the Philippines for tourism, business, or other purposes.",
                "region": "Southeast Asia"
            },
            "cambodia": {
                "name": "Cambodia",
                "flag": "🇰🇭", 
                "summary": "Indian passport holders can get a visa on arrival or apply for an e-visa to enter Cambodia.",
                "region": "Southeast Asia"
            },
            "indonesia": {
                "name": "Indonesia",
                "flag": "🇮🇩",
                "summary": "Indian citizens can enter Indonesia visa-free for 30 days for tourism purposes.",
                "region": "Southeast Asia"
            },
            "vietnam": {
                "name": "Vietnam",
                "flag": "🇻🇳",
                "summary": "Indian passport holders require a visa to enter Vietnam. E-visa and visa on arrival options are available.",
                "region": "Southeast Asia"
            }
        }
        
        added_count = 0
        for slug, info in missing_data.items():
            # Check if country already exists
            existing = await country_crud.get_by_slug(slug)
            if existing:
                continue
                
            # Create minimal country data
            country = CountryCreate(
                slug=slug,
                name=info["name"],
                flag=info["flag"],
                region=info["region"],
                visa_required=True,
                last_updated=datetime.now().isoformat(),
                summary=info["summary"],
                visa_types=[
                    VisaType(
                        name="Tourist Visa",
                        purpose="Tourism",
                        entry_type="Single",
                        validity="30 days",
                        stay_duration="30 days",
                        extendable=False,
                        fees=[],
                        conditions=[],
                        notes=""
                    )
                ],
                documents=[
                    Document(
                        name="Passport",
                        required=True,
                        category="mandatory",
                        details="Valid passport with at least 6 months validity"
                    )
                ],
                photo_requirements=PhotoRequirement(
                    size="35mm x 45mm",
                    background="white",
                    specifications=["Recent photo", "Clear face visibility"]
                ),
                processing_times=[
                    ProcessingTime(
                        type="regular",
                        duration="3-5 working days",
                        notes=""
                    )
                ],
                fees=[
                    Fee(
                        type="Visa Fee",
                        amount_inr=2000,
                        notes="Approximate fee"
                    )
                ],
                application_methods=[
                    ApplicationMethod(
                        name="embassy",
                        description="Apply through embassy or visa center",
                        requirements=[],
                        available=True
                    )
                ],
                embassies=[],
                important_notes=[],
                published=True,
                featured=False
            )
            
            # Create the country
            result = await country_crud.create(country)
            if result:
                added_count += 1
        
        # Get current stats
        stats = await country_crud.get_stats()
        
        return {
            "status": "success",
            "added_countries": added_count,
            "current_total": stats.get("total_countries", 0),
            "published_countries": stats.get("published_countries", 0)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/debug-db")
async def debug_database_connection():
    """Debug endpoint to check database connection and data"""
    try:
        db = get_database()
        
        # Check if MongoDB or file storage
        if hasattr(db, 'database'):
            # MongoDB connection
            collection = db.database.countries
            total = await collection.count_documents({})
            
            # Get first few countries
            countries = []
            async for country in collection.find({}, {"name": 1, "slug": 1, "_id": 0}).limit(5):
                countries.append({"name": country.get("name"), "slug": country.get("slug")})
            
            return {
                "status": "MongoDB connected",
                "total_countries": total,
                "sample_countries": countries,
                "database_type": "MongoDB Atlas"
            }
        else:
            # File storage
            data = db.load_collection('countries')
            sample_countries = [{"name": c.get("name"), "slug": c.get("slug")} for c in data[:5]]
            
            return {
                "status": "File storage active", 
                "total_countries": len(data),
                "sample_countries": sample_countries,
                "database_type": "File Storage"
            }
            
    except Exception as e:
        return {
            "status": "Error",
            "error": str(e),
            "database_type": "Unknown"
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