from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import InputType, Verdict

class CheckRequest(BaseModel):
    input_value: str
    message_text: Optional[str] = None  # for the urgency/sentiment bonus feature later

class CheckResponse(BaseModel):
    id: int
    input_value: str
    input_type: InputType
    verdict: Verdict
    risk_score: float
    details: dict
    checked_at: datetime

    class Config:
        from_attributes = True