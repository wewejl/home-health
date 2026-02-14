"""
智能体路由器 V3 - 支持虚拟医生分身

主要改进：
1. 支持按 doctor_id 获取对应智能体
2. 自动加载医生配置并注入到智能体
3. 保持向后兼容：支持按 agent_type 获取科室智能体
"""
from typing import Dict, List, Type, Any, Optional
from sqlalchemy.orm import Session

from .agents.doctor_react_agent import DoctorReActAgent
from .agents.router import AgentRouter as AgentRouterV2
from ..models.doctor import Doctor
from ..models.virtual_doctor import (
    list_specialties,
    get_specialty_config,
    VirtualDoctorExtension,
)


class AgentRouterV3:
    """
    智能体路由器 V3 - 虚拟医生分身支持

    支持两种模式：
    1. 按医生 ID 获取智能体（新模式）
    2. 按科室类型获取智能体（兼容 V2）
    """

    @classmethod
    def get_agent_by_doctor_id(
        cls,
        doctor_id: int,
        db: Session
    ) -> DoctorReActAgent:
        """
        根据医生 ID 获取对应的智能体

        Args:
            doctor_id: 医生 ID
            db: 数据库会话

        Returns:
            DoctorReActAgent 实例

        Raises:
            ValueError: 医生不存在或不是 AI 医生
        """
        # 查询医生
        doctor = db.query(Doctor).filter(
            Doctor.id == doctor_id,
            Doctor.is_ai == True,
            Doctor.is_active == True
        ).first()

        if not doctor:
            raise ValueError(f"虚拟医生 {doctor_id} 不存在或未激活")

        # 转换为字典配置
        doctor_config = {
            "id": doctor.id,
            "name": doctor.name,
            "title": doctor.title,
            "agent_type": doctor.agent_type,
            "department_id": doctor.department_id,
            "ai_model": doctor.ai_model,
            "ai_temperature": doctor.ai_temperature,
            "ai_max_tokens": doctor.ai_max_tokens,
            "ai_persona_prompt": doctor.ai_persona_prompt,
            "agent_config": doctor.agent_config or {},
        }

        # 创建并返回智能体
        return DoctorReActAgent(doctor_config)

    @classmethod
    def get_doctor_config(
        cls,
        doctor_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        获取医生配置（用于 API 返回）

        Args:
            doctor_id: 医生 ID
            db: 数据库会话

        Returns:
            医生配置字典
        """
        doctor = db.query(Doctor).filter(
            Doctor.id == doctor_id,
            Doctor.is_active == True
        ).first()

        if not doctor:
            return None

        return {
            "id": doctor.id,
            "name": doctor.name,
            "title": doctor.title,
            "department_id": doctor.department_id,
            "agent_type": doctor.agent_type,
            "avatar_url": doctor.avatar_url,
            "intro": doctor.intro,
            "specialty": doctor.specialty,
            "rating": doctor.rating,
            "is_ai": doctor.is_ai,
            "ai_model": doctor.ai_model,
            "ai_temperature": doctor.ai_temperature,
            "ai_max_tokens": doctor.ai_max_tokens,
            "agent_config": doctor.agent_config or {},
        }

    @classmethod
    def list_doctors_by_department(
        cls,
        department_id: int,
        db: Session,
        ai_only: bool = True,
        active_only: bool = True
    ) -> List[Doctor]:
        """
        列出科室下的医生列表

        Args:
            department_id: 科室 ID
            db: 数据库会话
            ai_only: 是否只返回 AI 医生
            active_only: 是否只返回激活的医生

        Returns:
            医生列表
        """
        query = db.query(Doctor).filter(
            Doctor.department_id == department_id
        )

        if ai_only:
            query = query.filter(Doctor.is_ai == True)
        if active_only:
            query = query.filter(Doctor.is_active == True)

        # 按评分和排序字段排序
        return query.order_by(
            Doctor.rating.desc(),
            Doctor.monthly_answers.desc()
        ).all()

    @classmethod
    def list_ai_doctors(
        cls,
        db: Session,
        department_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出所有 AI 医生（用于前端展示）

        Args:
            db: 数据库会话
            department_id: 可选，筛选科室
            limit: 限制数量

        Returns:
            医生配置列表
        """
        query = db.query(Doctor).filter(
            Doctor.is_ai == True,
            Doctor.is_active == True
        )

        if department_id:
            query = query.filter(Doctor.department_id == department_id)

        doctors = query.order_by(
            Doctor.rating.desc(),
            Doctor.monthly_answers.desc()
        ).limit(limit).all()

        return [
            {
                "id": d.id,
                "name": d.name,
                "title": d.title,
                "department_id": d.department_id,
                "agent_type": d.agent_type,
                "avatar_url": d.avatar_url,
                "intro": d.intro,
                "specialty": d.specialty,
                "rating": d.rating,
                "monthly_answers": d.monthly_answers,
                "avg_response_time": d.avg_response_time,
                "personality_type": (
                    d.agent_config.get('personality_type') if d.agent_config else None
                ) if d.agent_config else None,
            }
            for d in doctors
        ]

    @classmethod
    def get_available_personalities(cls) -> List[Dict]:
        """获取所有可用的性格类型"""
        return VirtualDoctorExtension.list_available_personalities()

    @classmethod
    def get_available_specialties(cls) -> List[Dict]:
        """获取所有可用的科室类型"""
        return list_specialties()

    @classmethod
    def infer_agent_type_from_department(cls, department_name: str) -> str:
        """
        根据科室名称推断智能体类型

        复用 V2 路由器的逻辑
        """
        return AgentRouterV2.infer_agent_type(department_name)

    # ========== 向后兼容方法 ==========

    @classmethod
    def get_agent(cls, agent_type: str, db: Optional[Session] = None):
        """
        兼容 V2：按科室类型获取智能体

        注意：此方法返回的是 V2 的科室智能体
        建议使用 get_agent_by_doctor_id
        """
        return AgentRouterV2.get_agent(agent_type)

    @classmethod
    def get_capabilities(cls, agent_type: str) -> Dict:
        """兼容 V2：获取智能体能力配置"""
        return AgentRouterV2.get_capabilities(agent_type)

    @classmethod
    def list_agents(cls) -> Dict[str, Dict]:
        """兼容 V2：列出所有可用智能体"""
        return AgentRouterV2.list_agents()

    @classmethod
    def is_valid_agent_type(cls, agent_type: str) -> bool:
        """兼容 V2：检查智能体类型是否有效"""
        return AgentRouterV2.is_valid_agent_type(agent_type)


# 便捷别名
AgentRouter = AgentRouterV3
