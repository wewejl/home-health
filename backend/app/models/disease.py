from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Disease(Base):
    """疾病模型 - 支持 DXY 和 MedLive 数据"""
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    aliases = Column(Text, nullable=True)  # 别名
    pinyin = Column(String(200), nullable=True, index=True)  # 拼音，用于搜索
    pinyin_abbr = Column(String(50), nullable=True, index=True)  # 拼音首字母缩写

    # MedLive 特有字段
    wiki_id = Column(String(50), nullable=True, unique=True, index=True)  # 医脉通 wiki_id
    url = Column(String(500), nullable=True)  # 原始链接

    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    recommended_department = Column(String(100), nullable=True)  # 推荐就诊科室名称

    # DXY 格式内容 (Markdown) - 保留兼容
    overview = Column(Text, nullable=True)  # 简介/概述
    symptoms = Column(Text, nullable=True)  # 症状
    causes = Column(Text, nullable=True)  # 病因
    diagnosis = Column(Text, nullable=True)  # 诊断
    treatment = Column(Text, nullable=True)  # 治疗
    prevention = Column(Text, nullable=True)  # 预防
    care = Column(Text, nullable=True)  # 日常护理

    # MedLive 格式内容 (JSONB) - 结构化区块
    sections = Column(JSON, nullable=True)  # [{"id": "overview", "title": "疾病简介", ...}]

    # 作者与审核信息（DXY 使用，MedLive 不需要）
    author_name = Column(String(50), nullable=True)
    author_title = Column(String(100), nullable=True)
    author_avatar = Column(String(255), nullable=True)
    reviewer_info = Column(String(200), nullable=True)

    source = Column(String(50), nullable=False, index=True, default="manual")  # 来源: medlive, dxy, manual

    # 排序与状态
    is_hot = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    department = relationship("Department", back_populates="diseases")


# 在 Department 模型中添加反向关系需要更新 department.py
