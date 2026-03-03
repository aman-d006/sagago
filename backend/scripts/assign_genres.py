import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models.story import Story

GENRES = ["Fantasy", "Sci-Fi", "Mystery", "Romance", "Horror", "Adventure", "Thriller", "Drama", "Comedy"]

def assign_genres():
    db = SessionLocal()
    try:
        stories = db.query(Story).filter(Story.is_published == True).all()
        
        if not stories:
            print("No published stories found")
            return
        
        print(f"Found {len(stories)} published stories")
        
        # First, check which stories already have genres
        stories_with_genre = db.query(Story).filter(Story.genre.isnot(None)).count()
        print(f"Stories that already have genres: {stories_with_genre}")
        
        assigned_count = 0
        for story in stories:
            if not story.genre:
                story.genre = random.choice(GENRES)
                assigned_count += 1
                print(f"Assigned genre '{story.genre}' to story ID {story.id}: {story.title}")
        
        if assigned_count > 0:
            db.commit()
            print(f"\nGenre assignment completed! Assigned genres to {assigned_count} stories.")
        else:
            print("\nAll stories already have genres assigned.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    assign_genres()