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

def fix_jobs_table():
    """Create jobs table if it doesn't exist"""
    if not settings.USE_TURSO:
        logger.info("Turso not enabled")
        return
    
    with get_turso_client() as client:
        # Check if jobs table exists
        tables = client.query("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'", [])
        if tables and len(tables) > 0:
            logger.info("Jobs table already exists")
        else:
            logger.info("Creating jobs table...")
            client.execute("""
                CREATE TABLE jobs (
                    job_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    theme TEXT,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME
                )
            """, [])
            logger.info("✅ Jobs table created")
        
        # Verify table was created
        verify = client.query("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'", [])
        if verify:
            logger.info("✅ Jobs table verified")
        else:
            logger.error("❌ Failed to create jobs table")

if __name__ == "__main__":
    fix_jobs_table()