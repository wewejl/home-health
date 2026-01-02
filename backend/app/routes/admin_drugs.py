from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from pydantic import BaseModel
from ..database import get_db
from ..models import Drug, DrugCategory
from .admin_auth import get_current_admin

router = APIRouter(prefix="/admin/drugs", tags=["admin-drugs"])
categories_router = APIRouter(prefix="/admin/drug-categories", tags=["admin-drug-categories"])


# ========== Pydantic Schemas ==========

class DrugCategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    display_type: str = "grid"
    sort_order: int = 0
    is_active: bool = True


class DrugCategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    display_type: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class DrugCategoryResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    display_type: str
    sort_order: int
    is_active: bool
    drug_count: int = 0

    class Config:
        from_attributes = True


class DrugCreate(BaseModel):
    name: str
    pinyin: Optional[str] = None
    pinyin_abbr: Optional[str] = None
    aliases: Optional[str] = None
    common_brands: Optional[str] = None
    
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
    sort_order: int = 0
    is_active: bool = True
    category_ids: List[int] = []


class DrugUpdate(BaseModel):
    name: Optional[str] = None
    pinyin: Optional[str] = None
    pinyin_abbr: Optional[str] = None
    aliases: Optional[str] = None
    common_brands: Optional[str] = None
    
    pregnancy_level: Optional[str] = None
    pregnancy_desc: Optional[str] = None
    lactation_level: Optional[str] = None
    lactation_desc: Optional[str] = None
    children_usable: Optional[bool] = None
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
    
    is_hot: Optional[bool] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    category_ids: Optional[List[int]] = None


class DrugListResponse(BaseModel):
    id: int
    name: str
    common_brands: Optional[str] = None
    is_hot: bool
    is_active: bool
    sort_order: int
    view_count: int
    category_names: List[str] = []

    class Config:
        from_attributes = True


class DrugDetailResponse(BaseModel):
    id: int
    name: str
    pinyin: Optional[str] = None
    pinyin_abbr: Optional[str] = None
    aliases: Optional[str] = None
    common_brands: Optional[str] = None
    
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
    sort_order: int = 0
    is_active: bool = True
    view_count: int = 0
    category_ids: List[int] = []

    class Config:
        from_attributes = True


class PaginatedDrugsResponse(BaseModel):
    total: int
    items: List[DrugListResponse]


# ========== 分类管理路由 ==========

