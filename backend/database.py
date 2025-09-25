from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables with fallbacks
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')

if not DB_USER or not DB_PASS:
    raise ValueError("Database credentials not found in environment variables")

# Database configuration
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@indus-digital-projects.cfu6suc24hx8.ap-south-1.rds.amazonaws.com/clientregisterationform"

print(f"Database URL: {DATABASE_URL.split('@')[0]}@***")  # Print masked URL for security

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()