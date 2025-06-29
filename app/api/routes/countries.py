from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.models.country import Country
from app.crud.country import country_crud

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

@router.get("/{slug}", response_model=Country)
async def get_country_by_slug(slug: str):
    """Get a specific country by slug"""
    country = await country_crud.get_by_slug(slug)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    if not country.published:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return country 