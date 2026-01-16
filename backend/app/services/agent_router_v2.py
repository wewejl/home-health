"""
智能体路由器 V2 - 简化版

设计原则：硬编码映射表，不使用装饰器、自动扫描等复杂机制
新增科室只需在此文件添加注册即可
"""
from typing import Dict, Type
from .base.base_agent_v2 import BaseAgentV2
from .general_v2 import GeneralAgentV2
from .dermatology.agent_v2 import DermatologyAgentV2


class AgentRouterV2:
    """智能体路由器 V2 - 简化版"""
    
    # ========== 硬编码注册表 ==========
    _AGENTS: Dict[str, Type[BaseAgentV2]] = {
        "general": GeneralAgentV2,
        "dermatology": DermatologyAgentV2,
        # "cardiology": CardiologyAgentV2,    # 后续添加
    }
    
    # ========== 能力配置 ==========
    _CAPABILITIES: Dict[str, Dict] = {
        "general": {
            "display_name": "全科AI医生",
            "description": "通用医疗咨询",
            "actions": ["conversation"],
            "accepts_media": [],
        },
        "dermatology": {
            "display_name": "皮肤科AI医生",
            "description": "专业的皮肤科问诊智能体",
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
        },
        "cardiology": {
            "display_name": "心血管科AI医生",
            "description": "心血管疾病问诊和心电图解读",
            "actions": ["conversation", "interpret_ecg", "risk_assessment"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
        },
    }
    
    # ========== 科室映射表 ==========
    _DEPARTMENT_MAPPING: Dict[str, str] = {
        "皮肤科": "dermatology",
        "皮肤性病科": "dermatology",
        "心内科": "cardiology",
        "心血管内科": "cardiology",
        "骨科": "orthopedics",
    }
    
    @classmethod
    def get_agent(cls, agent_type: str) -> BaseAgentV2:
        """获取智能体实例"""
        agent_class = cls._AGENTS.get(agent_type)
        if not agent_class:
            raise ValueError(f"未知智能体类型: {agent_type}")
        return agent_class()
    
    @classmethod
    def get_capabilities(cls, agent_type: str) -> Dict:
        """获取智能体能力配置"""
        return cls._CAPABILITIES.get(agent_type, {})
    
    @classmethod
    def list_agents(cls) -> Dict[str, Dict]:
        """列出所有可用智能体"""
        return cls._CAPABILITIES.copy()
    
    @classmethod
    def is_valid_agent_type(cls, agent_type: str) -> bool:
        """检查智能体类型是否有效"""
        return agent_type in cls._AGENTS
    
    @classmethod
    def infer_agent_type(cls, department_name: str) -> str:
        """根据科室名称推断智能体类型"""
        if not department_name:
            return "general"
        return cls._DEPARTMENT_MAPPING.get(department_name, "general")
