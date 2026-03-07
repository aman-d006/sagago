import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_turso_client
from core.config import settings

def backup_data():
    if not settings.USE_TURSO:
        return
    
    backup = {}
    tables = ['users', 'stories', 'comments', 'likes', 'follows', 'messages', 'notifications', 'bookmarks', 'templates']
    
    with get_turso_client() as client:
        for table in tables:
            rows = client.query(f"SELECT * FROM {table}", [])
            backup[table] = rows
    
    filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(backup, f, default=str)
    print(f"✅ Backup saved to {filename}")

if __name__ == "__main__":
    backup_data()