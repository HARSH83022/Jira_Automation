import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.settings_model import AppSetting
from app.schemas.schemas import StatusSettingUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ── Completed statuses ────────────────────────────────────────────────────────

@router.get("/statuses")
def get_statuses(db: Session = Depends(get_db)):
    setting = db.query(AppSetting).filter_by(key="completed_statuses").first()
    if not setting:
        return {"statuses": ["Ready for QA", "QA Testing in Progress", "Done/ Live"]}
    return {"statuses": json.loads(setting.value)}


@router.put("/statuses")
def update_statuses(payload: StatusSettingUpdate, db: Session = Depends(get_db)):
    if not payload.statuses:
        raise HTTPException(status_code=422, detail="At least one completed status is required.")
    setting = db.query(AppSetting).filter_by(key="completed_statuses").first()
    if setting:
        setting.value = json.dumps(payload.statuses)
    else:
        setting = AppSetting(key="completed_statuses", value=json.dumps(payload.statuses))
        db.add(setting)
    db.commit()
    return {"statuses": payload.statuses, "message": "Statuses updated."}


# ── Sprint baseline settings ──────────────────────────────────────────────────

class SprintBaselineUpdate(BaseModel):
    day1_fixed_scope: Optional[float] = None
    sprint_start: Optional[str] = None  # e.g. "31/08/2026 14:06"
    developer_order: Optional[list] = None


class EmailAutomationUpdate(BaseModel):
    sender_email: Optional[str] = None
    recipients: Optional[list[str]] = None
    cc: Optional[list[str]] = None
    subject: Optional[str] = None
    report_type: Optional[str] = None
    morning_time: Optional[str] = None
    eod_time: Optional[str] = None
    timezone: Optional[str] = None
    days: Optional[list[int]] = None
    enabled: Optional[bool] = None
    jira_csv_path: Optional[str] = None


def _get_setting(db: Session, key: str, default=None):
    row = db.query(AppSetting).filter_by(key=key).first()
    if not row or row.value in ("null", "", None):
        return default
    try:
        return json.loads(row.value)
    except Exception:
        return row.value


def _set_setting(db: Session, key: str, value):
    row = db.query(AppSetting).filter_by(key=key).first()
    serialized = json.dumps(value) if value is not None else "null"
    if row:
        row.value = serialized
    else:
        db.add(AppSetting(key=key, value=serialized))
    db.commit()


@router.get("/baseline")
def get_baseline(db: Session = Depends(get_db)):
    return {
        "day1_fixed_scope": _get_setting(db, "day1_fixed_scope"),
        "sprint_start": _get_setting(db, "sprint_start"),
        "developer_order": _get_setting(db, "developer_order", [
            "Raj Shinde", "Sriniwas Chamreddy", "Sunny Shankar",
            "Dinesh Babu", "Ayush Srivastava",
        ]),
    }


@router.put("/baseline")
def update_baseline(payload: SprintBaselineUpdate, db: Session = Depends(get_db)):
    if payload.day1_fixed_scope is not None:
        _set_setting(db, "day1_fixed_scope", payload.day1_fixed_scope)
    if payload.sprint_start is not None:
        _set_setting(db, "sprint_start", payload.sprint_start)
    if payload.developer_order is not None:
        _set_setting(db, "developer_order", payload.developer_order)
    return {"message": "Baseline settings updated.", **payload.model_dump(exclude_none=True)}


@router.get("/email")
def get_email_settings(db: Session = Depends(get_db)):
    from app.services.email_service import EmailAutomationService
    return EmailAutomationService(db).settings()


@router.put("/email")
def update_email_settings(payload: EmailAutomationUpdate, db: Session = Depends(get_db)):
    from app.services.email_service import EmailAutomationService
    from app.services.scheduler import configure_scheduler
    values = payload.model_dump(exclude_none=True)
    if payload.report_type and payload.report_type not in {"MORNING", "EOD"}:
        raise HTTPException(status_code=422, detail="Report type must be MORNING or EOD.")
    result = EmailAutomationService(db).update_settings(values)
    configure_scheduler()
    return result


@router.get("/email/status")
def get_email_status(db: Session = Depends(get_db)):
    from app.services.email_service import EmailAutomationService
    return EmailAutomationService(db).validate_configuration()


# ── All settings (debug) ──────────────────────────────────────────────────────

@router.get("/all")
def get_all_settings(db: Session = Depends(get_db)):
    rows = db.query(AppSetting).all()
    result = {}
    for r in rows:
        try:
            result[r.key] = json.loads(r.value)
        except Exception:
            result[r.key] = r.value
    return result
