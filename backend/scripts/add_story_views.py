# scripts/add_story_views.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_turso_client
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_story_views_table():
    if not settings.USE_TURSO:
        logger.info("Turso not enabled")
        return
    
    with get_turso_client() as client:
        # Create story_views table
        client.execute("""
            CREATE TABLE IF NOT EXISTS story_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id INTEGER NOT NULL,
                user_id INTEGER,
                session_id TEXT,
                viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """, [])
        logger.info("✅ Story views table created/verified")

if __name__ == "__main__":
    add_story_views_table()