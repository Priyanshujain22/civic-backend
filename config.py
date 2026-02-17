import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key'
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    @staticmethod
    def validate():
        if not Config.DATABASE_URL:
            print("WARNING: DATABASE_URL environment variable is not set.")
            return False
        return True
