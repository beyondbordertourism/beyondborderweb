import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://inshamanowar22_db_user:gCHLC03QnvtTtdLP@beyondborders.pmw8pvm.mongodb.net/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "beyondborder")

# Application Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# File Storage Settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Email Settings
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM") 



