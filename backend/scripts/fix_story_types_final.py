import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models.story import Story, StoryNode

def fix_story_types():
    db = SessionLocal()
    try:
        stories = db.query(Story).all()
        
        print(f"Found {len(stories)} total stories")
        
        interactive_count = 0
        written_count = 0
        fixed_count = 0
        
        for story in stories:
            has_nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).count() > 0
            original_type = story.story_type
            
            if has_nodes and story.story_type != 'interactive':
                print(f"Fixing story ID {story.id}: '{story.title}' - had type '{story.story_type}', setting to 'interactive' (has {db.query(StoryNode).filter(StoryNode.story_id == story.id).count()} nodes)")
                story.story_type = 'interactive'
                fixed_count += 1
                interactive_count += 1
            elif not has_nodes and story.story_type != 'written':
                print(f"Fixing story ID {story.id}: '{story.title}' - had type '{story.story_type}', setting to 'written' (no nodes)")
                story.story_type = 'written'
                fixed_count += 1
                written_count += 1
            elif has_nodes:
                interactive_count += 1
                print(f"Story ID {story.id}: '{story.title}' - already interactive with {db.query(StoryNode).filter(StoryNode.story_id == story.id).count()} nodes")
            else:
                written_count += 1
                print(f"Story ID {story.id}: '{story.title}' - already written")
        
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