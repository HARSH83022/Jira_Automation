from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class DeveloperCreate(BaseModel):
    name: str
    is_active: bool = True


class DeveloperUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class DeveloperOut(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StatusSettingUpdate(BaseModel):
    statuses: List[str]


class ReportOut(BaseModel):
    id: int
    file_name: str
    sprint: Optional[str]
    report_date: Optional[str]
    snapshot_type: str
    total_scope: float
    completed_sp: float
    remaining_sp: float
    completion_percentage: float
    total_stories: int
    completed_stories: int
    open_stories: int
    stories_without_sp: int
    stories_without_dev: int
    developer_data: Optional[Any]
    warnings: Optional[Any]
    file_path: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class EmailSendRequest(BaseModel):
    report_id: int
    to: List[str]
    cc: List[str] = []
    subject: str = "DC-AI Sprint Development Report"
    body: str = ""


class AITestRequest(BaseModel):
    provider: str
    report_id: Optional[int] = None
