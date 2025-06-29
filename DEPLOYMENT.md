# Deployment Guide

## Quick Start (Local Development)

The application has been fixed and now runs gracefully even without MongoDB connection, making it easy to test locally.

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python run.py
```

The application will start on `http://localhost:8000` and will show warnings about MongoDB not being available, but all endpoints will work (returning empty data).

### 3. Access the Application
- **Homepage**: http://localhost:8000/
- **Admin Dashboard**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Database Setup

### Option 1: Local MongoDB
1. Install MongoDB locally
2. Start MongoDB service: `brew services start mongodb/brew/mongodb-community` (macOS)
3. The app will automatically connect to `mongodb://localhost:27017`

### Option 2: MongoDB Atlas (Recommended for Production)
1. Create a free MongoDB Atlas account
2. Create a cluster and get connection string
3. Set environment variable: `MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/`

### Import Sample Data
```bash
python scripts/import_data.py
```

## Environment Variables

Create a `.env` file in the root directory:

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=visa_website

# Application Configuration
PORT=8000
DEBUG=true
```

## Production Deployment

### Free Hosting Options

#### 1. Railway (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Add MongoDB Atlas connection string in Railway environment variables.

#### 2. Render
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python run.py`
4. Add environment variables in Render dashboard

#### 3. Fly.io
```bash
# Install Fly CLI
flyctl deploy
```

### Environment Variables for Production
```env
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=visa_website
PORT=8000
DEBUG=false
```

## Features Working Without Database
- ✅ Application starts and serves pages
- ✅ API endpoints return empty data gracefully
- ✅ Frontend loads and displays properly
- ✅ Admin interface accessible
- ⚠️ No data persistence until database is connected

## Troubleshooting

### Pydantic v2 Compatibility
The application has been updated to work with Pydantic v2. If you encounter any Pydantic-related errors, ensure you're using the versions specified in `requirements.txt`.

### Port Already in Use
If you get "address already in use" error:
```bash
# Kill existing processes
pkill -f "python run.py"
# Or use a different port
PORT=8001 python run.py
```

### MongoDB Connection Issues
The application will start without MongoDB and log warnings. This is normal for development. For production, ensure your MongoDB connection string is correct.

## Next Steps

1. **Connect Database**: Set up MongoDB Atlas for data persistence
2. **Import Data**: Run the import script to populate with visa information
3. **Customize**: Modify templates and add your own visa data
4. **Deploy**: Use one of the free hosting options above

The application is now ready to run and can be deployed to any platform that supports Python web applications! 