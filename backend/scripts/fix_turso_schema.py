import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_turso_client
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_schema():
    """Fix Turso table schemas"""
    if not settings.USE_TURSO:
        logger.info("Turso not enabled")
        return
    
    with get_turso_client() as client:
        
        users_cols = client.query("PRAGMA table_info(users)")
        col_names = [col[1]['value'] if isinstance(col[1], dict) else col[1] for col in users_cols]
        
        if 'is_active' not in col_names:
            logger.info("Adding is_active column to users table...")
            client.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
            logger.info("✅ Added is_active column")
        
        follows_cols = client.query("PRAGMA table_info(follows)")
        col_names = [col[1]['value'] if isinstance(col[1], dict) else col[1] for col in follows_cols]
        
        if 'is_active' not in col_names:
            logger.info("Adding is_active column to follows table...")
            client.execute("ALTER TABLE follows ADD COLUMN is_active BOOLEAN DEFAULT 1")
            logger.info("✅ Added is_active column")
        
        logger.info("Schema fix complete!")

if __name__ == "__main__":
    fix_schema()