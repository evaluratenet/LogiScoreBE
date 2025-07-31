from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Ensure PostgreSQL dialect is specified
if DATABASE_URL.startswith('postgres'):
    if not DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create SQLAlchemy engine lazily
def get_engine():
    """Get database engine, creating it if necessary"""
    if not hasattr(get_engine, '_engine'):
        if DATABASE_URL.startswith('postgres'):
            # PostgreSQL configuration
            get_engine._engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False
            )
        else:
            # SQLite fallback for development
            get_engine._engine = create_engine(
                DATABASE_URL,
                connect_args={"check_same_thread": False},
                echo=False
            )
    return get_engine._engine

# Create SessionLocal class
def get_session_local():
    """Get SessionLocal class"""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

# Create Base class
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 