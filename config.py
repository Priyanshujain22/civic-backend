import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://neondb_owner:npg_Mv0yS1LOdiYR@ep-sparkling-waterfall-a1uwiaaq-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'
