from sqlalchemy.orm import Session
from core.config import settings
from core.groq_client import GroqLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.prompts import INTERACTIVE_STORY_PROMPT, FULL_STORY_PROMPT, ASSISTED_STORY_PROMPT
from models.story import Story, StoryNode, StoryOption
import json
import logging
import traceback
import re
import random
import uuid
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoryGenerator:
    TARGET_NODES = 40
    MAX_DEPTH = 10
    
    @classmethod
    def _get_llm(cls): 
        return GroqLLM(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
    
    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        llm = cls._get_llm()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", INTERACTIVE_STORY_PROMPT),
            ("human", "Theme: {theme}")
        ])
        
        formatted_prompt = prompt.invoke({"theme": theme})
        
        try:
            logger.info(f"Generating epic story with theme: {theme}")
            raw_response = llm.invoke(formatted_prompt)
            
            response_text = raw_response
            if hasattr(raw_response, "content"):
                response_text = raw_response.content
            
            logger.info("Raw response received, attempting to parse")
            
            json_str = cls._extract_json(response_text)
            
            if not json_str:
                logger.error("No JSON found in response - Groq returned invalid format")
                return cls._retry_with_varied_prompt(db, session_id, theme, "more depth and branching")
            
            try:
                story_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                fixed_json = cls._fix_json(json_str)
                try:
                    story_data = json.loads(fixed_json)
                    logger.info("Successfully fixed JSON")
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to fix JSON: {e2}")
                    return cls._retry_with_varied_prompt(db, session_id, theme, "valid JSON format")
            
            if not story_data or "title" not in story_data or "nodes" not in story_data:
                logger.warning("Missing required fields, retrying")
                return cls._retry_with_varied_prompt(db, session_id, theme, "complete story structure")
            
            story_db = Story(
                title=story_data["title"],
                content=story_data.get("premise", ""),
                excerpt=story_data.get("premise", "")[:150] + "...",
                session_id=session_id,
                is_published=False,
                story_type="interactive"
            )
            db.add(story_db)
            db.flush()
            
            node_count = 0
            if story_data.get("nodes"):
                nodes = story_data.get("nodes", [])
                for node_data in nodes:
                    node = StoryNode(
                        story_id=story_db.id,
                        content=node_data.get("content", ""),
                        is_root=node_data.get("is_root", False),
                        is_ending=node_data.get("is_ending", False),
                        is_winning_ending=node_data.get("is_winning_ending", False)
                    )
                    db.add(node)
                    db.flush()
                    node_count += 1
                    
                    for option_data in node_data.get("options", []):
                        option = StoryOption(
                            node_id=node.id,
                            next_node_id=option_data.get("next_node_id"),
                            text=option_data.get("text", "")
                        )
                        db.add(option)
            
            db.commit()
            
            logger.info(f"Epic story created: {story_db.id} with {node_count} nodes")
            return story_db
            
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            logger.error(traceback.format_exc())
            return cls._retry_with_varied_prompt(db, session_id, theme, "any valid format")
    
    @classmethod
    def _retry_with_varied_prompt(cls, db: Session, session_id: str, theme: str, focus: str) -> Story:
        logger.info(f"Retrying with varied prompt for theme: {theme}, focus: {focus}")
        
        varied_prompt = f"""
        Create an interactive story about {theme} with multiple branching paths and endings.
        Focus on {focus}.
        
        Return ONLY a JSON object with this structure:
        {{
          "title": "Story Title",
          "premise": "Brief story setup",
          "nodes": [
            {{
              "id": 1,
              "content": "Opening scene...",
              "is_root": true,
              "is_ending": false,
              "is_winning_ending": false,
              "options": [
                {{
                  "next_node_id": 2,
                  "text": "Choice A"
                }}
              ]
            }},
            {{
              "id": 2,
              "content": "Result...",
              "is_root": false,
              "is_ending": true,
              "is_winning_ending": true,
              "options": []
            }}
          ]
        }}
        
        The story should have at least 3-4 levels of depth with multiple endings.
        """
        
        llm = cls._get_llm()
        response = llm.invoke(varied_prompt)
        response_text = response.content if hasattr(response, "content") else response
        
        json_str = cls._extract_json(response_text)
        if json_str:
            try:
                story_data = json.loads(json_str)
                if story_data and "title" in story_data and "nodes" in story_data:
                    story_db = Story(
                        title=story_data["title"],
                        content=story_data.get("premise", ""),
                        excerpt=story_data.get("premise", "")[:150] + "...",
                        session_id=session_id,
                        is_published=False,
                        story_type="interactive"
                    )
                    db.add(story_db)
                    db.flush()
                    
                    node_count = 0
                    for node_data in story_data.get("nodes", []):
                        node = StoryNode(
                            story_id=story_db.id,
                            content=node_data.get("content", ""),
                            is_root=node_data.get("is_root", False),
                            is_ending=node_data.get("is_ending", False),
                            is_winning_ending=node_data.get("is_winning_ending", False)
                        )
                        db.add(node)
                        db.flush()
                        node_count += 1
                        
                        for option_data in node_data.get("options", []):
                            option = StoryOption(
                                node_id=node.id,
                                next_node_id=option_data.get("next_node_id"),
                                text=option_data.get("text", "")
                            )
                            db.add(option)
                    
                    db.commit()
                    logger.info(f"Varied prompt retry successful: {story_db.id} with {node_count} nodes")
                    return story_db
            except Exception as e:
                logger.error(f"Failed to parse varied prompt response: {e}")
        
        logger.warning("All Groq attempts failed, using enhanced fallback")
        return cls._create_enhanced_fallback_story(db, session_id, theme)
    
    @classmethod
    def _create_enhanced_fallback_story(cls, db: Session, session_id: str, theme: str) -> Story:
        logger.info(f"Creating enhanced fallback story for theme: {theme}")
        
        theme_lower = theme.lower()
        paths = []
        
        if "fantasy" in theme_lower or "magic" in theme_lower or "dragon" in theme_lower:
            paths = [
                {"name": "The Ancient Forest", "desc": f"You venture into an ancient forest where magic flows through every leaf and stream. Mystical creatures watch from the shadows as you pass."},
                {"name": "The Crystal Caves", "desc": f"Deep beneath the mountains, you discover caves filled with glowing crystals that pulse with magical energy."},
                {"name": "The Dragon's Peak", "desc": f"You climb the tallest mountain, where legends say an ancient dragon guards a powerful artifact."},
                {"name": "The Enchanted Lake", "desc": f"A serene lake reflects the stars, and you hear whispers of a water spirit who grants wishes to the worthy."}
            ]
        elif "sci-fi" in theme_lower or "space" in theme_lower or "cyberpunk" in theme_lower:
            paths = [
                {"name": "The Neon District", "desc": f"You enter a bustling district filled with neon lights, cybernetically enhanced citizens, and shadowy corporate agents."},
                {"name": "The Space Station", "desc": f"Aboard a massive space station, you navigate through zero-gravity corridors and encounter alien species from across the galaxy."},
                {"name": "The Virtual Reality", "desc": f"You plug into a hyper-realistic virtual world where the lines between reality and simulation begin to blur."},
                {"name": "The Underground Lab", "desc": f"Deep beneath the city, you discover a secret laboratory conducting experiments that could change humanity forever."}
            ]
        elif "mystery" in theme_lower or "detective" in theme_lower or "noir" in theme_lower:
            paths = [
                {"name": "The Crime Scene", "desc": f"You arrive at a crime scene where every detail seems to contradict the others. The clock is ticking."},
                {"name": "The Suspect's Home", "desc": f"You search the suspect's apartment, finding clues that either incriminate or exonerate them."},
                {"name": "The Hidden Files", "desc": f"Breaking into a secure database, you discover encrypted files that hold the key to the mystery."},
                {"name": "The Final Confrontation", "desc": f"You corner the culprit in an abandoned warehouse, but they have one last trick up their sleeve."}
            ]
        else:
            paths = [
                {"name": "The Winding Path", "desc": f"You follow a winding path through the {theme} landscape, unsure where it leads."},
                {"name": "The Ancient Ruins", "desc": f"You discover ancient ruins that hold secrets about the history of {theme}."},
                {"name": "The Hidden Village", "desc": f"A small village appears nestled in the landscape, its inhabitants wary of strangers."},
                {"name": "The Mysterious Tower", "desc": f"A towering structure looms in the distance, beckoning you to explore its depths."}
            ]
        
        return cls._build_story_from_paths(db, session_id, theme, paths)
    
    @classmethod
    def _build_story_from_paths(cls, db: Session, session_id: str, theme: str, paths: List[dict]) -> Story:
        story_db = Story(
            title=f"The Legend of {theme.title()}",
            content=f"An epic adventure through the realm of {theme}...",
            excerpt=f"An epic adventure through the realm of {theme}...",
            session_id=session_id,
            is_published=False,
            story_type="interactive"
        )
        db.add(story_db)
        db.flush()
        
        nodes = []
        
        root = StoryNode(
            story_id=story_db.id,
            content=f"You stand at the threshold of the {theme} realm. Multiple paths stretch before you, each promising different adventures.",
            is_root=True,
            is_ending=False,
            is_winning_ending=False
        )
        db.add(root)
        db.flush()
        nodes.append(root)
        
        path_nodes = []
        for path in paths:
            node = StoryNode(
                story_id=story_db.id,
                content=path["desc"],
                is_root=False,
                is_ending=False,
                is_winning_ending=False
            )
            db.add(node)
            db.flush()
            path_nodes.append(node)
            nodes.append(node)
        
        for i, path_node in enumerate(path_nodes):
            num_endings = random.randint(2, 3)
            endings = []
            
            for j in range(num_endings):
                is_winning = (j == 0)
                
                if is_winning:
                    content = f"You have triumphed! Your journey through the {theme} realm ends in glory. The legends will remember your name forever."
                else:
                    content = f"Your journey reaches an end, though not as you hoped. The lessons learned in the {theme} realm will stay with you."
                
                ending = StoryNode(
                    story_id=story_db.id,
                    content=content,
                    is_root=False,
                    is_ending=True,
                    is_winning_ending=is_winning
                )
                db.add(ending)
                db.flush()
                nodes.append(ending)
                
                option = StoryOption(
                    node_id=path_node.id,
                    next_node_id=ending.id,
                    text=f"Path {j+1}: {'Victory' if is_winning else 'Reflection'}"
                )
                db.add(option)
        
        for i, path_node in enumerate(path_nodes):
            option = StoryOption(
                node_id=root.id,
                next_node_id=path_node.id,
                text=paths[i]["name"]
            )
            db.add(option)
        
        db.commit()
        
        logger.info(f"Story created with ID: {story_db.id}, {len(nodes)} nodes")
        return story_db
    
    @classmethod
    def generate_full_story(cls, db: Session, session_id: str, theme: str) -> Story:
        llm = cls._get_llm()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", FULL_STORY_PROMPT),
            ("human", "Theme: {theme}")
        ])
        
        formatted_prompt = prompt.invoke({"theme": theme})
        
        try:
            logger.info(f"Generating epic full story with theme: {theme}")
            raw_response = llm.invoke(formatted_prompt)
            
            story_text = raw_response
            if hasattr(raw_response, "content"):
                story_text = raw_response.content
            
            story_text = story_text.strip()
            story_text = re.sub(r'^["\']|["\']$', '', story_text)
            
            title = f"The Epic Tale of {theme.title()}"
            excerpt = story_text[:200] + "..." if len(story_text) > 200 else story_text
            
            story_db = Story(
                title=title,
                content=story_text,
                excerpt=excerpt,
                session_id=session_id,
                is_published=False,
                story_type="written"
            )
            db.add(story_db)
            db.flush()
            
            logger.info(f"Epic full story created: {story_db.id}")
            return story_db
            
        except Exception as e:
            logger.error(f"Full story generation failed: {e}")
            logger.error(traceback.format_exc())
            
            story_db = Story(
                title=f"The Epic of {theme.title()}",
                content=f"In the legendary realm of {theme}, an epic tale unfolds. " * 10,
                excerpt=f"An epic tale from the realm of {theme}...",
                session_id=session_id,
                is_published=False,
                story_type="written"
            )
            db.add(story_db)
            db.flush()
            
            return story_db
    
    @classmethod
    def generate_assisted_story(cls, db: Session, session_id: str, prompt: str) -> Story:
        llm = cls._get_llm()
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", ASSISTED_STORY_PROMPT),
            ("human", "Story prompt: {theme}")
        ])
        
        formatted_prompt = prompt_template.invoke({"theme": prompt})
        
        try:
            logger.info(f"Generating assisted story with prompt: {prompt[:50]}...")
            raw_response = llm.invoke(formatted_prompt)
            
            story_text = raw_response
            if hasattr(raw_response, "content"):
                story_text = raw_response.content
            
            story_text = story_text.strip()
            
            lines = story_text.split('\n')
            title = lines[0].strip() if lines else f"Story about {prompt[:30]}"
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            
            content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else story_text
            if not content:
                content = story_text
            
            excerpt = content[:150] + "..." if len(content) > 150 else content

            story_db = Story(
                title=title,
                content=content,
                excerpt=excerpt,
                session_id=session_id,
                is_published=False,
                story_type="written"
            )
            db.add(story_db)
            db.flush()
            
            logger.info(f"Assisted story created: {story_db.id}")
            return story_db
            
        except Exception as e:
            logger.error(f"Assisted story generation failed: {e}")
            logger.error(traceback.format_exc())
            
            story_db = Story(
                title=f"Story about {prompt[:30]}",
                content=f"Once upon a time, in a world of {prompt}, an amazing story unfolded.",
                excerpt=f"A story about {prompt[:50]}...",
                session_id=session_id,
                is_published=False,
                story_type="written"
            )
            db.add(story_db)
            db.flush()
            
            return story_db
    
    @classmethod
    def _extract_json(cls, text: str) -> str:
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        
        return None
    
    @classmethod
    def _fix_json(cls, text: str) -> str:
        text = text.replace("'", '"')
        text = re.sub(r'([{,])\s*(\w+)\s*:', r'\1"\2":', text)
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        text = re.sub(r'}(\s*){', r'},\1{', text)
        text = re.sub(r'}(\s*)"', r'},\1"', text)
        text = re.sub(r'](\s*){', r'],\1{', text)
        return text