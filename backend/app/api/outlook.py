from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.integrations.outlook.graph_client import outlook_client
from app.models.report import Report
from app.schemas.schemas import EmailSendRequest

router = APIRouter(prefix="/api/outlook", tags=["outlook"])


@router.get("/connect")
def connect_outlook():
    """Start Microsoft OAuth flow."""
    try:
        auth_url = outlook_client.get_auth_url()
        return {"auth_url": auth_url}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/callback")
def oauth_callback(code: str, state: str = ""):
    """Handle OAuth callback from Microsoft."""
    try:
        outlook_client.handle_callback(code, state)
        return {"message": "Outlook connected successfully.", "connected": True}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/status")
def outlook_status():
    return {"connected": outlook_client.is_connected()}


@router.post("/send")
async def send_email(payload: EmailSendRequest, db: Session = Depends(get_db)):
    """Send the report Excel via Outlook."""
    report = db.query(Report).filter(Report.id == payload.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    body = payload.body or f"""<p>Hi Team,</p>
<p>Please find attached the latest DC-AI Sprint Development Report.</p>
<ul>
  <li>Overall Sprint Completion: <strong>{report.completion_percentage:.2f}%</strong></li>
  <li>Total Scope: <strong>{report.total_scope} SP</strong></li>
  <li>Completed: <strong>{report.completed_sp} SP</strong></li>
  <li>Remaining: <strong>{report.remaining_sp} SP</strong></li>
</ul>
<p>Developer-wise details are available in the attached Excel report.</p>
<p>Regards,<br/>DC-AI Reporting System</p>"""

    try:
        await outlook_client.send_email(
            to=payload.to,
            cc=payload.cc,
            subject=payload.subject,
            body=body,
            attachment_path=report.file_path,
        )
        return {"message": "Email sent successfully."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/test")
async def test_email(payload: EmailSendRequest):
    """Send a test email without a report attachment."""
    try:
        await outlook_client.send_email(
            to=payload.to,
            cc=payload.cc,
            subject="[Test] DC-AI Reporting System",
            body="<p>This is a test email from DC-AI Reporting System.</p>",
        )
        return {"message": "Test email sent."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
