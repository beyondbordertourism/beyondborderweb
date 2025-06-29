from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
import os

from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.routes import countries, admin
from app.core.auth import verify_token
from app.crud.admin import admin_crud
import config

# Create FastAPI app
app = FastAPI(
    title="Visa Guide API",
    description="API for visa information and admin management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(countries.router, prefix="/api/countries", tags=["Countries"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    
    # Initialize default admin user if none exists
    try:
        admin_count = await admin_crud.count()
        if admin_count == 0:
            print("🔧 Creating default admin user...")
            await admin_crud.create_default_admin()
            print("✅ Default admin user created successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not create default admin user: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

def check_admin_auth(admin_token: Optional[str] = Cookie(None)) -> bool:
    if not admin_token:
        return False
    payload = verify_token(admin_token)
    if payload is None:
        return False
    username = payload.get("sub")
    return username == config.ADMIN_USERNAME

# Basic routes for the website
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/countries", response_class=HTMLResponse)
async def countries_page(request: Request):
    return templates.TemplateResponse("countries.html", {"request": request})

@app.get("/countries/{slug}", response_class=HTMLResponse)
async def country_detail(request: Request, slug: str):
    return templates.TemplateResponse("country_detail.html", {"request": request, "slug": slug})

@app.get("/search", response_class=HTMLResponse)
async def search_results(request: Request):
    return templates.TemplateResponse("search_results.html", {"request": request})

# Admin routes with authentication
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, admin_token: Optional[str] = Cookie(None)):
    # If already logged in, redirect to admin dashboard
    if check_admin_auth(admin_token):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin/login.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin_token: Optional[str] = Cookie(None)):
    if not check_admin_auth(admin_token):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@app.get("/admin/countries", response_class=HTMLResponse)
async def admin_countries(request: Request, admin_token: Optional[str] = Cookie(None)):
    if not check_admin_auth(admin_token):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse("admin/countries.html", {"request": request})

@app.get("/admin/countries/new", response_class=HTMLResponse)
async def admin_new_country(request: Request, admin_token: Optional[str] = Cookie(None)):
    if not check_admin_auth(admin_token):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse("admin/country_form.html", {"request": request})

@app.get("/admin/countries/{country_id}/edit", response_class=HTMLResponse)
async def admin_edit_country(request: Request, country_id: str, admin_token: Optional[str] = Cookie(None)):
    if not check_admin_auth(admin_token):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse("admin/country_form.html", {"request": request, "country_id": country_id})

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 