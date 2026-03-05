# db/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
from urllib.parse import quote
import json

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
        logger.info("🔧 Creating Turso client...")
        _turso_client = TursoClient(
            settings.TURSO_DATABASE_URL,
            settings.TURSO_AUTH_TOKEN
        )
        # Test connection immediately
        try:
            test = _turso_client.query("SELECT 1")
            logger.info(f"✅ Turso client created and tested: {test}")
        except Exception as e:
            logger.error(f"❌ Turso client test failed: {e}")
            _turso_client = None
    return _turso_client

def test_turso_connection():
    """Test Turso connection using our direct client"""
    try:
        client = get_turso_client()
        if client:
            result = client.query("SELECT 1")
            logger.info(f"✅ Turso connection test result: {result}")
            return True
    except Exception as e:
        logger.error(f"❌ Turso connection test failed: {e}")
        return False
    return False

def create_turso_tables():
    """Create all required tables in Turso"""
    if not settings.USE_TURSO:
        return
    
    try:
        client = get_turso_client()
        if not client:
            logger.error("❌ Cannot create Turso tables: No client")
            return
        
        logger.info("📊 Creating tables in Turso...")
        
        # Check existing tables first
        existing = client.query("SELECT name FROM sqlite_master WHERE type='table'")
        logger.info(f"Existing tables in Turso: {existing}")
        
        # Create users table
        client.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                bio TEXT,
                avatar_url TEXT,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_superuser BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """)
        logger.info("✅ Users table created/verified in Turso")
        
        # Create stories table
        client.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                excerpt TEXT,
                cover_image TEXT,
                user_id INTEGER NOT NULL,
                story_type TEXT DEFAULT 'written',
                genre TEXT,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                is_published BOOLEAN DEFAULT 0,
                is_premium BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Stories table created/verified in Turso")
        
        # Create story_nodes table (for interactive stories)
        client.execute("""
            CREATE TABLE IF NOT EXISTS story_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                is_root BOOLEAN DEFAULT 0,
                is_ending BOOLEAN DEFAULT 0,
                is_winning_ending BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Story nodes table created/verified in Turso")
        
        # Create story_options table (choices in interactive stories)
        client.execute("""
            CREATE TABLE IF NOT EXISTS story_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                next_node_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (node_id) REFERENCES story_nodes(id) ON DELETE CASCADE,
                FOREIGN KEY (next_node_id) REFERENCES story_nodes(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Story options table created/verified in Turso")
        
        # Create templates table
        client.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                genre TEXT,
                content_structure TEXT,
                prompt TEXT,
                cover_image TEXT,
                is_premium BOOLEAN DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        logger.info("✅ Templates table created/verified in Turso")
        
        # Create comments table
        client.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                story_id INTEGER NOT NULL,
                parent_id INTEGER,
                like_count INTEGER DEFAULT 0,
                is_edited BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Comments table created/verified in Turso")
        
        # Create likes table
        client.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                story_id INTEGER,
                comment_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, story_id),
                UNIQUE(user_id, comment_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
                FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Likes table created/verified in Turso")
        
        # Create follows table
        client.execute("""
            CREATE TABLE IF NOT EXISTS follows (
                follower_id INTEGER NOT NULL,
                followed_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (follower_id, followed_id),
                FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (followed_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Follows table created/verified in Turso")
        
        # Create messages table
        client.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Messages table created/verified in Turso")
        
        # Create notifications table
        client.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                related_id INTEGER,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Notifications table created/verified in Turso")
        
        # Create bookmarks table
        client.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                story_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, story_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
            )
        """)
        logger.info("✅ Bookmarks table created/verified in Turso")
        
        # Verify all tables were created
        final_tables = client.query("SELECT name FROM sqlite_master WHERE type='table'")
        logger.info(f"✅ All Turso tables: {final_tables}")
        
    except Exception as e:
        logger.error(f"❌ Failed to create Turso tables: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def get_database_url():
    # Use Turso via our direct client, not SQLAlchemy
    if settings.USE_TURSO:
        logger.info("📁 Using Turso distributed database (direct client)")
        # Return SQLite URL as fallback for SQLAlchemy parts that don't use Turso
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
    
    # Create tables in SQLite (for fallback/local)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ SQLite tables created/verified")
    except Exception as e:
        logger.error(f"❌ Failed to create SQLite tables: {e}")
    
    # Create tables in Turso
    if settings.USE_TURSO:
        create_turso_tables()
    
    # SQLite-specific migrations
    if DATABASE_URL.startswith("sqlite") and not settings.USE_TURSO:
        try:
            with engine.begin() as conn:
                # Check for story_jobs table
                result = conn.execute(text("PRAGMA table_info('story_jobs')"))
                cols = [row[1] for row in result.fetchall()]
                if 'completed_at' not in cols:
                    conn.execute(text("ALTER TABLE story_jobs ADD COLUMN completed_at DATETIME"))
                    logger.info("✅ Added completed_at column to story_jobs")
                
                # Check for users table
                result = conn.execute(text("PRAGMA table_info('users')"))
                cols = [row[1] for row in result.fetchall()]
                if 'avatar_url' not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR"))
                    logger.info("✅ Added avatar_url column to users")
                    
        except Exception as e:
            logger.error(f"⚠️ Migration error (non-critical): {e}")

def check_database():
    try:
        # Check SQLite connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("✅ SQLite connection successful")
        
        # Test Turso if enabled
        if settings.USE_TURSO:
            if test_turso_connection():
                logger.info("✅ Turso connection successful")
                
                # Verify tables exist in Turso
                client = get_turso_client()
                if client:
                    tables = client.query("SELECT name FROM sqlite_master WHERE type='table'")
                    table_names = [t[0] for t in tables if t]
                    logger.info(f"📊 Turso tables: {table_names}")
                    
                    # Check if users table exists
                    if 'users' not in table_names:
                        logger.warning("⚠️ Users table missing in Turso, creating tables...")
                        create_turso_tables()
            else:
                logger.error("❌ Turso connection failed")
                return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")
        return False

def get_database_stats():
    """Get database statistics for monitoring"""
    if not settings.USE_TURSO:
        return {"turso_enabled": False}
    
    stats = {
        "turso_enabled": True,
        "tables": {}
    }
    
    try:
        client = get_turso_client()
        if client:
            # Get all tables
            tables = client.query("SELECT name FROM sqlite_master WHERE type='table'")
            for table in tables:
                if table and table[0]:
                    count = client.query_value(f"SELECT COUNT(*) FROM {table[0]}")
                    stats["tables"][table[0]] = count
            
            # Get database size
            size = client.query_value("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
            stats["database_size_bytes"] = size
    except Exception as e:
        stats["error"] = str(e)
    
    return stats

if settings.USE_TURSO:
    # Initialize client and check database on import
    check_database()