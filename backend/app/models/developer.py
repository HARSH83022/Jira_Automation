from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Developer(Base):
    __tablename__ = "developers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
