"""
数据加载器

优先使用 MSD 诊疗手册的真实医学数据，如果不可用则回退到示例数据。
"""
try:
    from .msd_loader import load_icd10_documents
except ImportError:
    from .icd10_loader import load_icd10_documents

from .icd10_loader import ICD10_KNOWLEDGE_BASE
from .pediatrics_loader import load_pediatrics_documents, load_pediatrics_data

__all__ = ["load_icd10_documents", "ICD10_KNOWLEDGE_BASE",
           "load_pediatrics_documents", "load_pediatrics_data"]
