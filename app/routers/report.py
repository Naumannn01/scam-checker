from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models import Report, ReportStatus, BlocklistEntry
from app.schemas import ReportRequest, ReportResponse
from app.utils import classify_input
from app.config import settings

router = APIRouter(prefix="/report", tags=["report"])


def verify_admin(x_admin_key: Optional[str] = Header(None)):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin key")


@router.post("", response_model=ReportResponse)
def create_report(request: ReportRequest, db: Session = Depends(get_db)):
    input_type = classify_input(request.reported_value)

    report = Report(
        reported_value=request.reported_value,
        input_type=input_type,
        reporter_note=request.reporter_note,
        status=ReportStatus.pending,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/pending", response_model=List[ReportResponse])
def list_pending_reports(db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    return db.query(Report).filter(Report.status == ReportStatus.pending).all()


@router.post("/{report_id}/approve", response_model=ReportResponse)
def approve_report(report_id: int, db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = ReportStatus.approved
    report.reviewed_at = datetime.now(timezone.utc)

    # feed into the same blocklist your scoring already checks
    existing = db.query(BlocklistEntry).filter(BlocklistEntry.url == report.reported_value).first()
    if not existing:
        db.add(BlocklistEntry(url=report.reported_value, source="user_report"))

    db.commit()
    db.refresh(report)
    return report


@router.post("/{report_id}/reject", response_model=ReportResponse)
def reject_report(report_id: int, db: Session = Depends(get_db), _: None = Depends(verify_admin)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = ReportStatus.rejected
    report.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report