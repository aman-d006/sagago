from sqlalchemy.orm import Session
from core.config import settings
from .groq_client import GroqLLM, MockLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.prompts import STORY_PROMPT, FULL_STORY_PROMPT, ASSISTED_STORY_PROMPT
from models.story import Story, StoryNode
from core.models import StoryLLMResponse, StoryNodeLLM, StoryOptionLLM
import json
import logging
import traceback
import re
import random
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoryGenerator:
    # Constants for story generation
    TARGET_NODES = 40  # Target 40 nodes for epic stories
    MAX_DEPTH = 10      # Maximum depth of 10 levels
    
    @classmethod
    def _get_llm(cls): 
        return GroqLLM(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
    
    @classmethod
    def generate_story(cls, db: Session, session_id: str, theme: str = "fantasy") -> Story:
        """Generate an epic interactive node-based story with 30-50 nodes and 8-10 levels deep"""
        llm = cls._get_llm()
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", STORY_PROMPT),
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
                # Try once more with a slightly different prompt
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
            
            if not story_data or "title" not in story_data or "rootNode" not in story_data:
                logger.warning("Missing required fields, retrying")
                return cls._retry_with_varied_prompt(db, session_id, theme, "complete story structure")
            
            # Validate depth - check if the story has sufficient depth
            def count_levels(node_data, current_depth=0):
                if not node_data or "options" not in node_data or not node_data["options"]:
                    return current_depth
                max_child_depth = current_depth
                for opt in node_data["options"]:
                    if "nextNode" in opt:
                        child_depth = count_levels(opt["nextNode"], current_depth + 1)
                        max_child_depth = max(max_child_depth, child_depth)
                return max_child_depth
            
            actual_depth = count_levels(story_data["rootNode"])
            logger.info(f"Story depth detected: {actual_depth} levels")
            
            if actual_depth < 5:
                logger.warning(f"Story only has {actual_depth} levels, less than requested. Using anyway.")
            
            # Create story
            story_db = Story(
                title=story_data["title"],
                session_id=session_id,
                excerpt=story_data.get("excerpt", story_data["rootNode"]["content"][:150] + "..."),
                story_type="interactive"
            )
            db.add(story_db)
            db.flush()
            
            # Process root node
            root_node = StoryNode(
                story_id=story_db.id,
                content=story_data["rootNode"]["content"],
                is_root=True,
                is_ending=story_data["rootNode"].get("isEnding", False),
                is_winning_ending=story_data["rootNode"].get("isWinningEnding", False),
                options=[]
            )
            db.add(root_node)
            db.flush()
            
            # Process options recursively
            node_count = 1
            if "options" in story_data["rootNode"] and story_data["rootNode"]["options"]:
                options = []
                for opt in story_data["rootNode"]["options"]:
                    if "nextNode" in opt:
                        child_count, child_node = cls._create_node_with_count(db, story_db.id, opt["nextNode"], depth=1)
                        node_count += child_count
                        options.append({
                            "text": opt["text"],
                            "node_id": child_node.id
                        })
                
                if options:
                    root_node.options = options
                    db.commit()
                else:
                    # No valid options created, but we still have the story
                    logger.warning(f"No valid options created for root node in story {story_db.id}")
            else:
                logger.warning(f"No options in root node for story {story_db.id}")
            
            logger.info(f"Epic story created: {story_db.id} with {node_count} nodes")
            return story_db
            
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            logger.error(traceback.format_exc())
            return cls._retry_with_varied_prompt(db, session_id, theme, "any valid format")
    
    @classmethod
    def _retry_with_varied_prompt(cls, db: Session, session_id: str, theme: str, focus: str) -> Story:
        """Retry with a varied prompt to get a valid response from Groq"""
        logger.info(f"Retrying with varied prompt for theme: {theme}, focus: {focus}")
        
        varied_prompt = f"""
        Create an interactive story about {theme} with multiple branching paths and endings.
        Focus on {focus}.
        
        Return ONLY a JSON object with this structure:
        {{
          "title": "Story Title",
          "rootNode": {{
            "content": "Opening scene...",
            "isEnding": false,
            "isWinningEnding": false,
            "options": [
              {{
                "text": "Choice description",
                "nextNode": {{
                  "content": "Result...",
                  "isEnding": true,
                  "isWinningEnding": true,
                  "options": []
                }}
              }}
            ]
          }}
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
                if story_data and "title" in story_data and "rootNode" in story_data:
                    # Create story
                    story_db = Story(
                        title=story_data["title"],
                        session_id=session_id,
                        excerpt=story_data["rootNode"]["content"][:150] + "...",
                        story_type="interactive"
                    )
                    db.add(story_db)
                    db.flush()
                    
                    # Process nodes
                    root_node = StoryNode(
                        story_id=story_db.id,
                        content=story_data["rootNode"]["content"],
                        is_root=True,
                        is_ending=False,
                        is_winning_ending=False,
                        options=[]
                    )
                    db.add(root_node)
                    db.flush()
                    
                    node_count = cls._process_nodes_simple(db, story_db.id, story_data["rootNode"], root_node)
                    
                    logger.info(f"Varied prompt retry successful: {story_db.id} with {node_count} nodes")
                    return story_db
            except Exception as e:
                logger.error(f"Failed to parse varied prompt response: {e}")
        
        # Ultimate fallback - only if Groq fails completely
        logger.warning("All Groq attempts failed, using enhanced fallback")
        return cls._create_enhanced_fallback_story(db, session_id, theme)
    
    @classmethod
    def _process_nodes_simple(cls, db: Session, story_id: int, node_data: dict, parent_node: StoryNode) -> int:
        """Process nodes for simple retry"""
        node_count = 1
        
        if "options" in node_data and node_data["options"]:
            options = []
            for opt in node_data["options"]:
                if "nextNode" in opt:
                    child = StoryNode(
                        story_id=story_id,
                        content=opt["nextNode"].get("content", "Continue..."),
                        is_root=False,
                        is_ending=opt["nextNode"].get("isEnding", False),
                        is_winning_ending=opt["nextNode"].get("isWinningEnding", False),
                        options=[]
                    )
                    db.add(child)
                    db.flush()
                    node_count += 1
                    
                    options.append({
                        "text": opt["text"],
                        "node_id": child.id
                    })
                    
                    # Recurse if needed
                    if "options" in opt["nextNode"] and opt["nextNode"]["options"] and not child.is_ending:
                        node_count += cls._process_nodes_simple(db, story_id, opt["nextNode"], child)
            
            if options:
                parent_node.options = options
                db.commit()
        
        return node_count
    
    @classmethod
    def _create_node_with_count(cls, db: Session, story_id: int, node_data: dict, depth: int = 0) -> tuple:
        """Create a node and return (node_count, node)"""
        try:
            # Determine if this should be an ending based on depth or node_data
            is_ending = node_data.get("isEnding", False) or depth >= cls.MAX_DEPTH
            
            node = StoryNode(
                story_id=story_id,
                content=node_data.get("content", "Continue the adventure..."),
                is_root=False,
                is_ending=is_ending,
                is_winning_ending=node_data.get("isWinningEnding", False) if is_ending else False,
                options=[]
            )
            db.add(node)
            db.flush()
            
            node_count = 1
            
            # Only process children if not ending and within depth limit
            if not node.is_ending and depth < cls.MAX_DEPTH and "options" in node_data and node_data["options"]:
                options = []
                for opt in node_data["options"]:
                    if "nextNode" in opt:
                        child_count, child_node = cls._create_node_with_count(db, story_id, opt["nextNode"], depth + 1)
                        node_count += child_count
                        options.append({
                            "text": opt["text"],
                            "node_id": child_node.id
                        })
                
                if options:
                    node.options = options
                    db.commit()
            
            return node_count, node
            
        except Exception as e:
            logger.error(f"Error creating node: {e}")
            # Return a simple ending node as fallback
            fallback = StoryNode(
                story_id=story_id,
                content="The adventure comes to an unexpected end.",
                is_root=False,
                is_ending=True,
                is_winning_ending=True,
                options=[]
            )
            db.add(fallback)
            db.flush()
            return 1, fallback
    
    @classmethod
    def _add_minimal_endings(cls, db: Session, story_id: int, parent_node: StoryNode, theme: str) -> int:
        """Add minimal endings when AI fails to provide options"""
        logger.info(f"Adding minimal endings to node {parent_node.id}")
        
        # Create a winning ending
        win = StoryNode(
            story_id=story_id,
            content=f"Congratulations! You successfully completed your {theme} adventure! The realm celebrates your victory.",
            is_root=False,
            is_ending=True,
            is_winning_ending=True,
            options=[]
        )
        db.add(win)
        db.flush()
        
        # Create a losing ending
        lose = StoryNode(
            story_id=story_id,
            content=f"Your {theme} journey ends here. Though you didn't succeed, you learned valuable lessons for next time.",
            is_root=False,
            is_ending=True,
            is_winning_ending=False,
            options=[]
        )
        db.add(lose)
        db.flush()
        
        parent_node.options = [
            {"text": "Take the brave path forward", "node_id": win.id},
            {"text": "Take the cautious approach", "node_id": lose.id}
        ]
        db.commit()
        
        return 2
    
    @classmethod
    def _create_enhanced_fallback_story(cls, db: Session, session_id: str, theme: str) -> Story:
        """Enhanced fallback with unique paths based on theme - only used when Groq completely fails"""
        logger.info(f"Creating enhanced fallback story for theme: {theme}")
        
        # Create theme-specific paths
        theme_lower = theme.lower()
        
        # Generate paths based on theme keywords
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
            # Generic paths for any theme
            paths = [
                {"name": "The Winding Path", "desc": f"You follow a winding path through the {theme} landscape, unsure where it leads."},
                {"name": "The Ancient Ruins", "desc": f"You discover ancient ruins that hold secrets about the history of {theme}."},
                {"name": "The Hidden Village", "desc": f"A small village appears nestled in the landscape, its inhabitants wary of strangers."},
                {"name": "The Mysterious Tower", "desc": f"A towering structure looms in the distance, beckoning you to explore its depths."}
            ]
        
        return cls._build_story_from_paths(db, session_id, theme, paths)
    
    @classmethod
    def _build_story_from_paths(cls, db: Session, session_id: str, theme: str, paths: List[dict]) -> Story:
        """Build a story from given paths"""
        story_db = Story(
            title=f"The Legend of {theme.title()}",
            session_id=session_id,
            excerpt=f"An epic adventure through the realm of {theme}...",
            story_type="interactive"
        )
        db.add(story_db)
        db.flush()
        
        nodes = []
        
        # Root node
        root = StoryNode(
            story_id=story_db.id,
            content=f"You stand at the threshold of the {theme} realm. Multiple paths stretch before you, each promising different adventures.",
            is_root=True,
            is_ending=False,
            is_winning_ending=False,
            options=[]
        )
        db.add(root)
        db.flush()
        nodes.append(root)
        
        # Path nodes
        path_nodes = []
        for path in paths:
            node = StoryNode(
                story_id=story_db.id,
                content=path["desc"],
                is_root=False,
                is_ending=False,
                is_winning_ending=False,
                options=[]
            )
            db.add(node)
            db.flush()
            path_nodes.append(node)
            nodes.append(node)
        
        # Create endings for each path
        for i, path_node in enumerate(path_nodes):
            # Each path gets 2-3 endings
            num_endings = random.randint(2, 3)
            endings = []
            
            for j in range(num_endings):
                is_winning = (j == 0)  # First ending is winning
                
                if is_winning:
                    content = f"You have triumphed! Your journey through the {theme} realm ends in glory. The legends will remember your name forever."
                else:
                    content = f"Your journey reaches an end, though not as you hoped. The lessons learned in the {theme} realm will stay with you."
                
                ending = StoryNode(
                    story_id=story_db.id,
                    content=content,
                    is_root=False,
                    is_ending=True,
                    is_winning_ending=is_winning,
                    options=[]
                )
                db.add(ending)
                db.flush()
                nodes.append(ending)
                endings.append({
                    "text": f"Path {j+1}: {'Victory' if is_winning else 'Reflection'}",
                    "node_id": ending.id
                })
            
            path_node.options = endings
            db.commit()
        
        # Set root options
        root.options = [
            {"text": paths[0]["name"], "node_id": path_nodes[0].id},
            {"text": paths[1]["name"], "node_id": path_nodes[1].id},
            {"text": paths[2]["name"], "node_id": path_nodes[2].id},
            {"text": paths[3]["name"], "node_id": path_nodes[3].id}
        ]
        db.commit()
        
        logger.info(f"Story created with ID: {story_db.id}, {len(nodes)} nodes")
        return story_db
    
    @classmethod
    def generate_full_story(cls, db: Session, session_id: str, theme: str) -> Story:
        """Generate an epic full paragraph-style story"""
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
                story_type="written"
            )
            db.add(story_db)
            db.flush()
            
            logger.info(f"Epic full story created: {story_db.id}")
            return story_db
            
        except Exception as e:
            logger.error(f"Full story generation failed: {e}")
            logger.error(traceback.format_exc())
            
            # Simple fallback
            story_db = Story(
                title=f"The Epic of {theme.title()}",
                content=f"In the legendary realm of {theme}, an epic tale unfolds. " * 10,
                excerpt=f"An epic tale from the realm of {theme}...",
                session_id=session_id,
                story_type="written"
            )
            db.add(story_db)
            db.flush()
            
            return story_db
    
    @classmethod
    def generate_assisted_story(cls, db: Session, session_id: str, prompt: str) -> Story:
        """Generate a full paragraph-style story based on user prompt"""
        llm = cls._get_llm()
        
        from core.prompts import ASSISTED_STORY_PROMPT
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
            
            # Extract title from first line
            lines = story_text.split('\n')
            title = lines[0].strip() if lines else f"Story about {prompt[:30]}"
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            
            # The rest is content
            content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else story_text
            if not content:
                content = story_text
            
            excerpt = content[:150] + "..." if len(content) > 150 else content

            story_db = Story(
                title=title,
                content=content,
                excerpt=excerpt,
                session_id=session_id,
                story_type="written"
            )
            db.add(story_db)
            db.flush()
            
            logger.info(f"Assisted story created: {story_db.id}")
            return story_db
            
        except Exception as e:
            logger.error(f"Assisted story generation failed: {e}")
            logger.error(traceback.format_exc())
            
            # Simple fallback
            story_db = Story(
                title=f"Story about {prompt[:30]}",
                content=f"Once upon a time, in a world of {prompt}, an amazing story unfolded.",
                excerpt=f"A story about {prompt[:50]}...",
                session_id=session_id,
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