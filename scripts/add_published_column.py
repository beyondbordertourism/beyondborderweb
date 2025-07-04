import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import quote_plus

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def add_published_column():
    conn_string = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    conn = None
    
    try:
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Add published column if it doesn't exist
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = 'countries' 
                    AND column_name = 'published'
                ) THEN
                    ALTER TABLE countries ADD COLUMN published BOOLEAN DEFAULT true;
                END IF;
            END $$;
        """)
        
        print("✅ Published column added successfully!")
        
        # Set all existing countries to published=true
        cur.execute("""
            UPDATE countries 
            SET published = true 
            WHERE published IS NULL;
        """)
        
        print("✅ All existing countries set to published=true")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    add_published_column() 