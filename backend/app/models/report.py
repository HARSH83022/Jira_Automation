from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(500), nullable=False)
    sprint = Column(String(200), nullable=True)
    sprint_id = Column(String(100), nullable=True)
    sprint_start = Column(String(100), nullable=True)
    sprint_end = Column(String(100), nullable=True)
    day1_fixed_scope = Column(Float, nullable=True)
    report_date = Column(String(50), nullable=True)
    snapshot_type = Column(String(20), default="EOD")  # MORNING or EOD

    # Scope
    total_scope = Column(Float, default=0.0)
    completed_sp = Column(Float, default=0.0)
    remaining_sp = Column(Float, default=0.0)
    completion_percentage = Column(Float, default=0.0)

    # Story counts
    total_stories = Column(Integer, default=0)
    completed_stories = Column(Integer, default=0)
    open_stories = Column(Integer, default=0)
    stories_without_sp = Column(Integer, default=0)
    stories_without_dev = Column(Integer, default=0)

    # Developer breakdown (stored as JSON)
    developer_data = Column(JSON, nullable=True)

    # Warnings and structured audit findings
    warnings = Column(JSON, nullable=True)
    data_quality_issues = Column(JSON, nullable=True)

    # File path to generated Excel
    file_path = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
