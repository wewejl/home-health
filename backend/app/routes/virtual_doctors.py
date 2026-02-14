"""
虚拟医生 API 路由

提供用户端虚拟医生查询接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..services.agent_router_v3 import AgentRouterV3
from ..services.agents.persona_builder import (
    list_available_personalities,
    get_personality_summary
)
from ..schemas.doctor import DoctorResponse, DoctorDetailResponse

router = APIRouter(prefix="/virtual-doctors", tags=["虚拟医生"])


@router.get("", response_model=List[DoctorResponse])
def list_virtual_doctors(
    department_id: Optional[int] = Query(None, description="科室 ID"),
    personality_type: Optional[str] = Query(None, description="性格类型"),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取虚拟医生列表

    - **department_id**: 筛选指定科室的医生
    - **personality_type**: 筛选指定性格的医生
    - **limit**: 限制返回数量
    """
    doctors = AgentRouterV3.list_ai_doctors(
        db=db,
        department_id=department_id
    )

    # 按性格筛选
    if personality_type:
        doctors = [
            d for d in doctors
            if d.get("personality_type") == personality_type
        ]

    # 限制数量
    doctors = doctors[:limit]

    return [DoctorResponse(**d) for d in doctors]


@router.get("/personalities")
def get_personalities():
    """
    获取所有可用的性格类型

    返回每种性格的配置信息，包括：
    - 代码
    - 名称
    - 描述
    - 风格标签
    - 推荐温度值
    """
    personalities = list_available_personalities()
    return [
        {
            "code": p["code"],
            "name": p["name"],
            "description": p["description"],
            "style_tags": p["style_tags"],
            "temperature": p["temperature"],
            "greeting_template": p["greeting_template"],
        }
        for p in personalities
    ]


@router.get("/specialties")
def get_specialties():
    """
    获取所有可用的科室类型

    返回每种科室的配置信息，包括：
    - 代码
    - 名称
    - 智能体类名
    """
    from ..models.virtual_doctor import list_specialties
    return list_specialties()


@router.get("/{doctor_id}", response_model=DoctorDetailResponse)
def get_virtual_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    """
    获取虚拟医生详情
    """
    doctor_config = AgentRouterV3.get_doctor_config(doctor_id, db)

    if not doctor_config:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="医生不存在")

    return DoctorDetailResponse(**doctor_config)


@router.get("/{doctor_id}/personality")
def get_doctor_personality(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    """
    获取虚拟医生的性格配置详情
    """
    doctor_config = AgentRouterV3.get_doctor_config(doctor_id, db)

    if not doctor_config:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="医生不存在")

    personality_type = (
        doctor_config.get("agent_config", {}).get("personality_type") or "formal"
    )

    return get_personality_summary(personality_type)
