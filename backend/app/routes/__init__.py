from .auth import router as auth_router
from .departments import router as departments_router
from .sessions import router as sessions_router
from .sessions_v2 import router as sessions_v2_router
from .feedbacks import router as feedbacks_router
from .diseases import router as diseases_router
from .drugs import router as drugs_router
# from .diagnosis import router as diagnosis_router  # 已废弃，使用 sessions_router 统一接口
# from .derma import router as derma_router  # 已废弃，使用 sessions_router 统一接口
from .medical_events import router as medical_events_router
from .ai import router as ai_router
from .persona_chat import router as persona_chat_router
from .admin_auth import router as admin_auth_router
from .admin_doctors import router as admin_doctors_router
from .admin_departments import router as admin_departments_router
from .admin_knowledge import router as admin_knowledge_router, documents_router as admin_documents_router
from .admin_feedbacks import router as admin_feedbacks_router
from .admin_stats import router as admin_stats_router
from .admin_diseases import router as admin_diseases_router
from .admin_drugs import router as admin_drugs_router, categories_router as admin_drug_categories_router

__all__ = [
    "auth_router", "departments_router", "sessions_router", "sessions_v2_router", "feedbacks_router", "diseases_router", "drugs_router",
    "medical_events_router", "ai_router", "persona_chat_router",  # diagnosis_router, derma_router 已废弃，使用 sessions_router
    "admin_auth_router", "admin_doctors_router", "admin_departments_router",
    "admin_knowledge_router", "admin_documents_router", "admin_feedbacks_router", "admin_stats_router",
    "admin_diseases_router", "admin_drugs_router", "admin_drug_categories_router"
]
