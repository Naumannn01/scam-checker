from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CheckedEntry, InputType, Verdict
from app.schemas import CheckRequest, CheckResponse
from app.utils import classify_input
from app.tasks import check_domain_whois
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/check", tags=["check"])

@router.post("", response_model=CheckResponse)
def create_check(request: CheckRequest, db: Session = Depends(get_db)):
    input_type = classify_input(request.input_value)

    existing = db.query(CheckedEntry).filter(
        CheckedEntry.input_value == request.input_value
    ).first()

    if existing:
        return existing

    entry = CheckedEntry(
        input_value=request.input_value,
        input_type=InputType(input_type),
        verdict=Verdict.unknown,
        risk_score=0.0,
        details={},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

     # trigger enrichment: always for URLs, or for any type if a message was attached
    if input_type == "url" or request.message_text:
        check_domain_whois.delay(entry.id, request.message_text)

    return entry


@router.get("/{entry_id}", response_model=CheckResponse)
def get_check(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(CheckedEntry).filter(CheckedEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry