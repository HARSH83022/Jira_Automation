from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(200), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
