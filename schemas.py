from typing import Literal
from pydantic import BaseModel, Field

class FeedbackAnalysis(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    category: str = Field(description="A string describing the feedback topic")
    priority: Literal["low", "medium", "high"]
    summary: str = Field(description="A short summary of the feedback")