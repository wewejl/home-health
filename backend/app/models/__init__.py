from .user import User
from .department import Department
from .doctor import Doctor
from .session import Session
from .message import Message, SenderType
from .knowledge_base import KnowledgeBase, KnowledgeDocument
from .admin_user import AdminUser, AuditLog
from .feedback import SessionFeedback
from .disease import Disease
from .drug import Drug, DrugCategory
# from .diagnosis_session import DiagnosisSession  # 已废弃，使用统一 Session 表
# from .derma_session import DermaSession  # 已废弃，使用统一 Session 表
from .medical_event import (
    MedicalEvent, EventAttachment, EventNote, ExportRecord, ExportAccessLog,
    EventStatus, RiskLevel, AgentType, AttachmentType
)

__all__ = [
    "User", "Department", "Doctor", "Session", "Message", "SenderType",
    "KnowledgeBase", "KnowledgeDocument", "AdminUser", "AuditLog",
    "SessionFeedback", "Disease", "Drug", "DrugCategory",
    # "DiagnosisSession", "DermaSession",  # 已废弃，使用统一 Session 表
    "MedicalEvent", "EventAttachment", "EventNote", "ExportRecord", "ExportAccessLog",
    "EventStatus", "RiskLevel", "AgentType", "AttachmentType"
]
