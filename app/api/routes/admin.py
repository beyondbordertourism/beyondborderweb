from fastapi import APIRouter, HTTPException, Query, Depends, status, Form, Response
from fastapi.responses import RedirectResponse
from typing import List, Optional
from app.models.country import Country, CountryCreate, CountryUpdate
from app.models.admin import AdminUserResponse, AdminUserCreate, AdminUserUpdate
from app.crud.country import country_crud
from app.core.auth import admin_required, authenticate_admin, create_access_token
from datetime import datetime
import config

router = APIRouter()

@router.post("/login")
async def admin_login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    """Admin login endpoint"""
    admin_user = await authenticate_admin(username, password)
    if admin_user:
        access_token = create_access_token(data={"sub": admin_user["username"]})
        response.set_cookie(
            key="admin_token",
            value=access_token,
            httponly=True,
            max_age=28800,  # 8 hours
            samesite="lax"
        )
        return {"message": "Login successful", "redirect": "/admin"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

@router.post("/logout")
async def admin_logout(response: Response):
    """Admin logout endpoint"""
    response.delete_cookie(key="admin_token")
    return {"message": "Logged out successfully"}

@router.get("/countries")
def admin_get_countries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    published: Optional[bool] = Query(None),
    region: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, regex="^(name|created_at|updated_at)$"),
    _: dict = Depends(admin_required)
):
    """Admin: Get all countries with filters"""
    countries = country_crud.get_all(skip=skip, limit=limit, published=published, region=region, search=search, sort=sort)
    # Compute total using same filters (without pagination) to preserve pagination behavior
    total = len(country_crud.get_all(skip=0, limit=1000000, published=published, region=region, search=search, sort=sort))
    
    return {
        "countries": countries,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/countries/{country_id}")
def admin_get_country(country_id: str, _: dict = Depends(admin_required)):
    """Admin: Get country by ID"""
    country = country_crud.get_by_id(country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@router.post("/countries", response_model=Country)
def admin_create_country(
    country_data: CountryCreate,
    _: dict = Depends(admin_required)
):
    """Admin: Create new country"""
    return country_crud.create(country_data)

@router.put("/countries/{country_id}", response_model=Country)
def admin_update_country(
    country_id: str,
    country_data: CountryUpdate,
    _: dict = Depends(admin_required)
):
    updated_country = country_crud.update(country_id, country_data)
    if not updated_country:
        raise HTTPException(status_code=404, detail="Country not found")

    from app.core.db import db
    payload = country_data.model_dump(exclude_unset=True)

    if payload.get("visa_types") is not None:
        db.update_visa_types(country_id, payload["visa_types"])

    if payload.get("documents") is not None:
        db.update_documents(country_id, payload["documents"])

    if payload.get("processing_times") is not None:
        db.update_processing_times(country_id, payload["processing_times"])

    if payload.get("application_methods") is not None:
        db.update_application_methods(country_id, payload["application_methods"])

    refreshed = db.get_country_by_id(country_id)
    return refreshed

@router.delete("/countries/{country_id}")
def admin_delete_country(country_id: str, _: dict = Depends(admin_required)):
    """Admin: Delete country"""
    success = country_crud.delete(country_id)
    if not success:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"message": "Country deleted successfully"}

@router.patch("/countries/{country_id}/publish")
def admin_toggle_publish(country_id: str, published: bool, _: dict = Depends(admin_required)):
    """Admin: Toggle country publish status"""
    country_data = CountryUpdate(published=published)
    updated_country = country_crud.update(country_id, country_data)
    if not updated_country:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"message": f"Country {'published' if published else 'unpublished'} successfully"}

@router.patch("/countries/{country_id}/feature")
def admin_toggle_feature(country_id: str, featured: bool, _: dict = Depends(admin_required)):
    """Admin: Toggle country featured status"""
    country_data = CountryUpdate(featured=featured)
    updated_country = country_crud.update(country_id, country_data)
    if not updated_country:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"message": f"Country {'featured' if featured else 'unfeatured'} successfully"}

@router.get("/stats")
def admin_get_stats(_: dict = Depends(admin_required)):
    """Admin: Get comprehensive statistics"""
    countries = country_crud.get_all()
    
    total_countries = len(countries)
    published_countries = len([c for c in countries if c.get('published')])
    regions = [c.get('region') for c in countries if c.get('region')]
    region_counts = {}
    for region in regions:
        if region:  # Only count non-empty regions
            region_counts[region] = region_counts.get(region, 0) + 1
    
    visa_required = len([c for c in countries if c.get('visa_required')])
    
    return {
        "total_countries": total_countries,
        "published_countries": published_countries,
        "regions": len(set(regions)),  # Count unique regions
        "region_distribution": [{"name": k, "count": v} for k, v in region_counts.items()],
        "visa_required": visa_required,
        "visa_free": total_countries - visa_required
    }

@router.get("/users", response_model=List[AdminUserResponse])
def admin_get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_admin: dict = Depends(admin_required)
):
    """Admin: Get all admin users (super admin only)"""
    if not current_admin.get("is_super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can view users"
        )
    # Return the single config-based admin user
    return [
        AdminUserResponse(
            id="config_admin",
            username=config.ADMIN_USERNAME,
            email="admin@visaguide.com",
            full_name="System Administrator",
            is_active=True,
            is_super_admin=True,
            last_login=None,
            login_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]

@router.post("/users", response_model=AdminUserResponse)
def admin_create_user(
    user_data: AdminUserCreate,
    current_admin: dict = Depends(admin_required)
):
    """Admin: Create new admin user (super admin only)"""
    raise HTTPException(status_code=403, detail="User management is disabled in this version.")

@router.get("/profile", response_model=AdminUserResponse)
def admin_get_profile(current_admin: dict = Depends(admin_required)):
    """Admin: Get current admin profile"""
    return AdminUserResponse(
        id="config_admin",
        username=current_admin["username"],
        email=current_admin["email"],
        full_name=current_admin["full_name"],
        is_active=True,
        is_super_admin=True,
        last_login=None,
        login_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@router.put("/profile", response_model=AdminUserResponse)
def admin_update_profile(
    user_data: AdminUserUpdate,
    current_admin: dict = Depends(admin_required)
):
    """Admin: Update current admin profile"""
    raise HTTPException(
        status_code=400,
        detail="Cannot update config-based admin profile"
    ) 