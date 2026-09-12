from __future__ import annotations

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.models.report import Report
from app.services.email_service import EmailAutomationService

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def run_automation(report_type: str = "EOD") -> None:
    db = SessionLocal()
    try:
        service = EmailAutomationService(db)
        config = service.settings()
        source = config.get("jira_csv_path") or settings.JIRA_CSV_PATH
        if not config["enabled"] or not source or not os.path.isfile(source):
            return
        from app.services.report_service import ReportService
        report_result = ReportService(db).process_upload(
            source,
            snapshot_type=report_type,
            report_date=datetime.now(ZoneInfo(config["timezone"])).strftime("%d/%m/%Y"),
            original_filename=os.path.basename(source),
        )
        report = db.query(Report).filter_by(id=report_result["report_id"]).one()
        service.send_report(report)
    except Exception:
        logger.exception("Scheduled report delivery failed.")
    finally:
        db.close()


def configure_scheduler() -> None:
    db = SessionLocal()
    try:
        config = EmailAutomationService(db).settings()
    finally:
        db.close()
    if not config["enabled"]:
        if scheduler.running:
            scheduler.remove_all_jobs()
        return
    tz = ZoneInfo(config["timezone"])
    for job_id, report_type, clock in (
        ("jira-report-morning", "MORNING", config["morning_time"]),
        ("jira-report-eod", "EOD", config["eod_time"]),
    ):
        hour, minute = [int(part) for part in clock.split(":", 1)]
        scheduler.add_job(
            run_automation,
            CronTrigger(day_of_week=",".join(str(day) for day in config["days"]), hour=hour, minute=minute, timezone=tz),
            args=[report_type],
            id=job_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
    if scheduler.running:
        scheduler.remove_all_jobs()
    else:
        scheduler.start()


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
