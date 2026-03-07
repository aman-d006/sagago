import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_turso_client
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_value(cell):
    if cell is None:
        return None
    if isinstance(cell, dict):
        return cell.get('value')
    return cell

def fix_all_tables():
    if not settings.USE_TURSO:
        logger.info("Turso not enabled")
        return
    
    with get_turso_client() as client:
        # Create jobs table
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
        """, [])
        logger.info("✅ Jobs table created/verified")
        
        # Create comment_likes table
        client.execute("""
            CREATE TABLE IF NOT EXISTS comment_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                comment_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, comment_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE
            )
        """, [])
        logger.info("✅ Comment_likes table created/verified")
        
        # Check follows table
        try:
            follows_cols = client.query("PRAGMA table_info(follows)", [])
            col_names = [get_value(col[1]) for col in follows_cols] if follows_cols else []
            if 'is_active' not in col_names:
                logger.info("Adding is_active column to follows table...")
                client.execute("ALTER TABLE follows ADD COLUMN is_active BOOLEAN DEFAULT 1", [])
                logger.info("✅ Added is_active column to follows")
        except Exception as e:
            logger.warning(f"Could not modify follows table: {e}")
        
        # List all tables
        tables = client.query("SELECT name FROM sqlite_master WHERE type='table'", [])
        table_list = [get_value(row[0]) for row in tables] if tables else []
        logger.info(f"All tables in database: {table_list}")
        
        logger.info("Database fix complete!")

if __name__ == "__main__":
    fix_all_tables()