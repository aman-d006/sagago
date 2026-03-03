from sqlalchemy import create_engine, text
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.config import settings

def add_genre_column():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info('stories')"))
        columns = [row[1] for row in result.fetchall()]
        
        print("Current columns in stories table:", columns)
        
        if 'genre' not in columns:
            print("Adding genre column to stories table...")
            conn.execute(text("ALTER TABLE stories ADD COLUMN genre VARCHAR"))
            conn.commit()
            print("Genre column added successfully!")
        else:
            print("Genre column already exists.")

if __name__ == "__main__":
    add_genre_column()