from fastapi import FastAPI, Request, HTTPException, Depends, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
import os

from app.api.routes import countries, admin
from app.core.auth import verify_token, get_current_admin
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
async def serve_home(request: Request):
    """Serves the home.html page."""
    return templates.TemplateResponse(request=request, name="home.html")

@app.get("/countries", response_class=HTMLResponse)
async def countries_page(request: Request):
    return templates.TemplateResponse(request=request, name="countries.html")

@app.get("/countries/{country_id}", response_class=HTMLResponse)
async def serve_country_page(request: Request, country_id: str):
    return templates.TemplateResponse(request=request, name="country_detail.html", context={"country_id": country_id})

@app.get("/search", response_class=HTMLResponse)
async def search_results(request: Request):
    return templates.TemplateResponse(request=request, name="search_results.html")

@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    return templates.TemplateResponse(request=request, name="contact.html")

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse(request=request, name="about.html")

@app.post("/contact")
async def handle_contact_form(request: Request):
    return templates.TemplateResponse(request=request, name="contact.html", context={"message": "Your message has been sent successfully!"})

# Admin routes with authentication
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin/login.html")

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    token = request.cookies.get("admin_token")
    if not token or not await get_current_admin(request, token):
        return RedirectResponse(url="/admin/login")
    return templates.TemplateResponse(request=request, name="admin/dashboard.html")

@app.get("/admin/countries", response_class=HTMLResponse)
async def admin_countries(request: Request):
    token = request.cookies.get("admin_token")
    if not token or not await get_current_admin(request, token):
        return RedirectResponse(url="/admin/login")
    return templates.TemplateResponse(request=request, name="admin/countries.html")

@app.get("/admin/countries/new", response_class=HTMLResponse)
async def admin_new_country(request: Request):
    token = request.cookies.get("admin_token")
    if not token or not await get_current_admin(request, token):
        return RedirectResponse(url="/admin/login")
    return templates.TemplateResponse(request=request, name="admin/country_form.html", context={"country_id": None})

@app.get("/admin/countries/{country_id}/edit", response_class=HTMLResponse)
async def admin_edit_country(request: Request, country_id: str):
    token = request.cookies.get("admin_token")
    if not token or not await get_current_admin(request, token):
        return RedirectResponse(url="/admin/login")
    return templates.TemplateResponse(request=request, name="admin/country_form.html", context={"country_id": country_id})

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Welcome to Beyond Borders"}

@app.on_event("startup")
async def startup_event():
    from app.core.database import connect_to_mongo, db
    await connect_to_mongo()
    await _ensure_admin_user(db)
    print("Application startup complete.")

async def _ensure_admin_user(db):
    """Create the admin user from config if no admin exists yet."""
    try:
        import config
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        collection = db.adapter["admin_users"]
        if await collection.count_documents({}) == 0:
            username = getattr(config, 'ADMIN_USERNAME', 'admin')
            password = getattr(config, 'ADMIN_PASSWORD', 'admin123')
            await collection.insert_one({
                "username": username,
                "email": "admin@beyondborders.com",
                "password_hash": pwd_context.hash(password),
                "full_name": "System Administrator",
                "is_active": True,
                "is_super_admin": True,
                "last_login": None,
                "login_count": 0,
                "created_at": __import__('datetime').datetime.utcnow(),
                "updated_at": __import__('datetime').datetime.utcnow(),
            })
            print(f"✅ Admin user '{username}' created.")
        else:
            print("✅ Admin user already exists.")
    except Exception as e:
        print(f"⚠️  Could not ensure admin user: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    from app.core.database import close_mongo_connection
    await close_mongo_connection()
    print("Application shutdown complete.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 