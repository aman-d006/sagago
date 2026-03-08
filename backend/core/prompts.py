STORY_PROMPT = """
Create an epic multi-level interactive story based on the theme: {theme}

IMPORTANT: The story MUST have 8-10 levels of depth with multiple branching paths.

Return ONLY a valid JSON object with this structure:
{{
  "title": "Epic Story Title",
  "rootNode": {{
    "content": "Opening scene that sets the epic adventure... (3-4 sentences)",
    "isEnding": false,
    "isWinningEnding": false,
    "options": [
      {{
        "text": "First major choice",
        "nextNode": {{
          "content": "Result of first choice leading deeper...",
          "isEnding": false,
          "isWinningEnding": false,
          "options": [
            {{
              "text": "Sub-choice A",
              "nextNode": {{
                "content": "Deeper into the story...",
                "isEnding": false,
                "isWinningEnding": false,
                "options": [
                  {{
                    "text": "Final choice path",
                    "nextNode": {{
                      "content": "Epic conclusion...",
                      "isEnding": true,
                      "isWinningEnding": true,
                      "options": []
                    }}
                  }}
                ]
              }}
            }},
            {{
              "text": "Sub-choice B",
              "nextNode": {{
                "content": "Alternative path...",
                "isEnding": true,
                "isWinningEnding": false,
                "options": []
              }}
            }}
          ]
        }}
      }},
      {{
        "text": "Second major choice",
        "nextNode": {{
          "content": "Result of second choice...",
          "isEnding": false,
          "isWinningEnding": false,
          "options": [
            {{
              "text": "Branch 1",
              "nextNode": {{
                "content": "Continuing adventure...",
                "isEnding": false,
                "isWinningEnding": false,
                "options": [
                  {{
                    "text": "Deep path",
                    "nextNode": {{
                      "content": "Final outcome...",
                      "isEnding": true,
                      "isWinningEnding": true,
                      "options": []
                    }}
                  }}
                ]
              }}
            }}
          ]
        }}
      }},
      {{
        "text": "Third major choice",
        "nextNode": {{
          "content": "Mysterious path...",
          "isEnding": false,
          "isWinningEnding": false,
          "options": [
            {{
              "text": "Explore deeper",
              "nextNode": {{
                "content": "More adventures...",
                "isEnding": false,
                "isWinningEnding": false,
                "options": [
                  {{
                    "text": "Final choice",
                    "nextNode": {{
                      "content": "Conclusion...",
                      "isEnding": true,
                      "isWinningEnding": false,
                      "options": []
                    }}
                  }}
                ]
              }}
            }}
          ]
        }}
      }}
    ]
  }}
}}

Story Requirements:
- Title must be epic and reflect the theme
- Root node must have 3-4 distinct choices
- Story depth: 8-10 levels (root → choices → sub-choices → deeper → ... → endings)
- Each node (except endings) must have 2-3 choices
- Include multiple endings (at least 4 winning, 4 losing)
- Each node content: 3-5 sentences of rich, descriptive text
- Create meaningful branching paths that make the story feel epic
- Total nodes should be 30-50 for a truly epic experience

Return ONLY the JSON. No other text.
"""

# INTERACTIVE_STORY_PROMPT = STORY_PROMPT

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