# db/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
from urllib.parse import quote
import sys
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from db.turso_client import init_pool, get_client, return_client, close_pool, get_pool_stats
from db.retry import with_retry

logger = logging.getLogger(__name__)

# Initialize pool on module load if Turso is enabled
_turso_initialized = False

def init_database_pool():
    """Initialize the Turso connection pool"""
    global _turso_initialized
    if settings.USE_TURSO and not _turso_initialized:
        try:
            init_pool(
                settings.TURSO_DATABASE_URL,
                settings.TURSO_AUTH_TOKEN,
                max_connections=5
            )
            _turso_initialized = True
            logger.info("✅ Turso connection pool initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Turso pool: {e}")

@contextmanager
def get_turso_client():
    """Get a client from the pool (context manager)"""
    if not settings.USE_TURSO:
        yield None
        return
    
    client = None
    try:
        client = get_client()
        yield client
    finally:
        if client:
            return_client(client)

@with_retry(max_attempts=3)
def execute_with_retry(client, sql, params=None):
    """Execute query with retry logic"""
    return client.query(sql, params)

def test_turso_connection():
    """Test Turso connection using pooled client"""
    try:
        with get_turso_client() as client:
            if client:
                result = client.query("SELECT 1")
                logger.info(f"✅ Turso connection test successful: {result}")
                return True
    except Exception as e:
        logger.error(f"❌ Turso connection test failed: {e}")
        return False
    return False

def get_database_url():
    # Use Turso via our direct client, not SQLAlchemy
    if settings.USE_TURSO:
        logger.info("📁 Using Turso distributed database (direct client)")
        return "sqlite:///./turso_fallback.db"
    
    if settings.DATABASE_URL:
        logger.info("📁 Using configured database URL")
        return settings.DATABASE_URL

    logger.info("📁 Using local SQLite database")
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
    logger.info("✅ Using SQLite engine")
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    logger.info("✅ Using other database engine")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    logger.info("📊 Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created/verified")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return
    
    # SQLite-specific migrations
    if DATABASE_URL.startswith("sqlite"):
        try:
            with engine.begin() as conn:
                result = conn.execute(text("PRAGMA table_info('story_jobs')"))
                cols = [row[1] for row in result.fetchall()]
                if 'completed_at' not in cols:
                    conn.execute(text("ALTER TABLE story_jobs ADD COLUMN completed_at DATETIME"))
                    logger.info("✅ Added completed_at column to story_jobs")
                
                result = conn.execute(text("PRAGMA table_info('users')"))
                cols = [row[1] for row in result.fetchall()]
                if 'avatar_url' not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))
                    logger.info("✅ Added avatar_url column to users")
                    
        except Exception as e:
            logger.error(f"⚠️ Migration error (non-critical): {e}")

def check_database():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✅ SQLite connection successful")
            
            # Test Turso if enabled
            if settings.USE_TURSO:
                if test_turso_connection():
                    logger.info("✅ Turso connection successful")
                else:
                    logger.error("❌ Turso connection failed")
            
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def get_database_stats():
    """Get database statistics for monitoring"""
    stats = {
        'turso_enabled': settings.USE_TURSO,
        'pool': get_pool_stats(),
    }
    
    if settings.USE_TURSO:
        try:
            with get_turso_client() as client:
                # Get database size
                size = client.query_value("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = size
                
                # Get table counts
                tables = client.query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                for table in tables:
                    count = client.query_value(f"SELECT COUNT(*) FROM {table[0]}")
                    stats[f'count_{table[0]}'] = count
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            stats['error'] = str(e)
    
    return stats

def shutdown_database():
    """Clean up database connections"""
    close_pool()
    logger.info("✅ Database connections closed")

# Initialize pool on import if Turso is enabled
if settings.USE_TURSO:
    init_database_pool()