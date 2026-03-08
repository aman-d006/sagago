# scripts/add_story_options.py
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

def add_story_options_table():
    if not settings.USE_TURSO:
        logger.info("Turso not enabled")
        return
    
    with get_turso_client() as client:
        # Create story_options table
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
        """, [])
        logger.info("✅ Story options table created/verified")

if __name__ == "__main__":
    add_story_options_table()