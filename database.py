import psycopg2
import psycopg2.extras
from config import Config

def get_db_connection():
    db_url = Config.DATABASE_URL
    if not db_url:
        print("CRITICAL: DATABASE_URL is not set.")
        return None
        
    # Standardize URL and fix typos
    db_url = db_url.replace("postgresq1://", "postgresql://", 1)
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # Ensure SSL is enabled (required by Neon)
    if "?" not in db_url:
        db_url += "?sslmode=require"
    elif "sslmode=" not in db_url:
        db_url += "&sslmode=require"
        
    try:
        connection = psycopg2.connect(db_url)
        return connection
    except psycopg2.Error as err:
        print(f"CRITICAL Database connection error: {err}")
        print(f"DEBUG: Attempted URL starts with: {db_url[:20]}...")
        return None
