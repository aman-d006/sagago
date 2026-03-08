from xmlrpc import client

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from db.turso_client import TursoClient

logger = logging.getLogger(__name__)

_turso_client = None

def get_turso_client():
    global _turso_client
    if _turso_client is None and settings.USE_TURSO:
        _turso_client = TursoClient(
            settings.TURSO_DATABASE_URL,
            settings.TURSO_AUTH_TOKEN
        )
    return _turso_client

def create_turso_tables():
    if not settings.USE_TURSO:
        return
    try:
        client = get_turso_client()
        if not client:
            return
        
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
        
        client.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                session_id TEXT,
                theme TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        """)
        logger.info("✅ Jobs table created/verified in Turso")

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
        
        client.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                session_id TEXT,
                theme TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        """)
        logger.info("✅ Jobs table created/verified in Turso")

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
        
    except Exception as e:
        logger.error(f"Failed to create Turso tables: {e}")

def get_database_url():
    if settings.USE_TURSO:
        return "sqlite:///./turso_fallback.db"
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    return "sqlite:///./sagago.db"

DATABASE_URL = get_database_url()

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Failed to create SQLite tables: {e}")
    
    if settings.USE_TURSO:
        create_turso_tables()

if settings.USE_TURSO:
    create_tables()