"""
知识库数据加载器
"""
from .icd10_loader import load_icd10_data
from .extended_medical_data import load_extended_medical_data

__all__ = [
    "load_icd10_data",
    "load_extended_medical_data"
]
