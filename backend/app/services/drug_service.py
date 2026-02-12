"""
药品库管理服务

提供药品搜索、CRUD 操作
"""
import logging
from sqlalchemy.orm import Session
from typing import Optional, List

from ..models.drug import Drug
from ..schemas.medical_order import DrugSearchResponse

logger = logging.getLogger(__name__)


class DrugService:
    """药品库服务"""

    @staticmethod
    def search_drugs(
        db: Session,
        query: str,
        limit: int = 20
    ) -> List[Drug]:
        """
        搜索药品

        支持按药品名称、通用名搜索
        """
        try:
            # 构建搜索条件
            search_pattern = f"%{query}%"

            drugs = db.query(Drug).filter(
                Drug.is_active == True
            ).filter(
                (Drug.name.ilike(search_pattern)) |
                (Drug.generic_name.ilike(search_pattern))
            ).order_by(
                # 名称匹配优先
                Drug.name.ilike(search_pattern).desc(),
                Drug.generic_name.ilike(search_pattern).desc(),
                # 创建时间
                Drug.created_at.desc()
            ).limit(limit).all()

            logger.info(f"药品搜索: query={query}, 找到{len(drugs)}条结果")
            return drugs

        except Exception as e:
            logger.error(f"药品搜索失败: {e}")
            raise

    @staticmethod
    def get_drug_by_id(db: Session, drug_id: int) -> Optional[Drug]:
        """根据ID获取药品"""
        return db.query(Drug).filter(
            Drug.id == drug_id,
            Drug.is_active == True
        ).first()

    @staticmethod
    def create_drug_response(drug: Drug) -> DrugSearchResponse:
        """构建药品搜索响应"""
        return DrugSearchResponse(
            id=drug.id,
            name=drug.name,
            generic_name=drug.generic_name,
            specification=drug.specification,
            manufacturer=drug.manufacturer,
            category=drug.category,
            unit=drug.unit,
            stock_count=drug.stock_count
        )
