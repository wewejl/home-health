from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from pydantic import BaseModel
from ..database import get_db
from ..models import Drug, DrugCategory

router = APIRouter(prefix="/drugs", tags=["drugs"])


# ========== Pydantic Schemas ==========

class DrugListItem(BaseModel):
    id: int
    name: str
    common_brands: Optional[str] = None
    is_hot: bool = False
    view_count: int = 0

    class Config:
        from_attributes = True


class DrugCategoryWithDrugs(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    display_type: str = "grid"
    drugs: List[DrugListItem] = []

    class Config:
        from_attributes = True


class DrugDetailResponse(BaseModel):
    id: int
    name: str
    common_brands: Optional[str] = None
    aliases: Optional[str] = None
    
    pregnancy_level: Optional[str] = None
    pregnancy_desc: Optional[str] = None
    lactation_level: Optional[str] = None
    lactation_desc: Optional[str] = None
    children_usable: bool = True
    children_desc: Optional[str] = None
    
    indications: Optional[str] = None
    contraindications: Optional[str] = None
    dosage: Optional[str] = None
    side_effects: Optional[str] = None
    precautions: Optional[str] = None
    interactions: Optional[str] = None
    storage: Optional[str] = None
    
    author_name: Optional[str] = None
    author_title: Optional[str] = None
    author_avatar: Optional[str] = None
    reviewer_info: Optional[str] = None
    
    is_hot: bool = False
    view_count: int = 0
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DrugSearchResponse(BaseModel):
    total: int
    items: List[DrugListItem]


# ========== 路由 ==========

@router.get("/categories", response_model=List[DrugCategoryWithDrugs])
def get_drug_categories_with_drugs(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取药品分类及其热门药品"""
    categories = db.query(DrugCategory).filter(
        DrugCategory.is_active == True
    ).order_by(DrugCategory.sort_order).all()
    
    result = []
    for cat in categories:
        drugs = db.query(Drug).filter(
            Drug.is_active == True,
            Drug.categories.any(id=cat.id)
        ).order_by(Drug.sort_order, Drug.is_hot.desc()).limit(limit).all()
        
        result.append(DrugCategoryWithDrugs(
            id=cat.id,
            name=cat.name,
            icon=cat.icon,
            display_type=cat.display_type,
            drugs=[DrugListItem.model_validate(d) for d in drugs]
        ))
    
    return result


@router.get("/hot", response_model=List[DrugListItem])
def get_hot_drugs(
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取热门药品"""
    query = db.query(Drug).filter(Drug.is_active == True, Drug.is_hot == True)
    
    if category_id:
        query = query.filter(Drug.categories.any(id=category_id))
    
    drugs = query.order_by(Drug.sort_order, Drug.view_count.desc()).limit(limit).all()
    return [DrugListItem.model_validate(d) for d in drugs]


@router.get("/search", response_model=DrugSearchResponse)
def search_drugs(
    q: str = Query(..., min_length=1),
    category_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """搜索药品（支持名称、拼音、别名）"""
    search_term = f"%{q}%"
    
    query = db.query(Drug).filter(
        Drug.is_active == True,
        or_(
            Drug.name.ilike(search_term),
            Drug.pinyin.ilike(search_term),
            Drug.pinyin_abbr.ilike(search_term),
            Drug.aliases.ilike(search_term),
            Drug.common_brands.ilike(search_term)
        )
    )
    
    if category_id:
        query = query.filter(Drug.categories.any(id=category_id))
    
    total = query.count()
    drugs = query.order_by(Drug.is_hot.desc(), Drug.sort_order).offset(offset).limit(limit).all()
    
    return DrugSearchResponse(
        total=total,
        items=[DrugListItem.model_validate(d) for d in drugs]
    )


@router.get("/{drug_id}", response_model=DrugDetailResponse)
def get_drug_detail(drug_id: int, db: Session = Depends(get_db)):
    """获取药品详情"""
    drug = db.query(Drug).filter(Drug.id == drug_id, Drug.is_active == True).first()
    
    if not drug:
        raise HTTPException(status_code=404, detail="药品不存在")
    
    # 增加浏览量
    drug.view_count += 1
    db.commit()
    
    return DrugDetailResponse(
        id=drug.id,
        name=drug.name,
        common_brands=drug.common_brands,
        aliases=drug.aliases,
        pregnancy_level=drug.pregnancy_level,
        pregnancy_desc=drug.pregnancy_desc,
        lactation_level=drug.lactation_level,
        lactation_desc=drug.lactation_desc,
        children_usable=drug.children_usable,
        children_desc=drug.children_desc,
        indications=drug.indications,
        contraindications=drug.contraindications,
        dosage=drug.dosage,
        side_effects=drug.side_effects,
        precautions=drug.precautions,
        interactions=drug.interactions,
        storage=drug.storage,
        author_name=drug.author_name,
        author_title=drug.author_title,
        author_avatar=drug.author_avatar,
        reviewer_info=drug.reviewer_info,
        is_hot=drug.is_hot,
        view_count=drug.view_count,
        updated_at=drug.updated_at.isoformat() if drug.updated_at else None
    )
