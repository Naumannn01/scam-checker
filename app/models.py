from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class InputType(str, enum.Enum):
    url = "url"
    upi = "upi"
    phone = "phone"

class Verdict(str, enum.Enum):
    safe = "safe"
    suspicious = "suspicious"
    high_risk = "high_risk"
    unknown = "unknown"

class CheckedEntry(Base):
    __tablename__ = "checked_entries"

    id = Column(Integer, primary_key=True, index=True)
    input_value = Column(String, index=True, nullable=False)
    input_type = Column(Enum(InputType), nullable=False)

    verdict = Column(Enum(Verdict), default=Verdict.unknown)
    risk_score = Column(Float, default=0.0)

    # raw findings, e.g. {"domain_age_days": 5, "phishtank_hit": true, ...}
    details = Column(JSON, default={})

    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BlocklistEntry(Base):
    __tablename__ = "blocklist_entries"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, default="openphish")
    added_at = Column(DateTime(timezone=True), server_default=func.now())