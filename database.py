import psycopg2
import psycopg2.extras
from config import Config

def get_db_connection():
    db_url = Config.DATABASE_URL
    if not db_url:
        print("CRITICAL: DATABASE_URL is not set.")
        return None
        
    # Fix common typos in URL
    if db_url.startswith("postgresq1://"):
        db_url = db_url.replace("postgresq1://", "postgresql://", 1)
        print("INFO: Corrected 'postgresq1' typo in DATABASE_URL")
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    try:
        connection = psycopg2.connect(db_url)
        return connection
    except psycopg2.Error as err:
        print(f"CRITICAL Database connection error: {err}")
        return None
