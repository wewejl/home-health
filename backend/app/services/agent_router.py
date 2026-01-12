"""
统一智能体路由器
负责：智能体注册、能力配置、实例获取

模块化架构：
- base/: BaseAgent 基类和共享 LLM 工具
- general/: 通用智能体
- dermatology/: 皮肤科智能体
- cardiology/: 心血管内科智能体
- orthopedics/: 骨科智能体（示例）
"""
from typing import Dict, Type, Any, Optional, Callable, Awaitable

# 从 base 模块导入 BaseAgent（向后兼容）
from .base import BaseAgent


class AgentRouter:
    """统一智能体路由器"""
    
    # 智能体注册表
    _agents: Dict[str, Type[BaseAgent]] = {}
    
    # 智能体能力配置
    _capabilities: Dict[str, Dict] = {}
    
    # 初始化标志
    _initialized: bool = False
    
    @classmethod
    def register_agent(
        cls,
        agent_type: str,
        agent_class: Type[BaseAgent],
        capabilities: Dict[str, Any]
    ):
        """注册智能体"""
        cls._agents[agent_type] = agent_class
        cls._capabilities[agent_type] = capabilities
        print(f"[AgentRouter] Registered agent: {agent_type}")
    
    @classmethod
    def get_agent(cls, agent_type: str) -> BaseAgent:
        """获取智能体实例"""
        cls.ensure_initialized()
        agent_class = cls._agents.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent_class()
    
    @classmethod
    def get_capabilities(cls, agent_type: str) -> Dict:
        """获取智能体能力配置"""
        cls.ensure_initialized()
        return cls._capabilities.get(agent_type, {})
    
    @classmethod
    def list_agents(cls) -> Dict[str, Dict]:
        """列出所有可用智能体"""
        cls.ensure_initialized()
        return {
            agent_type: cls._capabilities.get(agent_type, {})
            for agent_type in cls._agents.keys()
        }
    
    @classmethod
    def is_valid_agent_type(cls, agent_type: str) -> bool:
        """检查智能体类型是否有效"""
        cls.ensure_initialized()
        return agent_type in cls._agents
    
    @classmethod
    def infer_agent_type(cls, department_name: str) -> str:
        """
        根据科室名称推断智能体类型
        
        科室映射表集中管理，新增科室只需在此添加映射
        """
        if not department_name:
            return "general"
        
        # 科室映射表（集中管理）
        department_mapping = {
            # 皮肤科
            "皮肤": "dermatology",
            "皮肤科": "dermatology",
            "皮肤性病": "dermatology",
            "皮肤性病科": "dermatology",
            # 心血管内科
            "心内": "cardiology",
            "心内科": "cardiology",
            "心血管": "cardiology",
            "心血管内科": "cardiology",
            # 骨科
            "骨科": "orthopedics",
            "骨伤": "orthopedics",
            "骨伤科": "orthopedics",
            # 未来扩展...
        }
        
        # 精确匹配
        if department_name in department_mapping:
            return department_mapping[department_name]
        
        # 模糊匹配（关键词包含）
        for keyword, agent_type in department_mapping.items():
            if keyword in department_name:
                return agent_type
        
        return "general"
    
    @classmethod
    def ensure_initialized(cls):
        """确保智能体已初始化"""
        if not cls._initialized:
            initialize_agents()
    
    @classmethod
    def reset(cls):
        """重置路由器（用于测试）"""
        cls._agents.clear()
        cls._capabilities.clear()
        cls._initialized = False


def initialize_agents():
    """
    初始化并注册所有智能体
    
    使用模块化导入方式，从各科室子目录加载智能体
    新增智能体只需：
    1. 创建新科室目录（如 orthopedics/）
    2. 在此函数中添加注册代码
    3. 在 infer_agent_type() 中添加科室映射
    """
    if AgentRouter._initialized:
        return
    
    # ========== 注册通用智能体 ==========
    from .general import GeneralAgent
    AgentRouter.register_agent(
        agent_type="general",
        agent_class=GeneralAgent,
        capabilities={
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble"],
            "description": "通用医生问诊AI"
        }
    )
    
    # ========== 注册皮肤科智能体 ==========
    from .dermatology import DermaAgentWrapper
    AgentRouter.register_agent(
        agent_type="dermatology",
        agent_class=DermaAgentWrapper,
        capabilities={
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "SkinAnalysisCard", "ReportInterpretationCard"],
            "description": "皮肤科AI智能体，支持皮肤影像分析和报告解读"
        }
    )
    
    # ========== 注册心血管内科智能体 ==========
    from .cardiology import CardioAgentWrapper
    AgentRouter.register_agent(
        agent_type="cardiology",
        agent_class=CardioAgentWrapper,
        capabilities={
            "actions": ["conversation", "interpret_ecg", "risk_assessment"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "ECGInterpretationCard", "RiskAssessmentCard"],
            "description": "心血管内科AI智能体，支持心血管症状问诊、心电图解读和风险评估"
        }
    )
    
    # ========== 注册骨科智能体（示例/预留）==========
    from .orthopedics import OrthoAgentWrapper
    AgentRouter.register_agent(
        agent_type="orthopedics",
        agent_class=OrthoAgentWrapper,
        capabilities={
            "actions": ["conversation", "interpret_xray"],
            "accepts_media": ["image/jpeg", "image/png"],
            "ui_components": ["TextBubble", "XRayInterpretationCard"],
            "description": "骨科AI智能体，支持骨科症状问诊和X光片解读"
        }
    )
    
    # ========== 未来新增智能体在此添加 ==========
    # from .neurology import NeuroAgentWrapper
    # AgentRouter.register_agent(...)
    
    AgentRouter._initialized = True
    print(f"[AgentRouter] Initialized {len(AgentRouter._agents)} agents: {list(AgentRouter._agents.keys())}")
