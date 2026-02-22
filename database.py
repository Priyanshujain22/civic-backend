import psycopg2
import psycopg2.extras
from config import Config

def get_db_connection():
    db_url = Config.DATABASE_URL
    if not db_url:
        print("CRITICAL: DATABASE_URL is not set.")
        return None
    
    db_url = db_url.strip()
        
    # Standardize URL and fix typos (handle postgresq1, postgres, etc.)
    import re
    db_url = re.sub(r'^postgres(q1)?://', 'postgresql://', db_url)
    
    # Ensure SSL is enabled (required by Neon)
    if "sslmode=" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}sslmode=require"
        
    try:
        # Set a short timeout for the connection attempt
        connection = psycopg2.connect(db_url, connect_timeout=10)
        return connection
    except Exception as err:
        print(f"CRITICAL Database connection error: {type(err).__name__}: {err}")
        # Only log the start of the URL for privacy, but enough to see the host
        clean_url_start = db_url.split('@')[-1] if '@' in db_url else db_url[:30]
        print(f"DEBUG: Attempted connection to host part: {clean_url_start}")
        return None

def run_db_migrations():
    conn = None
    try:
        conn = get_db_connection()
        if not conn: 
            print("Migration failed: Could not connect to database.")
            return
        cursor = conn.cursor()
        
        # Ensure critical columns exist
        cursor.execute("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS resolution_notes TEXT;")
        cursor.execute("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS resolution_type VARCHAR(20);")
        cursor.execute("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS selected_vendor_id INT;")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);")

        # Fix users_role_check constraint to include 'vendor'
        cursor.execute("""
            ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
            ALTER TABLE users ADD CONSTRAINT users_role_check 
            CHECK (role IN ('citizen', 'admin', 'officer', 'vendor'));
        """)

        # Ensure categories exist
        categories = ['Road Damage', 'Garbage', 'Street Light', 'Water Leakage', 'Drainage', 'Other']
        for cat in categories:
            cursor.execute("INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (cat,))
        
        conn.commit()
        cursor.close()
        print("✅ Database migration successful.")
    except Exception as e:
        print(f"❌ Migration error: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()
