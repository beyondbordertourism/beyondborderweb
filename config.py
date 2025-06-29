import os

# MongoDB Atlas Configuration
# Replace "your_password_here" with your actual MongoDB Atlas password
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://inshamanowar22:YVfCabwE81MkSY68@visa-countries.gsywcpw.mongodb.net/")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "YVfCabwE81MkSY68")
DATABASE_NAME = os.getenv("DATABASE_NAME", "visa_website")

# Application Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Admin Authentication Configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

# Replace password placeholder if password is provided
if MONGODB_PASSWORD and "YVfCabwE81MkSY68" in MONGODB_URL:
    MONGODB_URL = MONGODB_URL.replace("YVfCabwE81MkSY68", MONGODB_PASSWORD) 