# scripts/fix_images.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_turso_client
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_images():
    if not settings.USE_TURSO:
        logger.info("Turso not enabled")
        return
    
    with get_turso_client() as client:
        # Create images table
        client.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                url_path TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                user_id INTEGER,
                story_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
            )
        """, [])
        logger.info("✅ Images table created/verified")

if __name__ == "__main__":
    fix_images()