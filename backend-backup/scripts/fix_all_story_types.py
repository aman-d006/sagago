import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models.story import Story, StoryNode

def fix_all_story_types():
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
            
            if has_nodes:
                if story.story_type != 'interactive':
                    print(f"Fixing story ID {story.id}: '{story.title}' - had type '{story.story_type}', setting to 'interactive'")
                    story.story_type = 'interactive'
                    fixed_count += 1
                interactive_count += 1
            else:
                if story.story_type != 'written':
                    print(f"Fixing story ID {story.id}: '{story.title}' - had type '{story.story_type}', setting to 'written'")
                    story.story_type = 'written'
                    fixed_count += 1
                written_count += 1
        
        db.commit()
        
        print(f"\nSummary:")
        print(f"Total stories: {len(stories)}")
        print(f"Interactive stories: {interactive_count}")
        print(f"Written stories: {written_count}")
        print(f"Fixed stories: {fixed_count}")
        
        # Verify the fixes
        print("\nVerifying fixes:")
        for story in stories[:5]:  # Check first 5 stories
            has_nodes = db.query(StoryNode).filter(StoryNode.story_id == story.id).count() > 0
            print(f"Story {story.id}: '{story.title}' - type: {story.story_type}, has_nodes: {has_nodes}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_story_types()