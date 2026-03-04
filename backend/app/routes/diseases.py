from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from ..database import get_db
from ..schemas.disease import (
    DiseaseListResponse,
    DiseaseDetailResponse,
    DiseaseSearchResponse,
    MedLiveDiseaseResponse,
    DiseaseSection,
    DiseaseSectionItem
)
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


def _to_medlive_response(disease: Disease) -> MedLiveDiseaseResponse:
    """转换疾病模型为 MedLive 格式响应"""
    sections_data = disease.sections or []

    # 如果有 sections 数据，直接使用
    if sections_data:
        sections = [
            DiseaseSection(
                id=s.get("id", ""),
                title=s.get("title", ""),
                icon=s.get("icon", ""),
                content=s.get("content"),
                items=[
                    DiseaseSectionItem(
                        id=item.get("id", ""),
                        title=item.get("title"),
                        content=item.get("content", ""),
                        level=item.get("level", 0)
                    )
                    for item in (s.get("items") or [])
                ] if s.get("items") else None
            )
            for s in sections_data
        ]
    else:
        # 如果没有 sections 数据，从平铺字段转换
        sections = []

        # 简介
        if disease.overview:
            sections.append(DiseaseSection(
                id="overview",
                title="疾病简介",
                icon="info.circle",
                content=disease.overview
            ))

        # 症状
        if disease.symptoms:
            sections.append(DiseaseSection(
                id="symptoms",
                title="症状表现",
                icon="stethoscope",
                content=disease.symptoms
            ))

        # 病因
        if disease.causes:
            sections.append(DiseaseSection(
                id="causes",
                title="病因分析",
                icon="magnifyingglass",
                content=disease.causes
            ))

        # 诊断
        if disease.diagnosis:
            sections.append(DiseaseSection(
                id="diagnosis",
                title="诊断方法",
                icon="text.magnifyingglass",
                content=disease.diagnosis
            ))

        # 治疗
        if disease.treatment:
            sections.append(DiseaseSection(
                id="treatment",
                title="治疗方案",
                icon="cross.case",
                content=disease.treatment
            ))

        # 预防
        if disease.prevention:
            sections.append(DiseaseSection(
                id="prevention",
                title="预防调理",
                icon="shield",
                content=disease.prevention
            ))

        # 护理
        if disease.care:
            sections.append(DiseaseSection(
                id="care",
                title="护理指南",
                icon="heart",
                content=disease.care
            ))

        # 并发症
        if disease.complications:
            sections.append(DiseaseSection(
                id="complications",
                title="并发症",
                icon="exclamationmark.triangle",
                content=disease.complications
            ))

        # 相关症状
        if disease.related_symptoms:
            sections.append(DiseaseSection(
                id="related_symptoms",
                title="相关症状",
                icon="list.bullet",
                content=disease.related_symptoms
            ))

        # 检查项目
        if disease.exam_items:
            sections.append(DiseaseSection(
                id="exam_items",
                title="检查项目",
                icon="clipboard",
                content=disease.exam_items
            ))

        # 相关疾病
        if disease.related_diseases:
            sections.append(DiseaseSection(
                id="related_diseases",
                title="相关疾病",
                icon="link",
                content=disease.related_diseases
            ))

    return MedLiveDiseaseResponse(
        id=disease.id,
        name=disease.name,
        department=disease.recommended_department or (
            disease.department.name if disease.department else None
        ),
        source=disease.source or "健康百科",
        url=disease.url or "",
        sections=sections
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
    """搜索疾病（支持拼音、模糊匹配）"""
    query = db.query(Disease).filter(Disease.is_active == True)

    # 构建搜索条件：名称、拼音、拼音缩写
    search_pattern = f"%{q}%"
    search_conditions = or_(
        Disease.name.ilike(search_pattern),
        Disease.pinyin.ilike(search_pattern),
        Disease.pinyin_abbr.ilike(search_pattern)
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
def get_departments_with_diseases(
    db: Session = Depends(get_db),
    limit: int = Query(100, description="每个科室最多返回的疾病数量，默认100（设为0返回所有）")
):
    """获取所有科室及其疾病列表（问疾病页面使用，返回所有科室）"""
    departments = db.query(Department).order_by(Department.sort_order).all()

    result = []
    for dept in departments:
        # 获取该科室下的所有疾病，按浏览量排序
        diseases_query = db.query(Disease).filter(
            Disease.department_id == dept.id,
            Disease.is_active == True
        ).order_by(Disease.is_hot.desc(), Disease.view_count.desc(), Disease.sort_order)

        if limit > 0:
            diseases_query = diseases_query.limit(limit)

        diseases = diseases_query.all()

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
            "hot_diseases": [_to_list_response(d) for d in diseases]
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
        raise HTTPException(status_code=404, detail="疾病不存在")

    # 增加浏览次数
    disease.view_count += 1
    db.commit()
    db.refresh(disease)

    return _to_detail_response(disease)


@router.get("/{disease_id}/medlive", response_model=MedLiveDiseaseResponse)
def get_disease_detail_medlive(disease_id: int, db: Session = Depends(get_db)):
    """获取疾病详情（MedLive 格式，包含 sections）"""
    disease = db.query(Disease).filter(
        Disease.id == disease_id,
        Disease.is_active == True
    ).first()

    if not disease:
        raise HTTPException(status_code=404, detail="疾病不存在")

    # 增加浏览次数
    disease.view_count += 1
    db.commit()
    db.refresh(disease)

    # _to_medlive_response 会自动处理没有 sections 的情况
    # 从平铺字段（overview, symptoms 等）转换为 sections
    return _to_medlive_response(disease)


@router.get("/wiki-id/{wiki_id}", response_model=MedLiveDiseaseResponse)
def get_disease_by_wiki_id(wiki_id: str, db: Session = Depends(get_db)):
    """通过医脉通 wiki_id 获取疾病详情（MedLive 格式）"""
    disease = db.query(Disease).filter(
        Disease.wiki_id == wiki_id,
        Disease.is_active == True
    ).first()

    if not disease:
        raise HTTPException(status_code=404, detail=f"wiki_id={wiki_id} 的疾病不存在")

    return _to_medlive_response(disease)
