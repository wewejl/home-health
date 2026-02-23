from .auth import router as auth_router
from .departments import router as departments_router
from .sessions import router as sessions_router  # 多智能体架构
from .feedbacks import router as feedbacks_router
from .diseases import router as diseases_router
from .drugs import router as drugs_router
from .medical_events import router as medical_events_router
from .ai import router as ai_router
from .persona_chat import router as persona_chat_router
from .record_analysis import router as record_analysis_router
from .admin_auth import router as admin_auth_router
from .admin_doctors import router as admin_doctors_router
from .admin_departments import router as admin_departments_router
from .admin_knowledge import router as admin_knowledge_router, documents_router as admin_documents_router
from .admin_feedbacks import router as admin_feedbacks_router
from .admin_stats import router as admin_stats_router
from .admin_diseases import router as admin_diseases_router
from .admin_drugs import router as admin_drugs_router, categories_router as admin_drug_categories_router
from .medical_orders import router as medical_orders_router
from .rounding import router as rounding_router
from .medical_folders import router as medical_folders_router
from .medical_records import router as medical_records_router
from .medical_files import router as medical_files_router
from .funasr import router as funasr_router
# TTS 已移除，voice.py 只包含状态查询端点（可保留或删除）
# from .voice import router as voice_router
from .voice_asr import router as voice_asr_router  # GLM-ASR 语音识别
from .doctor_workstation import router as doctor_workstation_router  # 医生工作台

__all__ = [
    "auth_router", "departments_router",
    "sessions_router",  # 多智能体架构
    "feedbacks_router", "diseases_router", "drugs_router",
    "medical_events_router", "ai_router", "persona_chat_router", "record_analysis_router",
    "medical_orders_router",  # 医嘱执行监督系统
    "rounding_router",  # 远程查房系统
    "medical_folders_router",  # 病历夹管理
    "medical_records_router",  # 病历记录管理
    "medical_files_router",  # 医疗文件上传
    "funasr_router",  # FunASR语音识别
    "voice_asr_router",  # GLM-ASR语音识别
    "admin_auth_router", "admin_doctors_router", "admin_departments_router",
    "admin_knowledge_router", "admin_documents_router", "admin_feedbacks_router", "admin_stats_router",
    "admin_diseases_router", "admin_drugs_router", "admin_drug_categories_router",
    "doctor_workstation_router",  # 医生工作台
]
