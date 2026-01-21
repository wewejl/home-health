from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Disease(Base):
    """疾病模型"""
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    pinyin = Column(String(200), nullable=True, index=True)  # 拼音，用于搜索
    pinyin_abbr = Column(String(50), nullable=True, index=True)  # 拼音首字母缩写
    aliases = Column(Text, nullable=True)  # 同义词/别名，逗号分隔
    
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    recommended_department = Column(String(100), nullable=True)  # 推荐就诊科室名称
    
    # 内容模块 (Markdown 格式)
    overview = Column(Text, nullable=True)  # 简介/概述
    symptoms = Column(Text, nullable=True)  # 症状
    causes = Column(Text, nullable=True)  # 病因
    diagnosis = Column(Text, nullable=True)  # 诊断
    treatment = Column(Text, nullable=True)  # 治疗
    prevention = Column(Text, nullable=True)  # 预防
    care = Column(Text, nullable=True)  # 日常护理/注意事项
    
    # 作者与审核信息
    author_name = Column(String(50), nullable=True)
    author_title = Column(String(100), nullable=True)  # 作者职称
    author_avatar = Column(String(255), nullable=True)
    reviewer_info = Column(String(200), nullable=True)  # 审核信息，如"三甲医生专业编审"
    source = Column(String(50), nullable=True, index=True)  # 数据来源：ICD-10, medical.json, manual
    
    # 排序与状态
    is_hot = Column(Boolean, default=False)  # 是否热门
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    department = relationship("Department", back_populates="diseases")


# 在 Department 模型中添加反向关系需要更新 department.py
