import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import quote_plus

def create_tables():
    password = quote_plus("S_iXJCjL@-nf7m&")
    conn_string = f"postgresql://postgres:{password}@db.eufiyvhigestuyhzvuxc.supabase.co:5432/postgres"
    conn = None
    
    try:
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create countries table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                flag TEXT,
                region TEXT,
                visa_required BOOLEAN,
                last_updated TEXT,
                summary TEXT
            );
        """)
        
        # Create visa_types table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS visa_types (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                country_id TEXT REFERENCES countries(id),
                name TEXT NOT NULL,
                purpose TEXT,
                entry_type TEXT,
                validity TEXT,
                stay_duration TEXT,
                extendable BOOLEAN
            );
        """)
        
        # Create fees table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fees (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                visa_type_id UUID REFERENCES visa_types(id),
                type TEXT,
                amount TEXT,
                original_currency TEXT,
                note TEXT
            );
        """)
        
        # Create documents table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                country_id TEXT REFERENCES countries(id),
                name TEXT NOT NULL,
                type TEXT,
                specifications JSONB
            );
        """)
        
        # Create processing_times table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS processing_times (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                country_id TEXT REFERENCES countries(id),
                type TEXT,
                duration TEXT,
                notes TEXT
            );
        """)
        
        # Create application_processes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS application_processes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                country_id TEXT REFERENCES countries(id),
                method TEXT,
                note TEXT,
                steps JSONB,
                alternative_method JSONB
            );
        """)
        
        print("All tables created successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    create_tables() 