@categories_router.get("", response_model=List[DrugCategoryResponse])
def list_drug_categories(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """获取所有药品分类"""
    query = db.query(DrugCategory)
    if not include_inactive:
        query = query.filter(DrugCategory.is_active == True)
    
    categories = query.order_by(DrugCategory.sort_order).all()
    
    result = []
    for cat in categories:
        drug_count = db.query(Drug).filter(Drug.categories.any(id=cat.id)).count()
        result.append(DrugCategoryResponse(
            id=cat.id,
            name=cat.name,
            icon=cat.icon,
            description=cat.description,
            display_type=cat.display_type,
            sort_order=cat.sort_order,
            is_active=cat.is_active,
            drug_count=drug_count
        ))
    
    return result


@categories_router.post("", response_model=DrugCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_drug_category(
    data: DrugCategoryCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """创建药品分类"""
    category = DrugCategory(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return DrugCategoryResponse(
        id=category.id,
        name=category.name,
        icon=category.icon,
        description=category.description,
        display_type=category.display_type,
        sort_order=category.sort_order,
        is_active=category.is_active,
        drug_count=0
    )


@categories_router.put("/{category_id}", response_model=DrugCategoryResponse)
def update_drug_category(
    category_id: int,
    data: DrugCategoryUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """更新药品分类"""
    category = db.query(DrugCategory).filter(DrugCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    
    db.commit()
    db.refresh(category)
    
    drug_count = db.query(Drug).filter(Drug.categories.any(id=category.id)).count()
    
    return DrugCategoryResponse(
        id=category.id,
        name=category.name,
        icon=category.icon,
        description=category.description,
        display_type=category.display_type,
        sort_order=category.sort_order,
        is_active=category.is_active,
        drug_count=drug_count
    )


@categories_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_drug_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """删除药品分类"""
    category = db.query(DrugCategory).filter(DrugCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    db.delete(category)
    db.commit()


# ========== 药品管理路由 ==========

@router.get("", response_model=PaginatedDrugsResponse)
def list_drugs(
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    is_hot: Optional[bool] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """获取药品列表（分页、筛选）"""
    query = db.query(Drug)
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(or_(
            Drug.name.ilike(search_term),
            Drug.pinyin.ilike(search_term),
            Drug.aliases.ilike(search_term)
        ))
    
    if category_id:
        query = query.filter(Drug.categories.any(id=category_id))
    
    if is_hot is not None:
        query = query.filter(Drug.is_hot == is_hot)
    
    if is_active is not None:
        query = query.filter(Drug.is_active == is_active)
    
    total = query.count()
    drugs = query.order_by(Drug.sort_order, Drug.id.desc()).offset(offset).limit(limit).all()
    
    items = []
    for drug in drugs:
        items.append(DrugListResponse(
            id=drug.id,
            name=drug.name,
            common_brands=drug.common_brands,
            is_hot=drug.is_hot,
            is_active=drug.is_active,
            sort_order=drug.sort_order,
            view_count=drug.view_count,
            category_names=[c.name for c in drug.categories]
        ))
    
    return PaginatedDrugsResponse(total=total, items=items)


@router.get("/{drug_id}", response_model=DrugDetailResponse)
def get_drug(
    drug_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """获取药品详情"""
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="药品不存在")
    
    return DrugDetailResponse(
        id=drug.id,
        name=drug.name,
        pinyin=drug.pinyin,
        pinyin_abbr=drug.pinyin_abbr,
        aliases=drug.aliases,
        common_brands=drug.common_brands,
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
        sort_order=drug.sort_order,
        is_active=drug.is_active,
        view_count=drug.view_count,
        category_ids=[c.id for c in drug.categories]
    )


@router.post("", response_model=DrugDetailResponse, status_code=status.HTTP_201_CREATED)
def create_drug(
    data: DrugCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """创建药品"""
    category_ids = data.category_ids
    drug_data = data.model_dump(exclude={"category_ids"})
    
    drug = Drug(**drug_data)
    
    if category_ids:
        categories = db.query(DrugCategory).filter(DrugCategory.id.in_(category_ids)).all()
        drug.categories = categories
    
    db.add(drug)
    db.commit()
    db.refresh(drug)
    
    return DrugDetailResponse(
        id=drug.id,
        name=drug.name,
        pinyin=drug.pinyin,
        pinyin_abbr=drug.pinyin_abbr,
        aliases=drug.aliases,
        common_brands=drug.common_brands,
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
        sort_order=drug.sort_order,
        is_active=drug.is_active,
        view_count=drug.view_count,
        category_ids=[c.id for c in drug.categories]
    )


@router.put("/{drug_id}", response_model=DrugDetailResponse)
def update_drug(
    drug_id: int,
    data: DrugUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """更新药品"""
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="药品不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    category_ids = update_data.pop("category_ids", None)
    
    for key, value in update_data.items():
        setattr(drug, key, value)
    
    if category_ids is not None:
        categories = db.query(DrugCategory).filter(DrugCategory.id.in_(category_ids)).all()
        drug.categories = categories
    
    db.commit()
    db.refresh(drug)
    
    return DrugDetailResponse(
        id=drug.id,
        name=drug.name,
        pinyin=drug.pinyin,
        pinyin_abbr=drug.pinyin_abbr,
        aliases=drug.aliases,
        common_brands=drug.common_brands,
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
        sort_order=drug.sort_order,
        is_active=drug.is_active,
        view_count=drug.view_count,
        category_ids=[c.id for c in drug.categories]
    )


@router.delete("/{drug_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_drug(
    drug_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """删除药品"""
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="药品不存在")
    
    db.delete(drug)
    db.commit()


@router.post("/{drug_id}/toggle-hot", response_model=DrugListResponse)
def toggle_drug_hot(
    drug_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """切换药品热门状态"""
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="药品不存在")
    
    drug.is_hot = not drug.is_hot
    db.commit()
    db.refresh(drug)
    
    return DrugListResponse(
        id=drug.id,
        name=drug.name,
        common_brands=drug.common_brands,
        is_hot=drug.is_hot,
        is_active=drug.is_active,
        sort_order=drug.sort_order,
        view_count=drug.view_count,
        category_names=[c.name for c in drug.categories]
    )


@router.post("/{drug_id}/toggle-active", response_model=DrugListResponse)
def toggle_drug_active(
    drug_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """切换药品上下架状态"""
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="药品不存在")
    
    drug.is_active = not drug.is_active
    db.commit()
    db.refresh(drug)
    
    return DrugListResponse(
        id=drug.id,
        name=drug.name,
        common_brands=drug.common_brands,
        is_hot=drug.is_hot,
        is_active=drug.is_active,
        sort_order=drug.sort_order,
        view_count=drug.view_count,
        category_names=[c.name for c in drug.categories]
    )
