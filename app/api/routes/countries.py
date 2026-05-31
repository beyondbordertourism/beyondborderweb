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
    countries = await db._get_all_countries_async()
    countries = [c for c in countries if c.get('published') is True]

    if region:
        countries = [c for c in countries if c.get('region') == region]
    if visa_required is not None:
        countries = [c for c in countries if c.get('visa_required') == visa_required]

    return countries[skip:skip + limit]


@router.get("/featured", response_model=List[Country])
async def get_featured_countries(limit: int = Query(6, ge=1, le=20)):
    countries = await db._get_all_countries_async()
    return [c for c in countries if c.get('published') is True and c.get('featured', False)][:limit]


@router.get("/regions")
async def get_regions():
    countries = await db._get_all_countries_async()
    published = [c for c in countries if c.get('published') is True]
    regions = sorted(set(c.get('region') for c in published if c.get('region')))
    return {"regions": regions}


@router.get("/search", response_model=List[Country])
async def search_countries(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50)
):
    results = await db._search_countries_async(q)
    return [c for c in results if c.get('published') is True][:limit]


@router.get("/stats")
async def get_stats():
    countries = await db._get_all_countries_async()
    published = [c for c in countries if c.get('published') is True]
    regions = sorted(set(c.get('region') for c in published if c.get('region')))
    visa_required = sum(1 for c in published if c.get('visa_required'))
    return {
        "total_countries": len(published),
        "regions": len(regions),
        "visa_required": visa_required,
        "visa_free": len(published) - visa_required,
    }


@router.get("/{country_id}", response_model=Country)
async def get_country_by_id(country_id: str):
    country = await db._get_country_by_id_async(country_id)
    if not country or not country.get('published'):
        raise HTTPException(status_code=404, detail="Country not found")
    return country
