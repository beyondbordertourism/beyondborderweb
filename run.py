#!/usr/bin/env python3
import uvicorn
import os

if __name__ == "__main__":
    # Get port from environment variable or use Render's default.
    port = int(os.environ.get("PORT", 10000))
    
    # Use Uvicorn to run the FastAPI application.
    # It looks for the 'app' variable in the 'app.main' module.
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )