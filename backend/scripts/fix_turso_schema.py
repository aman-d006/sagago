import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_turso_client
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_schema():
    if not settings.USE_TURSO:
        logger.info("Turso not enabled")
        return
    
    with get_turso_client() as client:
        # Check follows table for is_active column
        follows_cols = client.query("PRAGMA table_info(follows)", [])
        col_names = [get_value(col[1]) for col in follows_cols] if follows_cols else []
        if 'is_active' not in col_names:
            logger.info("Adding is_active column to follows table...")
            try:
                client.execute("ALTER TABLE follows ADD COLUMN is_active BOOLEAN DEFAULT 1", [])
                logger.info("✅ Added is_active column to follows")
            except Exception as e:
                logger.error(f"Failed to add column: {e}")
        
        # Check notifications table
        notif_cols = client.query("PRAGMA table_info(notifications)", [])
        col_names = [get_value(col[1]) for col in notif_cols] if notif_cols else []
        required = ['id', 'user_id', 'type', 'content', 'related_id', 'is_read', 'created_at']
        for col in required:
            if col not in col_names:
                logger.warning(f"Missing column in notifications: {col}")
        
        # Check comment_likes table
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
        logger.info("✅ Verified comment_likes table")
        
        logger.info("Schema fix complete!")

def get_value(cell):
    if cell is None:
        return None
    if isinstance(cell, dict):
        return cell.get('value')
    return cell

if __name__ == "__main__":
    fix_schema()