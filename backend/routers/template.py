from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import random
from datetime import datetime, timedelta
import logging

from db.database import get_db, settings
from db import helpers
from core.auth import get_current_active_user, get_current_user_optional

router = APIRouter(prefix="/templates", tags=["templates"])
logger = logging.getLogger(__name__)

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

@router.get("/defaults")
def create_default_templates(
    current_user = Depends(get_current_active_user)
):
    if settings.USE_TURSO:
        if current_user.get("username") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        count = 0
        for template_data in DEFAULT_TEMPLATES:
            existing = helpers.get_template_by_title(template_data["title"])
            if not existing:
                helpers.create_template(template_data)
                count += 1
        
        return {"message": f"Created {count} default templates"}
    
    else:
        from sqlalchemy.orm import Session
        from models.template import Template
        
        db = next(get_db())
        
        if current_user.username != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        count = 0
        for template_data in DEFAULT_TEMPLATES:
            existing = db.query(Template).filter(Template.title == template_data["title"]).first()
            if not existing:
                template = Template(
                    title=template_data["title"],
                    description=template_data["description"],
                    genre=template_data["genre"],
                    content_structure=template_data["content_structure"],
                    prompt=template_data["prompt"],
                    is_premium=False
                )
                db.add(template)
                count += 1
        
        db.commit()
        return {"message": f"Created {count} default templates"}

