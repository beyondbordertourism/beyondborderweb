#!/usr/bin/env python3
import os
from app import app
from app.core.db import db

@app.route('/health')
def health_check():
    try:
        # Test database connection
        conn = db.connect()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        db.close()
        return {"status": "healthy", "database": "connected"}, 200
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}, 500

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 10000))
    
    # Run the application
    app.run(host="0.0.0.0", port=port)