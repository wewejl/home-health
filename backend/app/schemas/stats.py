from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class OverviewStats(BaseModel):
    total_departments: int = 0
    total_doctors: int = 0
    active_ai_doctors: int = 0
    total_sessions: int = 0
    total_messages: int = 0
    today_sessions: int = 0
    today_messages: int = 0
    pending_documents: int = 0
    pending_feedbacks: int = 0


class DailyStats(BaseModel):
    date: str
    sessions: int = 0
    messages: int = 0


class TrendStats(BaseModel):
    daily_stats: List[DailyStats] = []


class DoctorStats(BaseModel):
    doctor_id: int
    doctor_name: str
    total_sessions: int = 0
    total_messages: int = 0
    avg_rating: Optional[float] = None
    feedback_count: int = 0
