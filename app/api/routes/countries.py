from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.country import Country
from app.core.db import db

router = APIRouter()

@router.get("/", response_model=List[Country])
async def get_countries(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    region: Optional[str] = None,
    visa_required: Optional[bool] = None
):
    """Get all published countries with optional filtering"""
    countries = db.get_all_countries()
    
    # Filter to only published countries
    countries = [c for c in countries if c.get('published') == True]
    
    # Apply additional filters
    if region:
        countries = [c for c in countries if c.get('region') == region]
    if visa_required is not None:
        countries = [c for c in countries if c.get('visa_required') == visa_required]
    
    # Apply pagination
    total = len(countries)
    countries = countries[skip:skip + limit]
    
    return countries

@router.get("/featured", response_model=List[Country])
async def get_featured_countries(limit: int = Query(6, ge=1, le=20)):
    """Get featured countries for homepage"""
    countries = db.get_all_countries()
    # Filter to only published and featured countries
    featured = [c for c in countries if c.get('published') == True and c.get('featured', False)][:limit]
    return featured

@router.get("/regions")
async def get_regions():
    """Get all available regions"""
    countries = db.get_all_countries()
    # Filter to only published countries
    published_countries = [c for c in countries if c.get('published') == True]
    regions = list(set(c.get('region') for c in published_countries if c.get('region')))
    return {"regions": regions}

@router.get("/search", response_model=List[Country])
async def search_countries(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50)
):
    """Search countries by name or content"""
    all_results = db.search_countries(q)
    # Filter to only published countries
    published_results = [c for c in all_results if c.get('published') == True]
    return published_results[:limit]

@router.get("/stats")
async def get_stats():
    """Get public statistics about countries"""
    countries = db.get_all_countries()
    # Filter to only published countries
    published_countries = [c for c in countries if c.get('published') == True]
    
    # Calculate stats
    total_countries = len(published_countries)
    regions = list(set(c.get('region') for c in published_countries if c.get('region')))
    visa_required = len([c for c in published_countries if c.get('visa_required')])
    visa_free = total_countries - visa_required
    
    return {
        "total_countries": total_countries,
        "regions": len(regions),
        "visa_required": visa_required,
        "visa_free": visa_free,
        "debug": {
            "database_type": "Supabase PostgreSQL",
            "raw_stats": {
                "region_distribution": regions,
                "published_countries": total_countries
            }
        }
    }

@router.get("/{country_id}", response_model=Country)
async def get_country_by_id(country_id: str):
    """Get a specific country by its ID"""
    country = db.get_country_by_id(country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    # Check if country is published
    if not country.get('published'):
        raise HTTPException(status_code=404, detail="Country not found")
    
    return country