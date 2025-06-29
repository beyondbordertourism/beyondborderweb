from fastapi import APIRouter, HTTPException, Query, Depends, status, Form, Response
from fastapi.responses import RedirectResponse
from typing import List, Optional
from app.models.country import Country, CountryCreate, CountryUpdate
from app.models.admin import AdminUserResponse, AdminUserCreate, AdminUserUpdate
from app.crud.country import country_crud
from app.crud.admin import admin_crud
from app.core.auth import admin_required, authenticate_admin, create_access_token
from datetime import datetime

router = APIRouter()

@router.post("/login")
async def admin_login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    """Admin login endpoint"""
    admin_user = await authenticate_admin(username, password)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": admin_user.username})
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,
        max_age=28800,  # 8 hours
        samesite="lax"
    )
    
    return {"message": "Login successful", "redirect": "/admin"}

@router.post("/logout")
async def admin_logout(response: Response):
    """Admin logout endpoint"""
    response.delete_cookie(key="admin_token")
    return {"message": "Logged out successfully"}

@router.get("/countries")
async def admin_get_countries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    published: Optional[bool] = Query(None),
    region: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, regex="^(name|created_at|updated_at)$"),
    _: dict = Depends(admin_required)
):
    """Admin: Get all countries with filters"""
    # Get countries and total count
    countries = await country_crud.get_all(
        skip=skip,
        limit=limit,
        published=published,
        region=region,
        search=search,
        sort=sort
    )
    total_count = await country_crud.count_all(
        published=published,
        region=region,
        search=search
    )
    
    # Return paginated response
    return {
        "countries": [country.model_dump() for country in countries],
        "total": total_count,
        "skip": skip,
        "limit": limit
    }

@router.get("/countries/{country_id}")
async def admin_get_country(country_id: str, _: dict = Depends(admin_required)):
    """Admin: Get country by ID"""
    country = await country_crud.get_by_id(country_id)
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country.model_dump()

@router.post("/countries", response_model=Country)
async def admin_create_country(
    country_data: CountryCreate,
    _: dict = Depends(admin_required)
):
    """Admin: Create new country"""
    return await country_crud.create(country_data)

@router.put("/countries/{country_id}", response_model=Country)
async def admin_update_country(
    country_id: str,
    country_data: CountryUpdate,
    _: dict = Depends(admin_required)
):
    """Admin: Update country"""
    updated_country = await country_crud.update(country_id, country_data)
    if not updated_country:
        raise HTTPException(status_code=404, detail="Country not found")
    return updated_country

@router.delete("/countries/{country_id}")
async def admin_delete_country(country_id: str, _: dict = Depends(admin_required)):
    """Admin: Delete country"""
    success = await country_crud.delete(country_id)
    if not success:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"message": "Country deleted successfully"}

@router.patch("/countries/{country_id}/publish")
async def admin_toggle_publish(country_id: str, published: bool, _: dict = Depends(admin_required)):
    """Admin: Toggle country publish status"""
    country_data = CountryUpdate(published=published)
    updated_country = await country_crud.update(country_id, country_data)
    if not updated_country:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"message": f"Country {'published' if published else 'unpublished'} successfully"}

@router.patch("/countries/{country_id}/feature")
async def admin_toggle_feature(country_id: str, featured: bool, _: dict = Depends(admin_required)):
    """Admin: Toggle country featured status"""
    country_data = CountryUpdate(featured=featured)
    updated_country = await country_crud.update(country_id, country_data)
    if not updated_country:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"message": f"Country {'featured' if featured else 'unfeatured'} successfully"}

@router.get("/stats")
async def admin_get_stats(_: dict = Depends(admin_required)):
    """Admin: Get comprehensive statistics"""
    stats = await country_crud.get_stats()
    admin_stats = {
        "total_admins": await admin_crud.count()
    }
    return {**stats, **admin_stats}

@router.get("/users", response_model=List[AdminUserResponse])
async def admin_get_users(
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
    return await admin_crud.get_all(skip=skip, limit=limit)

@router.post("/users", response_model=AdminUserResponse)
async def admin_create_user(
    user_data: AdminUserCreate,
    current_admin: dict = Depends(admin_required)
):
    """Admin: Create new admin user (super admin only)"""
    if not current_admin.get("is_super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can create users"
        )
    
    try:
        admin_user = await admin_crud.create(user_data)
        return AdminUserResponse(
            id=str(admin_user.id),
            username=admin_user.username,
            email=admin_user.email,
            full_name=admin_user.full_name,
            is_active=admin_user.is_active,
            is_super_admin=admin_user.is_super_admin,
            last_login=admin_user.last_login,
            login_count=admin_user.login_count,
            created_at=admin_user.created_at,
            updated_at=admin_user.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile", response_model=AdminUserResponse)
async def admin_get_profile(current_admin: dict = Depends(admin_required)):
    """Admin: Get current admin profile"""
    if current_admin.get("id") == "config_admin":
        # Return config-based admin profile
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
    
    admin_user = await admin_crud.get_by_id(current_admin["id"])
    if not admin_user:
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    return AdminUserResponse(
        id=str(admin_user.id),
        username=admin_user.username,
        email=admin_user.email,
        full_name=admin_user.full_name,
        is_active=admin_user.is_active,
        is_super_admin=admin_user.is_super_admin,
        last_login=admin_user.last_login,
        login_count=admin_user.login_count,
        created_at=admin_user.created_at,
        updated_at=admin_user.updated_at
    )

@router.put("/profile", response_model=AdminUserResponse)
async def admin_update_profile(
    user_data: AdminUserUpdate,
    current_admin: dict = Depends(admin_required)
):
    """Admin: Update current admin profile"""
    if current_admin.get("id") == "config_admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot update config-based admin profile"
        )
    
    updated_admin = await admin_crud.update(current_admin["id"], user_data)
    if not updated_admin:
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    return AdminUserResponse(
        id=str(updated_admin.id),
        username=updated_admin.username,
        email=updated_admin.email,
        full_name=updated_admin.full_name,
        is_active=updated_admin.is_active,
        is_super_admin=updated_admin.is_super_admin,
        last_login=updated_admin.last_login,
        login_count=updated_admin.login_count,
        created_at=updated_admin.created_at,
        updated_at=updated_admin.updated_at
    ) 