@router.post("/", response_model=dict)
def create_template(
    template_data: dict,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Creating template by user {current_user.id}")
    
    if settings.USE_TURSO:
        template_data["created_by"] = current_user.id
        template = helpers.create_template(template_data)
        if not template:
            raise HTTPException(status_code=500, detail="Failed to create template")
        
        return template
    
    else:
        from sqlalchemy.orm import Session
        from models.template import Template
        
        db = next(get_db())
        
        db_template = Template(
            title=template_data["title"],
            description=template_data.get("description"),
            genre=template_data.get("genre"),
            content_structure=template_data["content_structure"],
            prompt=template_data.get("prompt"),
            cover_image=template_data.get("cover_image"),
            is_premium=template_data.get("is_premium", False),
            created_by=current_user.id
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        return {
            "id": db_template.id,
            "title": db_template.title,
            "description": db_template.description,
            "genre": db_template.genre,
            "content_structure": db_template.content_structure,
            "prompt": db_template.prompt,
            "cover_image": db_template.cover_image,
            "is_premium": db_template.is_premium,
            "usage_count": db_template.usage_count,
            "created_by": db_template.created_by,
            "created_at": db_template.created_at,
            "updated_at": db_template.updated_at,
            "creator_username": current_user.username,
            "is_favorite": False
        }

@router.get("/", response_model=dict)
def get_templates(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    genre: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: str = Query("popular", pattern="^(popular|newest|title)$"),
    current_user = Depends(get_current_user_optional)
):
    logger.info(f"Getting templates page {page}")
    
    if settings.USE_TURSO:
        offset = (page - 1) * per_page
        templates = helpers.get_templates(genre, search, sort, limit=per_page, offset=offset)
        
        total = len(templates)
        pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        template_responses = []
        for template in templates:
            template_responses.append(template)
        
        return {
            "templates": template_responses,
            "total": total,
            "page": page,
            "pages": pages
        }
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc, or_
        from models.template import Template, UserTemplate
        
        db = next(get_db())
        
        query = db.query(Template)
        
        if genre:
            query = query.filter(Template.genre == genre)
        
        if search:
            query = query.filter(
                or_(
                    Template.title.ilike(f"%{search}%"),
                    Template.description.ilike(f"%{search}%")
                )
            )
        
        if sort == "popular":
            query = query.order_by(desc(Template.usage_count))
        elif sort == "newest":
            query = query.order_by(desc(Template.created_at))
        else:
            query = query.order_by(Template.title)
        
        total = query.count()
        pages = (total + per_page - 1) // per_page
        templates = query.offset((page - 1) * per_page).limit(per_page).all()
        
        template_responses = []
        for template in templates:
            is_favorite = False
            if current_user:
                fav = db.query(UserTemplate).filter(
                    UserTemplate.user_id == current_user.id,
                    UserTemplate.template_id == template.id
                ).first()
                is_favorite = fav.is_favorite if fav else False
            
            template_responses.append({
                "id": template.id,
                "title": template.title,
                "description": template.description,
                "genre": template.genre,
                "content_structure": template.content_structure,
                "prompt": template.prompt,
                "cover_image": template.cover_image,
                "is_premium": template.is_premium,
                "usage_count": template.usage_count,
                "created_by": template.created_by,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "creator_username": template.creator.username if template.creator else None,
                "is_favorite": is_favorite
            })
        
        return {
            "templates": template_responses,
            "total": total,
            "page": page,
            "pages": pages
        }

@router.get("/{template_id}", response_model=dict)
def get_template(
    template_id: int,
    current_user = Depends(get_current_user_optional)
):
    logger.info(f"Getting template {template_id}")
    
    if settings.USE_TURSO:
        template = helpers.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return template
    
    else:
        from sqlalchemy.orm import Session
        from models.template import Template, UserTemplate
        
        db = next(get_db())
        
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        is_favorite = False
        if current_user:
            fav = db.query(UserTemplate).filter(
                UserTemplate.user_id == current_user.id,
                UserTemplate.template_id == template.id
            ).first()
            is_favorite = fav.is_favorite if fav else False
        
        return {
            "id": template.id,
            "title": template.title,
            "description": template.description,
            "genre": template.genre,
            "content_structure": template.content_structure,
            "prompt": template.prompt,
            "cover_image": template.cover_image,
            "is_premium": template.is_premium,
            "usage_count": template.usage_count,
            "created_by": template.created_by,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
            "creator_username": template.creator.username if template.creator else None,
            "is_favorite": is_favorite
        }

@router.post("/{template_id}/use", response_model=dict)
def use_template(
    template_id: int,
    request: dict = None,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Using template {template_id} by user {current_user.id}")
    
    custom_title = None
    if request and isinstance(request, dict):
        custom_title = request.get("custom_title")
    
    if settings.USE_TURSO:
        result = helpers.use_template(template_id, current_user.id, custom_title)
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return result
    
    else:
        from sqlalchemy.orm import Session
        from models.template import Template, UserTemplate
        from models.story import Story
        
        db = next(get_db())
        
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template.usage_count += 1
        
        title = custom_title if custom_title else f"Story using {template.title}"
        
        content = f"# {title}\n\n"
        content += f"*Based on the {template.title} template*\n\n"
        content += f"## Outline\n"
        for i, item in enumerate(template.content_structure.get("outline", []), 1):
            content += f"{i}. {item}\n"
        
        if template.content_structure.get("characters"):
            content += f"\n## Characters\n"
            for char in template.content_structure.get("characters", []):
                content += f"- **{char.get('role')}**: {char.get('description')}\n"
        
        if template.content_structure.get("settings"):
            content += f"\n## Settings\n"
            for setting in template.content_structure.get("settings", []):
                content += f"- {setting}\n"
        
        if template.content_structure.get("plot_points"):
            content += f"\n## Plot Points\n"
            for point in template.content_structure.get("plot_points", []):
                content += f"- {point}\n"
        
        content += f"\n## Your Story\n\n"
        if template.prompt:
            content += f"*Prompt: {template.prompt}*\n\n"
        content += "Start writing your story here...\n"
        
        story = Story(
            title=title,
            content=content,
            excerpt=f"A story created using the {template.title} template",
            user_id=current_user.id,
            is_published=False,
            story_type="written",
            genre=template.genre
        )
        db.add(story)
        db.commit()
        db.refresh(story)
        
        user_template = db.query(UserTemplate).filter(
            UserTemplate.user_id == current_user.id,
            UserTemplate.template_id == template.id
        ).first()
        
        if user_template:
            user_template.last_used = datetime.now()
        else:
            user_template = UserTemplate(
                user_id=current_user.id,
                template_id=template.id,
                last_used=datetime.now()
            )
            db.add(user_template)
        
        db.commit()
        
        return {
            "story_id": story.id,
            "title": title,
            "message": f"Story created using template '{template.title}'"
        }

@router.post("/{template_id}/favorite")
def toggle_favorite(
    template_id: int,
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Toggling favorite for template {template_id}")
    
    if settings.USE_TURSO:
        result = helpers.toggle_template_favorite(template_id, current_user.id)
        return result
    
    else:
        from sqlalchemy.orm import Session
        from models.template import Template, UserTemplate
        
        db = next(get_db())
        
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        user_template = db.query(UserTemplate).filter(
            UserTemplate.user_id == current_user.id,
            UserTemplate.template_id == template.id
        ).first()
        
        if user_template:
            user_template.is_favorite = not user_template.is_favorite
            message = "added to" if user_template.is_favorite else "removed from"
        else:
            user_template = UserTemplate(
                user_id=current_user.id,
                template_id=template.id,
                is_favorite=True
            )
            db.add(user_template)
            message = "added to"
        
        db.commit()
        
        return {"message": f"Template {message} favorites"}

@router.get("/prompts/daily", response_model=dict)
def get_daily_prompt(
    current_user = Depends(get_current_user_optional)
):
    logger.info(f"Getting daily prompt")
    
    if settings.USE_TURSO:
        prompts = [
            "Write a story about a character who finds a mysterious door that wasn't there yesterday.",
            "A letter arrives, addressed to you, but it's dated 100 years ago.",
            "You discover you can talk to animals, but only on Tuesdays.",
            "A stranger sits next to you and says, 'I've been looking for you for 500 years.'",
            "Your reflection in the mirror starts doing things differently.",
            "The last library on Earth contains books that write themselves.",
            "You find a photograph of yourself from 100 years in the future.",
            "A detective investigates a crime that hasn't happened yet.",
            "The moon has a message written on it that only appears once a year.",
            "You wake up with a new memory every day - memories of a life you never lived."
        ]
        
        random_index = random.randint(0, len(prompts) - 1)
        
        return {
            "id": random_index + 1,
            "prompt": prompts[random_index],
            "genre": "any",
            "difficulty": "medium",
            "created_at": datetime.now().isoformat()
        }
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import func
        from models.template import WritingPrompt
        
        db = next(get_db())
        
        today = datetime.now().date()
        
        prompt = db.query(WritingPrompt).filter(
            func.date(WritingPrompt.created_at) == today
        ).first()
        
        if not prompt:
            prompts = [
                "Write a story about a character who finds a mysterious door that wasn't there yesterday.",
                "A letter arrives, addressed to you, but it's dated 100 years ago.",
                "You discover you can talk to animals, but only on Tuesdays.",
                "A stranger sits next to you and says, 'I've been looking for you for 500 years.'",
                "Your reflection in the mirror starts doing things differently.",
                "The last library on Earth contains books that write themselves.",
                "You find a photograph of yourself from 100 years in the future.",
                "A detective investigates a crime that hasn't happened yet.",
                "The moon has a message written on it that only appears once a year.",
                "You wake up with a new memory every day - memories of a life you never lived."
            ]
            
            prompt = WritingPrompt(
                prompt=random.choice(prompts),
                genre="any",
                difficulty="medium",
                expires_at=datetime.now() + timedelta(days=1)
            )
            db.add(prompt)
            db.commit()
            db.refresh(prompt)
        
        return {
            "id": prompt.id,
            "prompt": prompt.prompt,
            "genre": prompt.genre,
            "difficulty": prompt.difficulty,
            "created_at": prompt.created_at
        }

@router.get("/favorites", response_model=List[dict])
def get_favorite_templates(
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting favorite templates for user {current_user.id}")
    
    if settings.USE_TURSO:
        favorites = helpers.get_favorite_templates(current_user.id)
        return favorites
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        from models.template import UserTemplate
        
        db = next(get_db())
        
        user_templates = db.query(UserTemplate).filter(
            UserTemplate.user_id == current_user.id,
            UserTemplate.is_favorite == True
        ).order_by(desc(UserTemplate.last_used)).all()
        
        result = []
        for ut in user_templates:
            template = ut.template
            result.append({
                "id": template.id,
                "title": template.title,
                "description": template.description,
                "genre": template.genre,
                "content_structure": template.content_structure,
                "prompt": template.prompt,
                "cover_image": template.cover_image,
                "is_premium": template.is_premium,
                "usage_count": template.usage_count,
                "created_by": template.created_by,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "creator_username": template.creator.username if template.creator else None,
                "is_favorite": True
            })
        
        return result
    
@router.get("/favorites", response_model=List[dict])
def get_favorite_templates(
    current_user = Depends(get_current_active_user)
):
    logger.info(f"Getting favorite templates for user {current_user.id}")
    
    if settings.USE_TURSO:
        try:
            favorites = helpers.get_favorite_templates(current_user.id)
            return favorites if favorites else []
        except Exception as e:
            logger.error(f"Error getting favorites: {e}")
            return []
    
    else:
        from sqlalchemy.orm import Session
        from sqlalchemy import desc
        from models.template import UserTemplate
        
        db = next(get_db())
        
        user_templates = db.query(UserTemplate).filter(
            UserTemplate.user_id == current_user.id,
            UserTemplate.is_favorite == True
        ).order_by(desc(UserTemplate.last_used)).all()
        
        result = []
        for ut in user_templates:
            template = ut.template
            result.append({
                "id": template.id,
                "title": template.title,
                "description": template.description,
                "genre": template.genre,
                "content_structure": template.content_structure,
                "prompt": template.prompt,
                "cover_image": template.cover_image,
                "is_premium": template.is_premium,
                "usage_count": template.usage_count,
                "created_by": template.created_by,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "creator_username": template.creator.username if template.creator else None,
                "is_favorite": True
            })
        
        return result