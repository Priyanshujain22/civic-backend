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
        print("Ensuring critical columns...")
        cursor.execute("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS resolution_notes TEXT;")
        cursor.execute("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS resolution_type VARCHAR(20);")
        cursor.execute("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS selected_vendor_id INT;")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);")

        # Fix users_role_check constraint to include 'vendor'
        print("Updating users_role_check constraint...")
        cursor.execute("""
            ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
            ALTER TABLE users ADD CONSTRAINT users_role_check 
            CHECK (role IN ('citizen', 'admin', 'officer', 'vendor'));
        """)

        # Fix complaints_status_check constraint to include 'Routed' and 'Awaiting Quotes'
        print("Updating complaints_status_check constraint...")
        # We try multiple common names just in case
        names = ['complaints_status_check', 'status_check']
        for name in names:
            cursor.execute(f"ALTER TABLE complaints DROP CONSTRAINT IF EXISTS {name};")
        
        cursor.execute("""
            ALTER TABLE complaints ADD CONSTRAINT complaints_status_check 
            CHECK (status IN ('Pending', 'Routed', 'Awaiting Quotes', 'In Progress', 'Resolved'));
        """)

        # Ensure categories exist
        print("Syncing categories...")
        categories = ['Road Damage', 'Garbage', 'Street Light', 'Water Leakage', 'Drainage', 'Other']
        for cat in categories:
            cursor.execute("INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (cat,))
        
        # Seed Test Users
        print("Seeding test users (Officers & Vendors)...")
        from werkzeug.security import generate_password_hash
        hashed_pw = generate_password_hash('password123')

        test_users = [
            # Officers
            ('Road Off', 'road@test.com', 'officer', 'Road Damage'),
            ('Garbage Off', 'garbage@test.com', 'officer', 'Garbage'),
            ('General Off', 'general@test.com', 'officer', 'General'),
            # Vendors
            ('Fixer Ltd', 'fixer@test.com', 'vendor', 'Road Damage'),
            ('Clean Co', 'clean@test.com', 'vendor', 'Garbage'),
            ('Test Vendor', 'vendor@test.com', 'vendor', 'General')
        ]

        for name, email, role, dept in test_users:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(
                    "INSERT INTO users (name, email, password, role, department) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (name, email, hashed_pw, role, dept)
                )
                uid = cursor.fetchone()[0]
                if role == 'vendor':
                    cursor.execute(
                        "INSERT INTO vendors (user_id, business_name, service_type, verified) VALUES (%s, %s, %s, TRUE) ON CONFLICT (user_id) DO NOTHING",
                        (uid, name, dept)
                    )
        
        conn.commit()
        cursor.close()
        print("✅ Database migration and seeding successful.")
    except Exception as e:
        print(f"❌ Migration error: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()
