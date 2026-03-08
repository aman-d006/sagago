# core/prompts.py

INTERACTIVE_STORY_PROMPT = """
You are an expert interactive fiction writer. Create a branching narrative story with multiple choices and endings based on this theme: {theme}

Return a VALID JSON object with this exact structure:
{
  "title": "Epic Story Title",
  "premise": "Brief story setup (2-3 sentences)",
  "nodes": [
    {
      "id": 1,
      "content": "The opening scene description (3-4 sentences)",
      "is_root": true,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 2,
          "text": "Choice A description"
        },
        {
          "next_node_id": 3,
          "text": "Choice B description"
        },
        {
          "next_node_id": 4,
          "text": "Choice C description"
        }
      ]
    },
    {
      "id": 2,
      "content": "Scene after choice A (3-4 sentences)",
      "is_root": false,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 5,
          "text": "Sub-choice A1"
        },
        {
          "next_node_id": 6,
          "text": "Sub-choice A2"
        }
      ]
    },
    {
      "id": 3,
      "content": "Scene after choice B (3-4 sentences)",
      "is_root": false,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 7,
          "text": "Sub-choice B1"
        },
        {
          "next_node_id": 8,
          "text": "Sub-choice B2"
        }
      ]
    },
    {
      "id": 4,
      "content": "Scene after choice C (3-4 sentences)",
      "is_root": false,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 9,
          "text": "Sub-choice C1"
        },
        {
          "next_node_id": 10,
          "text": "Sub-choice C2"
        }
      ]
    },
    {
      "id": 5,
      "content": "Deeper into path A... (3-4 sentences)",
      "is_root": false,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 11,
          "text": "Final choice A1"
        },
        {
          "next_node_id": 12,
          "text": "Final choice A2"
        }
      ]
    },
    {
      "id": 6,
      "content": "Alternative path A2... (3-4 sentences)",
      "is_root": false,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 13,
          "text": "Final choice A3"
        }
      ]
    },
    {
      "id": 7,
      "content": "Path B1 unfolding... (3-4 sentences)",
      "is_root": false,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 14,
          "text": "Final choice B1"
        }
      ]
    },
    {
      "id": 8,
      "content": "Path B2 leading to victory... (3-4 sentences)",
      "is_root": false,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 15,
          "text": "Claim victory"
        }
      ]
    },
    {
      "id": 9,
      "content": "Path C1... (3-4 sentences)",
      "is_root": false,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 16,
          "text": "Continue"
        }
      ]
    },
    {
      "id": 10,
      "content": "Path C2... (3-4 sentences)",
      "is_root": false,
      "is_ending": false,
      "is_winning_ending": false,
      "options": [
        {
          "next_node_id": 17,
          "text": "Explore further"
        }
      ]
    },
    {
      "id": 11,
      "content": "You made it to the treasure room! The golden light illuminates ancient artifacts. You've succeeded where others failed.",
      "is_root": false,
      "is_ending": true,
      "is_winning_ending": true,
      "options": []
    },
    {
      "id": 12,
      "content": "The trap springs! You fall into a pit of spikes. Your adventure ends here.",
      "is_root": false,
      "is_ending": true,
      "is_winning_ending": false,
      "options": []
    },
    {
      "id": 13,
      "content": "You find a secret passage and escape with minor treasure. Not a complete victory, but you survive.",
      "is_root": false,
      "is_ending": true,
      "is_winning_ending": false,
      "options": []
    },
    {
      "id": 14,
      "content": "You defeat the dragon and become the hero of the kingdom! The king rewards you with half his wealth.",
      "is_root": false,
      "is_ending": true,
      "is_winning_ending": true,
      "options": []
    },
    {
      "id": 15,
      "content": "You claim the legendary sword and become the new ruler. Peace returns to the land.",
      "is_root": false,
      "is_ending": true,
      "is_winning_ending": true,
      "options": []
    },
    {
      "id": 16,
      "content": "You get lost in the caves and never find your way out. The darkness consumes you.",
      "is_root": false,
      "is_ending": true,
      "is_winning_ending": false,
      "options": []
    },
    {
      "id": 17,
      "content": "You discover ancient knowledge but are forever changed. You return home a different person.",
      "is_root": false,
      "is_ending": true,
      "is_winning_ending": true,
      "options": []
    }
  ]
}

Story Requirements:
- Title must be epic and reflect the theme
- Create 12-20 nodes total
- Root node (id:1) must have 3 choices
- Each non-ending node should have 2-3 choices
- Include 4-6 endings (mix of winning and losing)
- Depth: 3-4 levels from root to endings
- Each node content: 3-4 sentences of rich, descriptive text
- Make choices meaningful and leading to different outcomes

Return ONLY the JSON. No other text.
"""

FULL_STORY_PROMPT = """
Write a complete epic story based on the theme: {theme}

Requirements:
- Write 8-10 paragraphs
- Clear beginning, middle, and end with multiple plot points
- Rich character development and vivid descriptions
- Engaging plot with twists and turns
- Satisfying conclusion
- Return ONLY the story text, no explanations
"""

ASSISTED_STORY_PROMPT = """
Write a complete, engaging story based on the following user input: {theme}

The user has provided a theme or prompt describing what they want. Create a full story with:

- A creative title on the first line
- Rich introduction that sets the scene (2-3 paragraphs)
- Detailed body with character development and plot progression (3-5 paragraphs)
- Satisfying conclusion that resolves the story (1-2 paragraphs)

Requirements:
- Title should be on the first line, not inside quotes unless part of title
- Write 6-10 paragraphs total
- Use vivid, descriptive language
- Create engaging characters and situations
- Ensure the story has a clear beginning, middle, and end
- Match the tone and style to the user's prompt

Format your response as:
Story Title Here
[content...]

Return ONLY the story with title on first line, no explanations, no markdown.
"""
