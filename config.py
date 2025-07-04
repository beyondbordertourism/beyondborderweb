import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://eufiyvhigestuyhzvuxc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-jwt-secret")

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "db.eufiyvhigestuyhzvuxc.supabase.co")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "S_iXJCjL@-nf7m&")

# Application Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# File Storage Settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Email Settings (if needed)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@example.com") 