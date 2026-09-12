from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.report import Report
from app.services.email_service import EmailAutomationService

router = APIRouter(prefix="/api/email", tags=["email"])


@router.post("/test")
def send_test_email(report_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Report).order_by(Report.created_at.desc())
    if report_type in {"MORNING", "EOD"}:
        query = query.filter(Report.snapshot_type == report_type)
    report = query.first()
    if not report:
        raise HTTPException(status_code=422, detail="Generate a report before sending a test email.")
    try:
        delivery = EmailAutomationService(db).send_report(report, test=True)
        return {"message": "Test email sent.", "delivery_id": delivery.id, "status": delivery.status}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/smtp-test")
def smtp_test():
    try:
        from app.integrations.email.gmail import GmailEmailProvider
        GmailEmailProvider().test_connection()
        return {"message": "Gmail SMTP connection succeeded.", "status": "PASS"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/history")
def email_history(db: Session = Depends(get_db)):
    return EmailAutomationService(db).history()
