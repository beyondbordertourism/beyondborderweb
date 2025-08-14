#!/usr/bin/env python3
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from app.core.db import Database

def main():
    db = Database()
    db.connect()
    try:
        # Ensure 'featured' column exists
        db._cursor.execute("ALTER TABLE countries ADD COLUMN IF NOT EXISTS featured boolean DEFAULT false")
        # Ensure 'hero_image_url' column exists
        db._cursor.execute("ALTER TABLE countries ADD COLUMN IF NOT EXISTS hero_image_url text")
        db._connection.commit()
        print("✅ Ensured schema: countries.featured, countries.hero_image_url")
    finally:
        db.close()

if __name__ == "__main__":
    main() 