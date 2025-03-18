from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://openchat:Infoundr2025%23%23@localhost:5432/openchat_db')

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Create base class for models
Base = declarative_base()

def init_db():
    """Initialize database"""
    Base.metadata.create_all(engine)

def get_session():
    """Get a new database session"""
    return Session() 