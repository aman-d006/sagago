from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging

from core.config import settings

logger = logging.getLogger(__name__)

def get_database_url():
    if os.getenv("RENDER"):
        db_path = "/data/sagago.db"
        os.makedirs("/data", exist_ok=True)
        try:
            test_file = "/data/test_write.txt"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"✅ Render disk is writable at: /data")
        except Exception as e:
            logger.error(f"❌ Render disk write error: {e}")
            db_path = "./sagago.db"
            logger.warning(f"⚠️ Falling back to: {db_path}")
        database_url = f"sqlite:///{db_path}"
        logger.info(f"📁 Using Render disk database at: {db_path}")
        return database_url
    
    if settings.DATABASE_URL:
        logger.info(f"📁 Using configured database URL")
        return settings.DATABASE_URL
    
    logger.info("📁 Using local SQLite database")
    return "sqlite:///./sagago.db"

DATABASE_URL = get_database_url()

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        pool_recycle=3600,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
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
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables created/verified")
    
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
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            
            if os.getenv("RENDER") and DATABASE_URL.startswith("sqlite"):
                try:
                    conn.execute(text("CREATE TABLE IF NOT EXISTS _test (id INTEGER)"))
                    conn.execute(text("DROP TABLE _test"))
                    logger.info("✅ Database is writable")
                except Exception as e:
                    logger.error(f"❌ Database write test failed: {e}")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False