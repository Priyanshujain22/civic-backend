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
        
        # Ensure vendors table exists (to prevent relation does not exist error)
        print("Ensuring vendors table exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                id SERIAL PRIMARY KEY,
                user_id INT UNIQUE NOT NULL,
                business_name VARCHAR(100) NOT NULL,
                service_type VARCHAR(100),
                verified BOOLEAN DEFAULT FALSE,
                rating DECIMAL(3,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Ensure quotations table exists
        print("Ensuring quotations table exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotations (
                id SERIAL PRIMARY KEY,
                complaint_id INT NOT NULL,
                vendor_id INT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                estimated_time VARCHAR(50),
                status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
                FOREIGN KEY (vendor_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Ensure feedback table exists
        print("Ensuring feedback table exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                complaint_id INT NOT NULL,
                rating INT CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE
            );
        """)

        # Ensure job_updates table exists
        print("Ensuring job_updates table exists...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_updates (
                id SERIAL PRIMARY KEY,
                complaint_id INT NOT NULL,
                vendor_id INT NOT NULL,
                message TEXT NOT NULL,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
                FOREIGN KEY (vendor_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Seed Test Users
        print("Seeding test users (Officers & Vendors)...")
        # Direct passwords as requested by user
        
        test_users = [
            # Admin & Officers
            ('System Admin', 'admin@system.com', 'admin@123', 'admin', 'General'),
            ('General Off', 'general@test.com', 'password123', 'officer', 'General'),
            ('Road Off', 'road@test.com', 'password123', 'officer', 'Road Damage'),
            # Vendors
            ('Waste Expert', 'waste@test.com', 'password123', 'vendor', 'Waste Management'),
            ('Fixer Ltd', 'fixer@test.com', 'password123', 'vendor', 'Road Damage'),
            ('Test Vendor', 'vendor@test.com', 'password123', 'vendor', 'General')
        ]

        for name, email, password, role, dept in test_users:
            # Get or create user
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_row = cursor.fetchone()
            
            if not user_row:
                cursor.execute(
                    "INSERT INTO users (name, email, password, role, department) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (name, email, password, role, dept)
                )
                uid = cursor.fetchone()[0]
            else:
                uid = user_row[0]
                # Force password and department update for test accounts to ensure login works
                cursor.execute("UPDATE users SET password = %s, department = %s WHERE id = %s", (password, dept, uid))

            # Always ensure vendor profile exists if role is vendor
            if role == 'vendor':
                cursor.execute(
                    "INSERT INTO vendors (user_id, business_name, service_type, verified) VALUES (%s, %s, %s, TRUE) ON CONFLICT (user_id) DO UPDATE SET service_type = EXCLUDED.service_type, business_name = EXCLUDED.business_name",
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

if __name__ == "__main__":
    run_db_migrations()
