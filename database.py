import psycopg2
import psycopg2.extras
from config import Config

def get_db_connection():
    try:
        connection = psycopg2.connect(Config.DATABASE_URL)
        return connection
    except psycopg2.Error as err:
        print(f"Database connection error: {err}")
        return None
