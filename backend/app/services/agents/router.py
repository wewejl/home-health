"""
统一智能体路由器

硬编码注册表，简单清晰，新增科室只需在此添加注册

所有智能体均使用 ReAct 架构（2.0-react 版本）
"""
from typing import Dict, Type, Any


class AgentRouter:
    """统一智能体路由器"""

    _agents: Dict[str, Type] = {}
    _capabilities: Dict[str, Dict] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, agent_type: str, agent_class: Type, capabilities: Dict[str, Any]):
        """注册智能体"""
        cls._agents[agent_type] = agent_class
        cls._capabilities[agent_type] = capabilities
        print(f"[AgentRouter] Registered: {agent_type}")

    @classmethod
    def get_agent(cls, agent_type: str):
        """获取智能体实例"""
        cls._ensure_initialized()
        agent_class = cls._agents.get(agent_type)
        if not agent_class:
            # Fallback 到 general
            agent_class = cls._agents.get("general")
        if not agent_class:
            raise ValueError(f"未知智能体类型: {agent_type}")
        return agent_class()

    @classmethod
    def get_capabilities(cls, agent_type: str) -> Dict:
        """获取智能体能力配置"""
        cls._ensure_initialized()
        return cls._capabilities.get(agent_type, {})

    @classmethod
    def list_agents(cls) -> Dict[str, Dict]:
        """列出所有可用智能体"""
        cls._ensure_initialized()
        return cls._capabilities.copy()

    @classmethod
    def is_valid_agent_type(cls, agent_type: str) -> bool:
        """检查智能体类型是否有效"""
        cls._ensure_initialized()
        return agent_type in cls._agents

    @classmethod
    def infer_agent_type(cls, department_name: str) -> str:
        """根据科室名称推断智能体类型"""
        if not department_name:
            return "general"

        mapping = {
            # 皮肤科
            "皮肤": "dermatology",
            "皮肤科": "dermatology",
            "皮肤性病": "dermatology",
            "皮肤性病科": "dermatology",
            # 心血管科
            "心内": "cardiology",
            "心内科": "cardiology",
            "心血管": "cardiology",
            "心血管内科": "cardiology",
            # 骨科
            "骨科": "orthopedics",
            "骨伤": "orthopedics",
            "骨伤科": "orthopedics",
            # 儿科
            "儿科": "pediatrics",
            "小儿": "pediatrics",
            "小儿科": "pediatrics",
            "儿童": "pediatrics",
            # 妇产科
            "妇产": "obstetrics_gynecology",
            "妇产科": "obstetrics_gynecology",
            "妇科": "obstetrics_gynecology",
            "产科": "obstetrics_gynecology",
            "产科": "obstetrics_gynecology",
            # 消化内科
            "消化": "gastroenterology",
            "消化内科": "gastroenterology",
            "胃肠": "gastroenterology",
            "胃": "gastroenterology",
            "肠": "gastroenterology",
            # 呼吸内科
            "呼吸": "respiratory",
            "呼吸内科": "respiratory",
            "肺": "respiratory",
            "气管": "respiratory",
            # 内分泌科
            "内分泌": "endocrinology",
            "内分泌科": "endocrinology",
            "糖尿病": "endocrinology",
            "甲状腺": "endocrinology",
            # 神经内科
            "神经": "neurology",
            "神经内科": "neurology",
            "神经科": "neurology",
            "头痛": "neurology",
            # 眼科
            "眼科": "ophthalmology",
            "眼": "ophthalmology",
            "视力": "ophthalmology",
            # 耳鼻咽喉科
            "耳鼻": "otorhinolaryngology",
            "耳鼻喉": "otorhinolaryngology",
            "耳鼻咽喉": "otorhinolaryngology",
            "耳鼻咽喉科": "otorhinolaryngology",
            "五官": "otorhinolaryngology",
            # 口腔科
            "口腔": "stomatology",
            "口腔科": "stomatology",
            "牙": "stomatology",
            "牙科": "stomatology",
        }

        if department_name in mapping:
            return mapping[department_name]

        for keyword, agent_type in mapping.items():
            if keyword in department_name:
                return agent_type

        return "general"

    @classmethod
    def _ensure_initialized(cls):
        """确保智能体已初始化"""
        if not cls._initialized:
            _initialize_agents()

    @classmethod
    def reset(cls):
        """重置路由器（用于测试）"""
        cls._agents.clear()
        cls._capabilities.clear()
        cls._initialized = False


