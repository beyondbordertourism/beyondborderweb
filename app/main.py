from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
import os

from app.api.routes import countries, admin
from app.core.auth import verify_token
import config

# Create FastAPI app
app = FastAPI(
    title="Visa Information API",
    description="API for retrieving visa information for Indian passport holders",
    version="2.0.0"
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
app.include_router(countries.router, prefix="/api/countries", tags=["countries"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

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

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Visa Information API",
        "version": "2.0.0",
        "database": "Supabase PostgreSQL"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 