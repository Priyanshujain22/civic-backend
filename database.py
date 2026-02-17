import psycopg2
import psycopg2.extras
from config import Config

def get_db_connection():
    db_url = Config.DATABASE_URL
    if not db_url:
        print("CRITICAL: DATABASE_URL is not set.")
        return None
        
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
