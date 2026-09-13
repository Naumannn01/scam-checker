from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import InputType, Verdict
from app.models import ReportStatus

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

class ReportRequest(BaseModel):
    reported_value: str
    reporter_note: Optional[str] = None

class ReportResponse(BaseModel):
    id: int
    reported_value: str
    input_type: InputType
    reporter_note: Optional[str]
    status: ReportStatus
    created_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True