def _initialize_agents():
    """初始化并注册所有智能体（全部使用 ReAct 架构）"""
    if AgentRouter._initialized:
        return

    # ========== 全科智能体（默认备用） ==========
    from .general.react_agent import GeneralReActAgent
    AgentRouter.register(
        agent_type="general",
        agent_class=GeneralReActAgent,
        capabilities={
            "display_name": "全科AI医生",
            "description": "全科医疗咨询智能体（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 皮肤科智能体 ==========
    from .dermatology.react_agent import DermatologyReActAgent
    AgentRouter.register(
        agent_type="dermatology",
        agent_class=DermatologyReActAgent,
        capabilities={
            "display_name": "皮肤科AI医生",
            "description": "专业皮肤科问诊和图像分析（ReAct版本）",
            "actions": ["conversation", "analyze_skin", "interpret_report"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "SkinAnalysisCard", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 儿科智能体 ==========
    from .pediatrics.react_agent import PediatricsReActAgent
    AgentRouter.register(
        agent_type="pediatrics",
        agent_class=PediatricsReActAgent,
        capabilities={
            "display_name": "儿科AI医生",
            "description": "儿科疾病问诊和健康管理（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 妇产科智能体 ==========
    from .obstetrics_gynecology.react_agent import ObstetricsGynecologyReActAgent
    AgentRouter.register(
        agent_type="obstetrics_gynecology",
        agent_class=ObstetricsGynecologyReActAgent,
        capabilities={
            "display_name": "妇产科AI医生",
            "description": "妇科疾病和孕期保健咨询（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 消化内科智能体 ==========
    from .gastroenterology.react_agent import GastroenterologyReActAgent
    AgentRouter.register(
        agent_type="gastroenterology",
        agent_class=GastroenterologyReActAgent,
        capabilities={
            "display_name": "消化内科AI医生",
            "description": "消化系统疾病问诊（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 呼吸内科智能体 ==========
    from .respiratory.react_agent import RespiratoryReActAgent
    AgentRouter.register(
        agent_type="respiratory",
        agent_class=RespiratoryReActAgent,
        capabilities={
            "display_name": "呼吸内科AI医生",
            "description": "呼吸系统疾病问诊（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 心血管科智能体 ==========
    from .cardiology.react_agent import CardiologyReActAgent
    AgentRouter.register(
        agent_type="cardiology",
        agent_class=CardiologyReActAgent,
        capabilities={
            "display_name": "心血管科AI医生",
            "description": "心血管疾病问诊和心电图解读（ReAct版本）",
            "actions": ["conversation", "interpret_ecg", "risk_assessment"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "ECGAnalysisCard", "RiskAssessmentCard", "DiagnosisCard"],
            "version": "2.0-react"
        }
    )

    # ========== 内分泌科智能体 ==========
    from .endocrinology.react_agent import EndocrinologyReActAgent
    AgentRouter.register(
        agent_type="endocrinology",
        agent_class=EndocrinologyReActAgent,
        capabilities={
            "display_name": "内分泌科AI医生",
            "description": "内分泌代谢疾病问诊（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 神经内科智能体 ==========
    from .neurology.react_agent import NeurologyReActAgent
    AgentRouter.register(
        agent_type="neurology",
        agent_class=NeurologyReActAgent,
        capabilities={
            "display_name": "神经内科AI医生",
            "description": "神经系统疾病问诊（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 骨科智能体 ==========
    from .orthopedics.react_agent import OrthopedicsReActAgent
    AgentRouter.register(
        agent_type="orthopedics",
        agent_class=OrthopedicsReActAgent,
        capabilities={
            "display_name": "骨科AI医生",
            "description": "骨科疾病问诊和X光片解读（ReAct版本）",
            "actions": ["conversation", "interpret_xray"],
            "accepts_media": ["image/jpeg", "image/png", "application/pdf"],
            "ui_components": ["TextBubble", "XRayAnalysisCard", "DiagnosisCard"],
            "version": "2.0-react"
        }
    )

    # ========== 眼科智能体 ==========
    from .ophthalmology.react_agent import OphthalmologyReActAgent
    AgentRouter.register(
        agent_type="ophthalmology",
        agent_class=OphthalmologyReActAgent,
        capabilities={
            "display_name": "眼科AI医生",
            "description": "眼科疾病问诊（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 耳鼻咽喉科智能体 ==========
    from .otorhinolaryngology.react_agent import OtorhinolaryngologyReActAgent
    AgentRouter.register(
        agent_type="otorhinolaryngology",
        agent_class=OtorhinolaryngologyReActAgent,
        capabilities={
            "display_name": "耳鼻咽喉科AI医生",
            "description": "耳鼻咽喉科疾病问诊（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    # ========== 口腔科智能体 ==========
    from .stomatology.react_agent import StomatologyReActAgent
    AgentRouter.register(
        agent_type="stomatology",
        agent_class=StomatologyReActAgent,
        capabilities={
            "display_name": "口腔科AI医生",
            "description": "口腔疾病问诊（ReAct版本）",
            "actions": ["conversation"],
            "accepts_media": [],
            "ui_components": ["TextBubble", "DiagnosisCard", "MedicationCard"],
            "version": "2.0-react"
        }
    )

    AgentRouter._initialized = True
    print(f"[AgentRouter] Initialized {len(AgentRouter._agents)} agents: {list(AgentRouter._agents.keys())}")
