from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CheckedEntry, InputType, Verdict
from app.schemas import CheckRequest, CheckResponse
from app.utils import classify_input
from app.tasks import check_domain_whois
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List

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


@router.get("/history", response_model=List[CheckResponse])
def get_history(

    verdict: Optional[Verdict] = None,
    input_type: Optional[InputType] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    limit = min(limit, 100)  # hard cap to prevent abuse

    query = db.query(CheckedEntry)

    if verdict is not None:
        query = query.filter(CheckedEntry.verdict == verdict)

    if input_type is not None:
        query = query.filter(CheckedEntry.input_type == input_type)

    if min_score is not None:
        query = query.filter(CheckedEntry.risk_score >= min_score)

    if max_score is not None:
        query = query.filter(CheckedEntry.risk_score <= max_score)

    query = query.order_by(CheckedEntry.checked_at.desc())

    return query.offset(offset).limit(limit).all()

@router.post("/{entry_id}/recheck", response_model=CheckResponse)
def recheck_entry(entry_id: int, request: Optional[CheckRequest] = None, db: Session = Depends(get_db)):
    entry = db.query(CheckedEntry).filter(CheckedEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # reset state so stale data doesn't linger if the recheck fails partway
    entry.verdict = Verdict.unknown
    entry.risk_score = 0.0
    entry.details = {}
    db.commit()
    db.refresh(entry)

    message_text = request.message_text if request else None

    if entry.input_type == InputType.url or message_text:
        check_domain_whois.delay(entry.id, message_text)

    return entry

@router.get("/{entry_id}", response_model=CheckResponse)
def get_check(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(CheckedEntry).filter(CheckedEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

    