# db/database.py
from sqlalchemy.dialects import registry
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
from urllib.parse import quote

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

registry.register("turso.http", "db.turso_dialect", "TursoDialect")

try:
    from db.turso_dialect import TursoDialect
    TURSO_AVAILABLE = True
except ImportError:
    try:
        from .turso_dialect import TursoDialect
        TURSO_AVAILABLE = True
    except ImportError as e:
        TURSO_AVAILABLE = False
        logging.warning(f"Turso dialect not available: {e}")

logger = logging.getLogger(__name__)

def test_turso_connection(db_url: str) -> bool:
    try:
        logger.info(f"Testing Turso connection with URL: {db_url[:100]}...")  # Log partial URL
        test_engine = create_engine(db_url, pool_pre_ping=True)
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"Test query result: {result.fetchone()}")
        test_engine.dispose()
        logger.info("Turso connection test successful")
        return True
    except Exception as e:
        logger.error(f"Turso connection test failed: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
def get_database_url():
   
    if settings.USE_TURSO and TURSO_AVAILABLE:
        turso_url = settings.TURSO_DATABASE_URL
        turso_token = settings.TURSO_AUTH_TOKEN
        
        if turso_url and turso_token:
            encoded_url = quote(turso_url, safe='')
            encoded_token = quote(turso_token, safe='')
            db_url = f"turso+http://?database_url={encoded_url}&auth_token={encoded_token}"
            logger.info("Attempting to use Turso distributed database")
            
            if test_turso_connection(db_url):
                logger.info("Turso connection successful")
                return db_url
            else:
                logger.warning("Turso connection failed, falling back to SQLite")

    if settings.DATABASE_URL:
        logger.info("Using configured database URL")
        return settings.DATABASE_URL

    logger.info("Using local SQLite database")
    return "sqlite:///./sagago.db"

DATABASE_URL = get_database_url()
logger.info(f"Database URL type: {DATABASE_URL.split('://')[0] if '://' in DATABASE_URL else 'unknown'}")

try:
    if DATABASE_URL.startswith("turso"):
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=5,
            max_overflow=10
        )
        logger.info("Using Turso distributed SQLite")
        
    elif DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        logger.info("Using SQLite")
        
    else:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        logger.info("Using other database")
        
except Exception as e:
    logger.error(f"Failed to create engine: {e}")
    logger.warning("Falling back to SQLite")
    engine = create_engine(
        "sqlite:///./sagago.db",
        connect_args={"check_same_thread": False}
    )

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
    
    if DATABASE_URL.startswith("sqlite") and not DATABASE_URL.startswith("turso"):
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
            logger.info("Database connection successful")
            
            if DATABASE_URL.startswith("sqlite") and not DATABASE_URL.startswith("turso"):
                try:
                    conn.execute(text("CREATE TABLE IF NOT EXISTS _test (id INTEGER)"))
                    conn.execute(text("DROP TABLE _test"))
                    logger.info("Database is writable")
                except Exception as e:
                    logger.error(f"Database write test failed: {e}")
            
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

if settings.USE_TURSO:
    check_database()