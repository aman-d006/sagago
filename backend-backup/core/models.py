from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class StoryOptionLLM(BaseModel):
    text: str = Field(description="The text of the option")
    nextNode: Dict[str, Any] = Field(description="The next node")

class StoryNodeLLM(BaseModel):
    content: str = Field(description="The content of the node")
    isEnding: bool = Field(description="Whether this is an ending")
    isWinningEnding: bool = Field(description="Whether this is a winning ending")
    options: Optional[List[StoryOptionLLM]] = Field(default=None, description="Options")

class StoryLLMResponse(BaseModel):
    title: str = Field(description="The story title")
    rootNode: StoryNodeLLM = Field(description="The root node")