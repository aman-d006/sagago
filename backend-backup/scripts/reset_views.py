import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models.analytics import StoryView

def reset_duplicate_views():
    db = SessionLocal()
    try:
        all_views = db.query(StoryView).all()
        unique_pairs = set()
        to_delete = []
        
        for view in all_views:
            key = (view.story_id, view.user_id) if view.user_id else (view.story_id, view.session_id)
            if key in unique_pairs:
                to_delete.append(view)
            else:
                unique_pairs.add(key)
        
        for view in to_delete:
            db.delete(view)
        
        db.commit()
        print(f"Removed {len(to_delete)} duplicate views")
        print(f"Remaining unique views: {len(all_views) - len(to_delete)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_duplicate_views()