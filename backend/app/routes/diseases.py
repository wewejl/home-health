from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from ..database import get_db
from ..schemas.disease import DiseaseListResponse, DiseaseDetailResponse, DiseaseSearchResponse
from ..models.disease import Disease
from ..models.department import Department

router = APIRouter(prefix="/diseases", tags=["diseases"])


def _to_list_response(disease: Disease) -> DiseaseListResponse:
    """转换疾病模型为列表响应"""
    return DiseaseListResponse(
        id=disease.id,
        name=disease.name,
        department_id=disease.department_id,
        department_name=disease.department.name if disease.department else None,
        recommended_department=disease.recommended_department,
        is_hot=disease.is_hot,
        view_count=disease.view_count
    )


def _to_detail_response(disease: Disease) -> DiseaseDetailResponse:
    """转换疾病模型为详情响应"""
    return DiseaseDetailResponse(
        id=disease.id,
        name=disease.name,
        pinyin=disease.pinyin,
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
        view_count=disease.view_count,
        updated_at=disease.updated_at
    )


@router.get("", response_model=List[DiseaseListResponse])
def get_diseases(
    department_id: Optional[int] = Query(None, description="按科室筛选"),
    is_hot: Optional[bool] = Query(None, description="只返回热门疾病"),
    db: Session = Depends(get_db)
):
    """获取疾病列表"""
    query = db.query(Disease).filter(Disease.is_active == True)
    
    if department_id:
        query = query.filter(Disease.department_id == department_id)
    if is_hot is not None:
        query = query.filter(Disease.is_hot == is_hot)
    
    diseases = query.order_by(Disease.sort_order, Disease.id).all()
    return [_to_list_response(d) for d in diseases]


@router.get("/search", response_model=DiseaseSearchResponse)
def search_diseases(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    department_id: Optional[int] = Query(None, description="按科室筛选"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """搜索疾病（支持拼音、同义词、模糊匹配）"""
    query = db.query(Disease).filter(Disease.is_active == True)
    
    # 构建搜索条件：名称、拼音、拼音缩写、同义词
    search_pattern = f"%{q}%"
    search_conditions = or_(
        Disease.name.ilike(search_pattern),
        Disease.pinyin.ilike(search_pattern),
        Disease.pinyin_abbr.ilike(search_pattern),
        Disease.aliases.ilike(search_pattern)
    )
    query = query.filter(search_conditions)
    
    if department_id:
        query = query.filter(Disease.department_id == department_id)
    
    # 统计总数
    total = query.count()
    
    # 分页查询
    diseases = query.order_by(Disease.is_hot.desc(), Disease.view_count.desc()).offset(offset).limit(limit).all()
    
    return DiseaseSearchResponse(
        total=total,
        items=[_to_list_response(d) for d in diseases]
    )


@router.get("/hot", response_model=List[DiseaseListResponse])
def get_hot_diseases(
    department_id: Optional[int] = Query(None, description="按科室筛选"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取热门疾病列表"""
    query = db.query(Disease).filter(
        Disease.is_active == True,
        Disease.is_hot == True
    )
    
    if department_id:
        query = query.filter(Disease.department_id == department_id)
    
    diseases = query.order_by(Disease.sort_order, Disease.view_count.desc()).limit(limit).all()
    return [_to_list_response(d) for d in diseases]


@router.get("/departments-with-diseases")
def get_departments_with_diseases(db: Session = Depends(get_db)):
    """获取所有科室及其热门疾病（用于疾病目录页左侧科室列表）"""
    departments = db.query(Department).order_by(Department.sort_order).all()
    
    result = []
    for dept in departments:
        # 先获取热门疾病
        hot_query = db.query(Disease).filter(
            Disease.department_id == dept.id,
            Disease.is_active == True,
            Disease.is_hot == True
        ).order_by(Disease.view_count.desc(), Disease.sort_order)
        hot_diseases = hot_query.limit(10).all()
        
        # 如果热门疾病不足，补充该科室下的其他疾病，避免前端空白
        if len(hot_diseases) < 10:
            existing_ids = [d.id for d in hot_diseases]
            fallback_query = db.query(Disease).filter(
                Disease.department_id == dept.id,
                Disease.is_active == True
            )
            if existing_ids:
                fallback_query = fallback_query.filter(~Disease.id.in_(existing_ids))
            fallback_diseases = fallback_query.order_by(
                Disease.view_count.desc(),
                Disease.sort_order
            ).limit(10 - len(hot_diseases)).all()
            hot_diseases.extend(fallback_diseases)
        
        # 获取该科室下的疾病总数
        disease_count = db.query(Disease).filter(
            Disease.department_id == dept.id,
            Disease.is_active == True
        ).count()
        
        result.append({
            "id": dept.id,
            "name": dept.name,
            "icon": dept.icon,
            "disease_count": disease_count,
            "hot_diseases": [_to_list_response(d) for d in hot_diseases]
        })
    
    return result


@router.get("/{disease_id}", response_model=DiseaseDetailResponse)
def get_disease_detail(disease_id: int, db: Session = Depends(get_db)):
    """获取疾病详情"""
    disease = db.query(Disease).filter(
        Disease.id == disease_id,
        Disease.is_active == True
    ).first()
    
    if not disease:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="疾病不存在")
    
    # 增加浏览次数
    disease.view_count += 1
    db.commit()
    db.refresh(disease)
    
    return _to_detail_response(disease)
