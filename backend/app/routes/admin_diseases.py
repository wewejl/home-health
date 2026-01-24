from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from ..database import get_db
from .admin_auth import get_current_admin
from ..schemas.disease import DiseaseCreate, DiseaseUpdate, DiseaseAdminResponse
from ..models.disease import Disease
from ..models.department import Department

router = APIRouter(prefix="/admin/diseases", tags=["admin-diseases"])


def _to_admin_response(disease: Disease) -> DiseaseAdminResponse:
    """转换疾病模型为管理后台响应"""
    return DiseaseAdminResponse(
        id=disease.id,
        name=disease.name,
        pinyin=disease.pinyin,
        pinyin_abbr=disease.pinyin_abbr,
        aliases=disease.aliases,
        department_id=disease.department_id,
        department_name=disease.department.name if disease.department else None,
        recommended_department=disease.recommended_department,
        overview=disease.overview,
        symptoms=disease.symptoms,
        causes=disease.causes,
        diagnosis=disease.diagnosis,
        treatment=disease.treatment,
        prevention=disease.prevention,
        care=disease.care,
        author_name=disease.author_name,
        author_title=disease.author_title,
        author_avatar=disease.author_avatar,
        reviewer_info=disease.reviewer_info,
        is_hot=disease.is_hot,
        sort_order=disease.sort_order,
        is_active=disease.is_active,
        view_count=disease.view_count,
        created_at=disease.created_at,
        updated_at=disease.updated_at
    )


def generate_pinyin(name: str) -> tuple[str, str]:
    """生成拼音和拼音首字母缩写"""
    try:
        from pypinyin import lazy_pinyin, Style
        pinyin_list = lazy_pinyin(name)
        pinyin = ''.join(pinyin_list)
        pinyin_abbr = ''.join([p[0] if p else '' for p in pinyin_list])
        return pinyin, pinyin_abbr
    except ImportError:
        return None, None


@router.get("", response_model=List[DiseaseAdminResponse])
def list_diseases(
    department_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_hot: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """获取疾病列表（管理后台）"""
    query = db.query(Disease)
    
    if department_id:
        query = query.filter(Disease.department_id == department_id)
    if is_active is not None:
        query = query.filter(Disease.is_active == is_active)
    if is_hot is not None:
        query = query.filter(Disease.is_hot == is_hot)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(or_(
            Disease.name.ilike(search_pattern),
            Disease.pinyin.ilike(search_pattern),
            Disease.aliases.ilike(search_pattern)
        ))
    
    diseases = query.order_by(Disease.department_id, Disease.sort_order, Disease.id).all()
    return [_to_admin_response(d) for d in diseases]


@router.get("/{disease_id}", response_model=DiseaseAdminResponse)
def get_disease(
    disease_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """获取疾病详情（管理后台）"""
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="疾病不存在")
    return _to_admin_response(disease)


@router.post("", response_model=DiseaseAdminResponse)
def create_disease(
    data: DiseaseCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """创建疾病"""
    # 检查科室是否存在
    department = db.query(Department).filter(Department.id == data.department_id).first()
    if not department:
        raise HTTPException(status_code=400, detail="科室不存在")
    
    # 自动生成拼音
    pinyin, pinyin_abbr = None, None
    if not data.pinyin or not data.pinyin_abbr:
        pinyin, pinyin_abbr = generate_pinyin(data.name)
    
    disease = Disease(
        name=data.name,
        pinyin=data.pinyin or pinyin,
        pinyin_abbr=data.pinyin_abbr or pinyin_abbr,
        aliases=data.aliases,
        department_id=data.department_id,
        recommended_department=data.recommended_department or department.name,
        overview=data.overview,
        symptoms=data.symptoms,
        causes=data.causes,
        diagnosis=data.diagnosis,
        treatment=data.treatment,
        prevention=data.prevention,
        care=data.care,
        author_name=data.author_name,
        author_title=data.author_title,
        author_avatar=data.author_avatar,
        reviewer_info=data.reviewer_info or "三甲医生专业编审 · 灵犀医生官方出品",
        is_hot=data.is_hot,
        sort_order=data.sort_order,
        is_active=data.is_active
    )
    
    db.add(disease)
    db.commit()
    db.refresh(disease)
    
    return _to_admin_response(disease)


@router.put("/{disease_id}", response_model=DiseaseAdminResponse)
def update_disease(
    disease_id: int,
    data: DiseaseUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """更新疾病"""
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="疾病不存在")
    
    # 检查科室是否存在
    if data.department_id:
        department = db.query(Department).filter(Department.id == data.department_id).first()
        if not department:
            raise HTTPException(status_code=400, detail="科室不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 如果更新了名称，自动更新拼音
    if 'name' in update_data and update_data['name']:
        if 'pinyin' not in update_data or 'pinyin_abbr' not in update_data:
            pinyin, pinyin_abbr = generate_pinyin(update_data['name'])
            if 'pinyin' not in update_data:
                update_data['pinyin'] = pinyin
            if 'pinyin_abbr' not in update_data:
                update_data['pinyin_abbr'] = pinyin_abbr
    
    for key, value in update_data.items():
        setattr(disease, key, value)
    
    db.commit()
    db.refresh(disease)
    
    return _to_admin_response(disease)


@router.delete("/{disease_id}")
def delete_disease(
    disease_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """删除疾病"""
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="疾病不存在")
    
    db.delete(disease)
    db.commit()
    
    return {"message": "删除成功"}


@router.put("/{disease_id}/toggle-hot")
def toggle_hot(
    disease_id: int,
    is_hot: bool = Query(...),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """切换热门状态"""
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="疾病不存在")
    
    disease.is_hot = is_hot
    db.commit()
    
    return {"message": "更新成功", "is_hot": is_hot}


@router.put("/{disease_id}/toggle-active")
def toggle_active(
    disease_id: int,
    is_active: bool = Query(...),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """切换启用状态"""
    disease = db.query(Disease).filter(Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="疾病不存在")
    
    disease.is_active = is_active
    db.commit()
    
    return {"message": "更新成功", "is_active": is_active}
