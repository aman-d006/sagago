import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models.story import Story

def fix_story_types():
    db = SessionLocal()
    try:
        stories = db.query(Story).all()
        
        print(f"Found {len(stories)} total stories")
        
        interactive_count = 0
        written_count = 0
        fixed_count = 0
        
        for story in stories:
            has_nodes = len(story.nodes) > 0 if hasattr(story, 'nodes') else False
            
            if has_nodes and story.story_type != 'interactive':
                print(f"Fixing story ID {story.id}: '{story.title}' - had type '{story.story_type}', setting to 'interactive'")
                story.story_type = 'interactive'
                fixed_count += 1
                interactive_count += 1
            elif not has_nodes and story.story_type != 'written':
                print(f"Fixing story ID {story.id}: '{story.title}' - had type '{story.story_type}', setting to 'written'")
                story.story_type = 'written'
                fixed_count += 1
                written_count += 1
            elif has_nodes:
                interactive_count += 1
            else:
                written_count += 1
        
        db.commit()
        
        print(f"\nSummary:")
        print(f"Total stories: {len(stories)}")
        print(f"Interactive stories: {interactive_count}")
        print(f"Written stories: {written_count}")
        print(f"Fixed stories: {fixed_count}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_story_types()