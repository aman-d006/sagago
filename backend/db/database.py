# db/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
from urllib.parse import quote

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

# Import our working Turso client
from db.turso_client import TursoClient

logger = logging.getLogger(__name__)

# Global Turso client instance
_turso_client = None

def get_turso_client():
    """Get or create Turso client"""
    global _turso_client
    if _turso_client is None and settings.USE_TURSO:
        _turso_client = TursoClient(
            settings.TURSO_DATABASE_URL,
            settings.TURSO_AUTH_TOKEN
        )
    return _turso_client

def test_turso_connection():
    """Test Turso connection using our direct client"""
    try:
        client = get_turso_client()
        if client:
            result = client.query("SELECT 1")
            logger.info(f"Turso connection test result: {result}")
            return True
    except Exception as e:
        logger.error(f"Turso connection test failed: {e}")
        return False
    return False

def get_database_url():
    # Use Turso via our direct client, not SQLAlchemy
    if settings.USE_TURSO:
        logger.info("Using Turso distributed database (direct client)")
        # Return SQLite URL as fallback for SQLAlchemy parts that don't use Turso
        # The actual Turso connection will be handled by get_turso_client()
        return "sqlite:///./turso_fallback.db"
    
    if settings.DATABASE_URL:
        logger.info("Using configured database URL")
        return settings.DATABASE_URL

    logger.info("Using local SQLite database")
    return "sqlite:///./sagago.db"

DATABASE_URL = get_database_url()

# Create SQLite engine for non-Turso operations
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    logger.info("Using SQLite engine")
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    logger.info("Using other database engine")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return
    
    # SQLite-specific migrations
    if DATABASE_URL.startswith("sqlite"):
        try:
            with engine.begin() as conn:
                result = conn.execute(text("PRAGMA table_info('story_jobs')"))
                cols = [row[1] for row in result.fetchall()]
                if 'completed_at' not in cols:
                    conn.execute(text("ALTER TABLE story_jobs ADD COLUMN completed_at DATETIME"))
                    logger.info("Added completed_at column to story_jobs")
                
                result = conn.execute(text("PRAGMA table_info('users')"))
                cols = [row[1] for row in result.fetchall()]
                if 'avatar_url' not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))
                    logger.info("Added avatar_url column to users")
                    
        except Exception as e:
            logger.error(f"Migration error (non-critical): {e}")

def check_database():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("SQLite connection successful")
            
            # Test Turso if enabled
            if settings.USE_TURSO:
                if test_turso_connection():
                    logger.info("✅ Turso connection successful")
                else:
                    logger.error("❌ Turso connection failed")
            
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

if settings.USE_TURSO:
    check_database()