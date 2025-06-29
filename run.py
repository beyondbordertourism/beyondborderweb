#!/usr/bin/env python3
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force rebuild and clear any cache - added missing countries to file storage
if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true",
        log_level="info"
    ) 