from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class EmailDelivery(Base):
    __tablename__ = "email_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(300), unique=True, nullable=False, index=True)
    report_type = Column(String(20), nullable=False)
    sprint = Column(String(200), nullable=False)
    sprint_id = Column(String(100), nullable=True)
    report_date = Column(String(50), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    recipients = Column(Text, nullable=False)
    attachment_filename = Column(String(500), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
