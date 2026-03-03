import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models.template import Template

DEFAULT_TEMPLATES = [
    {
        "title": "Hero's Journey Fantasy",
        "description": "Classic fantasy adventure with a reluctant hero",
        "genre": "fantasy",
        "content_structure": {
            "outline": [
                "The Ordinary World - Introduce hero in normal life",
                "The Call to Adventure - Something disrupts the ordinary",
                "Refusal of the Call - Hero hesitates",
                "Meeting the Mentor - Wise figure appears",
                "Crossing the Threshold - Enter the special world",
                "Tests, Allies, Enemies - Challenges and new friends",
                "Approach to the Inmost Cave - Preparing for big challenge",
                "The Ordeal - Major crisis/almost death",
                "The Reward - Claim victory/treasure",
                "The Road Back - Return to ordinary world",
                "The Resurrection - Final test/challenge",
                "Return with Elixir - Hero returns transformed"
            ],
            "characters": [
                {"role": "Hero", "description": "The protagonist on a journey"},
                {"role": "Mentor", "description": "Wise guide who helps the hero"},
                {"role": "Shadow", "description": "The antagonist/villain"},
                {"role": "Allies", "description": "Friends who join the quest"}
            ],
            "settings": ["Village", "Forest", "Castle", "Mountain", "Cave"],
            "plot_points": [
                "Discovery of ancient prophecy",
                "Loss of a loved one",
                "Betrayal by trusted ally",
                "Final confrontation with evil"
            ]
        },
        "prompt": "A young farmhand discovers they are the last of an ancient lineage and must embark on a quest to save their kingdom from darkness.",
        "is_premium": False
    },
    {
        "title": "Sci-Fi Mystery",
        "description": "Futuristic mystery with twists and turns",
        "genre": "sci-fi",
        "content_structure": {
            "outline": [
                "The Discovery - Find something strange",
                "The Investigation - Start asking questions",
                "Red Herrings - False leads",
                "Danger - Someone wants to stop you",
                "The Reveal - Discover the truth",
                "Confrontation - Face the mastermind",
                "Resolution - Wrap up loose ends"
            ],
            "characters": [
                {"role": "Detective", "description": "The investigator"},
                {"role": "Sidekick", "description": "Assistant/partner"},
                {"role": "Victim", "description": "Person in trouble"},
                {"role": "Villain", "description": "Mastermind behind it all"}
            ],
            "settings": ["Space Station", "Colony", "Laboratory", "City"],
            "plot_points": [
                "Murder in a sealed room",
                "Missing scientist",
                "Conspiracy cover-up",
                "AI gone rogue"
            ]
        },
        "prompt": "On a distant space station, a scientist is found dead in a locked room. The only clue is a cryptic message left in the ship's computer.",
        "is_premium": False
    },
    {
        "title": "Romantic Comedy",
        "description": "Light-hearted romance with humor",
        "genre": "romance",
        "content_structure": {
            "outline": [
                "Meet Cute - Unusual first meeting",
                "The Attraction - They're drawn together",
                "The Complication - Something gets in the way",
                "Growing Closer - They spend time together",
                "The Misunderstanding - Fight/separation",
                "Grand Gesture - One tries to win back",
                "Happy Ending - They get together"
            ],
            "characters": [
                {"role": "Protagonist", "description": "Main character"},
                {"role": "Love Interest", "description": "The one they fall for"},
                {"role": "Best Friend", "description": "Comic relief/advisor"},
                {"role": "Rival", "description": "Competition for love"}
            ],
            "settings": ["Coffee Shop", "Office", "City", "Wedding"],
            "plot_points": [
                "Mistaken identity",
                "Fake relationship",
                "Enemies to lovers",
                "Second chance romance"
            ]
        },
        "prompt": "Two rival coffee shop owners in a small town compete for 'Best Coffee' while secretly falling for each other.",
        "is_premium": False
    },
    {
        "title": "Gothic Horror",
        "description": "Dark, atmospheric horror story",
        "genre": "horror",
        "content_structure": {
            "outline": [
                "Arrival - Main character arrives at strange place",
                "Strange Occurrences - Weird things happen",
                "Investigation - Looking for answers",
                "Discovery - Find dark secret",
                "Confrontation - Face the horror",
                "Escape - Try to get away",
                "Aftermath - Changed forever"
            ],
            "characters": [
                {"role": "Protagonist", "description": "The one who uncovers horror"},
                {"role": "Mysterious Stranger", "description": "Knows the truth"},
                {"role": "Innocent", "description": "Victim to be saved"},
                {"role": "Monster", "description": "Source of horror"}
            ],
            "settings": ["Mansion", "Castle", "Village", "Forest"],
            "plot_points": [
                "Family curse",
                "Haunted house",
                "Ancient evil awakened",
                "Supernatural entity"
            ]
        },
        "prompt": "A young woman inherits a remote mansion and discovers it's haunted by the ghost of a relative with unfinished business.",
        "is_premium": False
    }
]

def init_templates():
    db = SessionLocal()
    try:
        count = 0
        for template_data in DEFAULT_TEMPLATES:
            existing = db.query(Template).filter(Template.title == template_data["title"]).first()
            if not existing:
                template = Template(**template_data)
                db.add(template)
                count += 1
        
        db.commit()
        print(f"Created {count} default templates")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_templates()