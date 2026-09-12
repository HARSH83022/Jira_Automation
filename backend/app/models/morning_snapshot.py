"""
Persisted morning snapshot — stores calculated developer stats and sprint-level
totals so an EOD upload later in the day can automatically pick them up.

Lookup key: sprint (normalised) + report_date
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class MorningSnapshot(Base):
    __tablename__ = "morning_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    # Lookup key
    sprint = Column(String(200), nullable=False, index=True)
    sprint_id = Column(String(100), nullable=True, index=True)
    sprint_start = Column(String(100), nullable=True)
    sprint_end = Column(String(100), nullable=True)
    day1_fixed_scope = Column(Float, nullable=True)
    report_date = Column(String(50), nullable=False, index=True)   # "DD/MM/YYYY"

    # Sprint-level totals (story-scope based)
    total_scope = Column(Float, default=0.0)
    completed_sp = Column(Float, default=0.0)
    completion_pct = Column(Float, default=0.0)

    # Per-developer breakdown  (JSON list matching _dev_data_to_json format)
    developer_data = Column(JSON, nullable=True)

    # Structured data-quality audit records for the snapshot
    data_quality_issues = Column(JSON, nullable=True)

    # Original CSV file metadata
    original_filename = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
