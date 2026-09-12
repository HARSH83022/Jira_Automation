from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.integrations.ai.provider import safe_generate_summary, get_provider, NoAIProvider
from app.models.report import Report
from app.schemas.schemas import AITestRequest

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/providers")
def list_providers():
    return {
        "providers": ["none", "gemini", "deepseek"],
        "descriptions": {
            "none": "No AI — deterministic report only",
            "gemini": "Google Gemini Pro (free tier available)",
            "deepseek": "DeepSeek Chat (low-cost API)",
        },
    }


@router.post("/summary/{report_id}")
async def generate_summary(report_id: int, provider: str = "none", db: Session = Depends(get_db)):
    """Generate an AI summary for an existing report. AI NEVER recalculates numbers."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    context = {
        "sprint": report.sprint,
        "report_date": report.report_date,
        "total_scope": report.total_scope,
        "completed_sp": report.completed_sp,
        "remaining_sp": report.remaining_sp,
        "completion_pct": report.completion_percentage,
        "developers": report.developer_data or [],
    }

    summary = await safe_generate_summary(context, provider_name=provider)
    return {
        "summary": summary,
        "ai_available": bool(summary and "unavailable" not in summary.lower()),
        "provider": provider,
    }


@router.post("/test")
async def test_ai(payload: AITestRequest):
    p = get_provider(payload.provider)
    if isinstance(p, NoAIProvider):
        return {"message": "No AI provider configured.", "provider": "none"}
    context = {
        "sprint": "Test Sprint",
        "report_date": datetime.now().strftime("%d/%m/%Y"),
        "total_scope": 100,
        "completed_sp": 40,
        "remaining_sp": 60,
        "completion_pct": 40.0,
        "developers": [
            {"name": "Test Dev", "assigned_sp": 100, "completed_sp": 40, "completion_pct": 40.0}
        ],
    }
    result = await safe_generate_summary(context, provider_name=payload.provider)
    return {"summary": result, "provider": payload.provider}
