from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


# 药品-分类多对多关联表
drug_category_association = Table(
    'drug_category_association',
    Base.metadata,
    Column('drug_id', Integer, ForeignKey('drugs.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('drug_categories.id'), primary_key=True)
)


class DrugCategory(Base):
    """药品分类模型"""
    __tablename__ = "drug_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # 分类名称，如"热门药品"、"孕期/哺乳期用药"
    icon = Column(String(100), nullable=True)  # 图标名称
    description = Column(Text, nullable=True)
    
    # 显示配置
    display_type = Column(String(50), default="grid")  # grid / list
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    drugs = relationship("Drug", secondary=drug_category_association, back_populates="categories")


class Drug(Base):
    """药品模型"""
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # 通用名
    pinyin = Column(String(200), nullable=True, index=True)  # 拼音
    pinyin_abbr = Column(String(50), nullable=True, index=True)  # 拼音首字母
    aliases = Column(Text, nullable=True)  # 别名，逗号分隔
    common_brands = Column(Text, nullable=True)  # 常见商品名，如"赛乐欣、希舒美、齐迈星"
    
    # 安全等级
    pregnancy_level = Column(String(20), nullable=True)  # 孕期安全等级：A/B/C/D/X
    pregnancy_desc = Column(String(100), nullable=True)  # 孕期说明，如"妊娠分级 B"
    lactation_level = Column(String(20), nullable=True)  # 哺乳期等级：L1/L2/L3/L4/L5
    lactation_desc = Column(String(100), nullable=True)  # 哺乳说明，如"哺乳分级 L2"
    children_usable = Column(Boolean, default=True)  # 儿童是否可用
    children_desc = Column(String(100), nullable=True)  # 儿童用药说明
    
    # 内容模块 (Markdown)
    indications = Column(Text, nullable=True)  # 功效作用/适应症
    contraindications = Column(Text, nullable=True)  # 用药禁忌
    dosage = Column(Text, nullable=True)  # 用法用量
    side_effects = Column(Text, nullable=True)  # 不良反应
    precautions = Column(Text, nullable=True)  # 注意事项
    interactions = Column(Text, nullable=True)  # 药物相互作用
    storage = Column(Text, nullable=True)  # 贮藏方法
    
    # 作者与审核
    author_name = Column(String(50), nullable=True)
    author_title = Column(String(100), nullable=True)
    author_avatar = Column(String(255), nullable=True)
    reviewer_info = Column(String(200), nullable=True)
    
    # 状态与排序
    is_hot = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    categories = relationship("DrugCategory", secondary=drug_category_association, back_populates="drugs")
