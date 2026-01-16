# 多智能体架构重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构现有单一皮肤科智能体架构为统一多智能体架构，支持皮肤科、心血管科等多科室扩展

**Architecture:** 
- 后端：统一响应格式（AgentResponse）+ 智能体基类（BaseAgent）+ 硬编码路由器（AgentRouter）
- iOS：通用会话层（ConversationViewModel）+ 专科数据动态渲染（SpecialtyDataView）
- 迁移策略：渐进式重构，保持新旧代码并存，确保功能不回归

**Tech Stack:** Python 3.11, FastAPI, Pydantic, SwiftUI, Combine

---

## Phase 1: 基础架构搭建（后端）

### Task 1: 创建统一响应格式 Schema

**Files:**
- Create: `backend/app/schemas/agent_response.py`
- Test: `backend/tests/schemas/test_agent_response.py`

**Step 1: 创建测试文件**

```bash
mkdir -p backend/tests/schemas
touch backend/tests/schemas/__init__.py
```

**Step 2: 编写响应格式测试**

在 `backend/tests/schemas/test_agent_response.py`:

```python
import pytest
from app.schemas.agent_response import AgentResponse

def test_agent_response_minimal():
    """测试最小必填字段"""
    response = AgentResponse(
        message="测试消息",
        stage="greeting",
        progress=0
    )
    assert response.message == "测试消息"
    assert response.stage == "greeting"
    assert response.progress == 0
    assert response.quick_options == []
    assert response.specialty_data is None

def test_agent_response_with_specialty_data():
    """测试包含专科数据"""
    response = AgentResponse(
        message="诊断完成",
        stage="diagnosing",
        progress=80,
        specialty_data={
            "diagnosis_card": {
                "summary": "湿疹",
                "conditions": [{"name": "湿疹", "confidence": 0.85}]
            }
        }
    )
    assert response.specialty_data is not None
    assert "diagnosis_card" in response.specialty_data

def test_agent_response_validation():
    """测试字段验证"""
    with pytest.raises(ValueError):
        AgentResponse(
            message="测试",
            stage="invalid_stage",
            progress=150  # 超出范围
        )
```

**Step 3: 运行测试确认失败**

```bash
cd backend
pytest tests/schemas/test_agent_response.py -v
```

Expected: FAIL - 模块不存在

**Step 4: 实现 AgentResponse Schema**

在 `backend/app/schemas/agent_response.py`:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List

class AgentResponse(BaseModel):
    """统一智能体响应格式"""
    
    # 基础字段（必填）
    message: str = Field(..., description="AI 回复内容")
    stage: str = Field(..., description="当前阶段")
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    
    # 可选字段
    quick_options: List[str] = Field(default=[], description="快捷回复选项")
    risk_level: Optional[str] = Field(None, description="风险等级")
    
    # 病历事件相关
    event_id: Optional[str] = Field(None, description="病历事件ID")
    is_new_event: bool = Field(False, description="是否创建新事件")
    should_show_dossier_prompt: bool = Field(False, description="是否提示生成病历")
    
    # 专科扩展数据
    specialty_data: Optional[Dict[str, Any]] = Field(
        None,
        description="专科特有数据"
    )
    
    # 状态持久化
    next_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="下次调用需要的状态"
    )
    
    @validator('stage')
    def validate_stage(cls, v):
        valid_stages = ['greeting', 'collecting', 'analyzing', 'diagnosing', 'completed']
        if v not in valid_stages:
            raise ValueError(f'stage must be one of {valid_stages}')
        return v
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        if v is not None:
            valid_levels = ['low', 'medium', 'high', 'emergency']
            if v not in valid_levels:
                raise ValueError(f'risk_level must be one of {valid_levels}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "根据您的描述，可能是湿疹",
                "stage": "diagnosing",
                "progress": 80,
                "quick_options": ["继续描述", "上传照片"],
                "risk_level": "low",
                "specialty_data": {
                    "diagnosis_card": {
                        "summary": "手臂湿疹",
                        "conditions": [{"name": "湿疹", "confidence": 0.85}]
                    }
                }
            }
        }
```

**Step 5: 运行测试确认通过**

```bash
pytest tests/schemas/test_agent_response.py -v
```

Expected: PASS - 所有测试通过

**Step 6: 提交**

```bash
git add backend/app/schemas/agent_response.py backend/tests/schemas/
git commit -m "feat(schema): add unified AgentResponse schema"
```

---

### Task 2: 创建智能体基类

**Files:**
- Create: `backend/app/services/base/__init__.py`
- Create: `backend/app/services/base/base_agent.py`
- Test: `backend/tests/services/test_base_agent.py`

**Step 1: 创建目录结构**

```bash
mkdir -p backend/app/services/base
mkdir -p backend/tests/services
touch backend/app/services/base/__init__.py
touch backend/tests/services/__init__.py
```

**Step 2: 编写基类测试**

在 `backend/tests/services/test_base_agent.py`:

```python
import pytest
from app.services.base.base_agent import BaseAgent
from app.schemas.agent_response import AgentResponse

class MockAgent(BaseAgent):
    """测试用的 Mock 智能体"""
    
    async def run(self, state, user_input, attachments=None, action="conversation", on_chunk=None):
        return AgentResponse(
            message="Mock response",
            stage="greeting",
            progress=0,
            next_state={"test": "state"}
        )

@pytest.mark.asyncio
async def test_base_agent_run():
    """测试基类 run 方法"""
    agent = MockAgent()
    response = await agent.run(
        state={},
        user_input="测试输入"
    )
    assert isinstance(response, AgentResponse)
    assert response.message == "Mock response"
    assert response.next_state == {"test": "state"}

@pytest.mark.asyncio
async def test_base_agent_abstract():
    """测试基类不能直接实例化"""
    with pytest.raises(TypeError):
        BaseAgent()
```

**Step 3: 运行测试确认失败**

```bash
pytest tests/services/test_base_agent.py -v
```

Expected: FAIL - 模块不存在

**Step 4: 实现 BaseAgent**

在 `backend/app/services/base/base_agent.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from ...schemas.agent_response import AgentResponse

class BaseAgent(ABC):
    """智能体抽象基类"""
    
    @abstractmethod
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str,
        attachments: List[Dict[str, Any]] = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> AgentResponse:
        """
        执行智能体逻辑
        
        Args:
            state: 从数据库恢复的状态（上次返回的 next_state）
            user_input: 用户输入文本
            attachments: 附件列表
            action: 动作类型
            on_chunk: 流式输出回调函数
            
        Returns:
            AgentResponse: 统一响应格式
        """
        pass
```

在 `backend/app/services/base/__init__.py`:

```python
from .base_agent import BaseAgent

__all__ = ['BaseAgent']
```

**Step 5: 运行测试确认通过**

```bash
pytest tests/services/test_base_agent.py -v
```

Expected: PASS

**Step 6: 提交**

```bash
git add backend/app/services/base/ backend/tests/services/
git commit -m "feat(agent): add BaseAgent abstract class"
```

---

### Task 3: 创建智能体路由器

**Files:**
- Create: `backend/app/services/agent_router_v2.py`
- Test: `backend/tests/services/test_agent_router_v2.py`

**Step 1: 编写路由器测试**

在 `backend/tests/services/test_agent_router_v2.py`:

```python
import pytest
from app.services.agent_router_v2 import AgentRouterV2
from app.services.base.base_agent import BaseAgent

def test_get_capabilities():
    """测试获取智能体能力配置"""
    caps = AgentRouterV2.get_capabilities("general")
    assert caps is not None
    assert "display_name" in caps
    assert "actions" in caps

def test_list_agents():
    """测试列出所有智能体"""
    agents = AgentRouterV2.list_agents()
    assert "general" in agents
    assert isinstance(agents["general"], dict)

def test_infer_agent_type():
    """测试科室推断"""
    assert AgentRouterV2.infer_agent_type("皮肤科") == "dermatology"
    assert AgentRouterV2.infer_agent_type("心内科") == "cardiology"
    assert AgentRouterV2.infer_agent_type("未知科室") == "general"

def test_get_agent_invalid():
    """测试获取不存在的智能体"""
    with pytest.raises(ValueError, match="未知智能体类型"):
        AgentRouterV2.get_agent("invalid_type")
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/services/test_agent_router_v2.py -v
```

Expected: FAIL - 模块不存在

**Step 3: 实现 AgentRouterV2**

在 `backend/app/services/agent_router_v2.py`:

```python
from typing import Dict, Type
from .base.base_agent import BaseAgent
from .general.general_agent import GeneralAgent

class AgentRouterV2:
    """智能体路由器 V2 - 简化版"""
    
    # 硬编码注册表（暂时只注册通用智能体）
    _AGENTS: Dict[str, Type[BaseAgent]] = {
        "general": GeneralAgent,
        # "dermatology": DermatologyAgent,  # 后续添加
        # "cardiology": CardiologyAgent,
    }
    
    # 能力配置
    _CAPABILITIES: Dict[str, Dict] = {
        "general": {
            "display_name": "全科AI医生",
            "description": "通用医疗咨询",
            "actions": ["conversation"],
            "accepts_media": [],
        },
    }
    
    # 科室映射表
    _DEPARTMENT_MAPPING: Dict[str, str] = {
        "皮肤科": "dermatology",
        "皮肤性病科": "dermatology",
        "心内科": "cardiology",
        "心血管内科": "cardiology",
        "骨科": "orthopedics",
    }
    
    @classmethod
    def get_agent(cls, agent_type: str) -> BaseAgent:
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
    def infer_agent_type(cls, department_name: str) -> str:
        """根据科室名称推断智能体类型"""
        return cls._DEPARTMENT_MAPPING.get(department_name, "general")
```

**Step 4: 创建临时 GeneralAgent（用于测试）**

在 `backend/app/services/general/general_agent.py`:

```python
from ..base.base_agent import BaseAgent
from ...schemas.agent_response import AgentResponse
from typing import Dict, Any, List, Optional, Callable

class GeneralAgent(BaseAgent):
    """通用智能体（临时实现）"""
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str,
        attachments: List[Dict[str, Any]] = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> AgentResponse:
        return AgentResponse(
            message="通用智能体回复",
            stage="greeting",
            progress=0,
            next_state={}
        )
```

创建 `backend/app/services/general/__init__.py`:

```python
from .general_agent import GeneralAgent

__all__ = ['GeneralAgent']
```

**Step 5: 运行测试确认通过**

```bash
pytest tests/services/test_agent_router_v2.py -v
```

Expected: PASS

**Step 6: 提交**

```bash
git add backend/app/services/agent_router_v2.py backend/app/services/general/ backend/tests/services/test_agent_router_v2.py
git commit -m "feat(router): add AgentRouterV2 with hardcoded registry"
```

---

## Phase 2: 重构皮肤科智能体

### Task 4: 重构 DermatologyAgent 适配新架构

**Files:**
- Create: `backend/app/services/dermatology/agent_v2.py`
- Modify: `backend/app/services/agent_router_v2.py`
- Test: `backend/tests/services/test_dermatology_agent_v2.py`

**Step 1: 编写皮肤科智能体测试**

在 `backend/tests/services/test_dermatology_agent_v2.py`:

```python
import pytest
from app.services.dermatology.agent_v2 import DermatologyAgentV2
from app.schemas.agent_response import AgentResponse

@pytest.mark.asyncio
async def test_dermatology_agent_greeting():
    """测试初次问候"""
    agent = DermatologyAgentV2()
    response = await agent.run(
        state={},
        user_input="你好"
    )
    assert isinstance(response, AgentResponse)
    assert response.stage == "greeting"
    assert response.progress >= 0

@pytest.mark.asyncio
async def test_dermatology_agent_collecting():
    """测试症状收集"""
    agent = DermatologyAgentV2()
    response = await agent.run(
        state={"stage": "greeting", "symptoms": []},
        user_input="我手臂有红疹，很痒"
    )
    assert response.stage in ["collecting", "diagnosing"]
    assert response.next_state.get("symptoms") is not None

@pytest.mark.asyncio
async def test_dermatology_agent_specialty_data():
    """测试专科数据返回"""
    agent = DermatologyAgentV2()
    response = await agent.run(
        state={"stage": "diagnosing", "symptoms": ["红疹", "瘙痒", "脱皮"]},
        user_input="症状持续3天了"
    )
    # 当症状足够时应该返回诊断卡
    if response.stage == "diagnosing":
        assert response.specialty_data is not None
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/services/test_dermatology_agent_v2.py -v
```

Expected: FAIL - 模块不存在

**Step 3: 实现 DermatologyAgentV2（简化版）**

在 `backend/app/services/dermatology/agent_v2.py`:

```python
from ..base.base_agent import BaseAgent
from ...schemas.agent_response import AgentResponse
from typing import Dict, Any, List, Optional, Callable
import re

class DermatologyAgentV2(BaseAgent):
    """皮肤科智能体 V2"""
    
    def __init__(self):
        # 初始化工具（复用现有服务）
        from ..qwen_service import QwenService
        self.llm = QwenService()
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str,
        attachments: List[Dict[str, Any]] = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> AgentResponse:
        """执行皮肤科问诊流程"""
        
        # 根据 action 分发
        if action == "analyze_skin":
            return await self._analyze_skin_image(state, attachments, on_chunk)
        else:
            return await self._conversation(state, user_input, on_chunk)
    
    async def _conversation(
        self,
        state: Dict[str, Any],
        user_input: str,
        on_chunk: Optional[Callable]
    ) -> AgentResponse:
        """对话问诊流程"""
        
        # 1. 从 state 恢复上下文
        stage = state.get("stage", "greeting")
        symptoms = state.get("symptoms", [])
        
        # 2. 提取症状（简化版 - 关键词匹配）
        new_symptoms = self._extract_symptoms_simple(user_input)
        symptoms.extend(new_symptoms)
        
        # 3. 判断阶段
        if len(symptoms) < 3:
            new_stage = "collecting"
            progress = len(symptoms) * 20
        else:
            new_stage = "diagnosing"
            progress = 80
        
        # 4. 生成回复（简化版 - 使用模板）
        message = self._generate_response_template(new_stage, symptoms)
        
        # 5. 构建专科数据
        specialty_data = None
        if new_stage == "diagnosing":
            specialty_data = {
                "diagnosis_card": {
                    "summary": f"收集到 {len(symptoms)} 个症状",
                    "conditions": [
                        {"name": "待诊断", "confidence": 0.5}
                    ]
                },
                "symptoms": symptoms
            }
        
        return AgentResponse(
            message=message,
            stage=new_stage,
            progress=progress,
            quick_options=self._get_quick_options(new_stage),
            risk_level="low",
            specialty_data=specialty_data,
            next_state={
                "stage": new_stage,
                "symptoms": symptoms,
                "questions_asked": state.get("questions_asked", 0) + 1
            }
        )
    
    def _extract_symptoms_simple(self, text: str) -> List[str]:
        """简化的症状提取（关键词匹配）"""
        symptom_keywords = {
            "痒": "瘙痒",
            "红": "红疹",
            "肿": "肿胀",
            "痛": "疼痛",
            "脱皮": "脱皮",
            "水泡": "水泡",
            "干燥": "皮肤干燥"
        }
        
        found_symptoms = []
        for keyword, symptom in symptom_keywords.items():
            if keyword in text:
                found_symptoms.append(symptom)
        
        return found_symptoms
    
    def _generate_response_template(self, stage: str, symptoms: List[str]) -> str:
        """生成回复（模板方式）"""
        if stage == "greeting":
            return "您好，我是皮肤科AI医生。请描述您的皮肤问题。"
        elif stage == "collecting":
            return f"我了解到您有 {', '.join(symptoms)} 的症状。请继续描述其他症状或上传照片。"
        else:
            return f"根据您描述的 {', '.join(symptoms)} 症状，我将为您分析。"
    
    def _get_quick_options(self, stage: str) -> List[str]:
        """获取快捷选项"""
        if stage == "diagnosing":
            return ["继续描述", "上传照片", "生成病历"]
        else:
            return ["继续描述", "上传照片"]
    
    async def _analyze_skin_image(self, state, attachments, on_chunk):
        """皮肤图像分析（占位实现）"""
        return AgentResponse(
            message="图像分析功能开发中",
            stage="analyzing",
            progress=50,
            next_state=state
        )
```

**Step 4: 运行测试确认通过**

```bash
pytest tests/services/test_dermatology_agent_v2.py -v
```

Expected: PASS

**Step 5: 在 AgentRouterV2 注册皮肤科智能体**

修改 `backend/app/services/agent_router_v2.py`:

```python
from .dermatology.agent_v2 import DermatologyAgentV2

class AgentRouterV2:
    _AGENTS: Dict[str, Type[BaseAgent]] = {
        "general": GeneralAgent,
        "dermatology": DermatologyAgentV2,  # 新增
    }
    
    _CAPABILITIES: Dict[str, Dict] = {
        "general": {...},
        "dermatology": {  # 新增
            "display_name": "皮肤科AI医生",
            "description": "专业的皮肤科问诊智能体",
            "actions": ["conversation", "analyze_skin"],
            "accepts_media": ["image/jpeg", "image/png"],
        },
    }
```

**Step 6: 测试路由器能获取皮肤科智能体**

```bash
pytest tests/services/test_agent_router_v2.py -v
```

Expected: PASS

**Step 7: 提交**

```bash
git add backend/app/services/dermatology/agent_v2.py backend/app/services/agent_router_v2.py backend/tests/services/test_dermatology_agent_v2.py
git commit -m "feat(derma): add DermatologyAgentV2 with unified response"
```

---

### Task 5: 修改统一路由使用新架构

**Files:**
- Modify: `backend/app/routes/sessions.py`
- Test: `backend/tests/routes/test_sessions_v2.py`

**Step 1: 编写路由集成测试**

在 `backend/tests/routes/test_sessions_v2.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_session_with_agent_type():
    """测试创建会话并指定智能体类型"""
    # 需要先登录获取 token
    # 这里假设已有测试用户
    response = client.post(
        "/sessions",
        json={"agent_type": "dermatology"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert "session_id" in data

def test_send_message_returns_agent_response():
    """测试发送消息返回 AgentResponse 格式"""
    # 创建会话
    session_resp = client.post(
        "/sessions",
        json={"agent_type": "dermatology"},
        headers={"Authorization": "Bearer test_token"}
    )
    session_id = session_resp.json()["session_id"]
    
    # 发送消息
    response = client.post(
        f"/sessions/{session_id}/messages",
        json={"content": "我手臂有红疹"},
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "stage" in data
    assert "progress" in data
```

**Step 2: 修改 sessions.py 使用 AgentRouterV2**

在 `backend/app/routes/sessions.py` 中找到智能体获取部分，修改为：

```python
# 原代码
from ..services.agent_router import AgentRouter

# 修改为
from ..services.agent_router_v2 import AgentRouterV2

# 在 send_message 函数中
@router.post("/{session_id}/messages")
async def send_message(...):
    # 获取智能体（使用新路由器）
    agent = AgentRouterV2.get_agent(session.agent_type)
    
    # 执行智能体（返回 AgentResponse）
    response = await agent.run(
        state=session.agent_state or {},
        user_input=content,
        attachments=attachments_data,
        action=action
    )
    
    # 保存响应
    ai_message = Message(
        session_id=session_id,
        sender=SenderType.assistant,
        content=response.message
    )
    db.add(ai_message)
    
    # 更新会话状态
    session.agent_state = response.next_state
    session.stage = response.stage
    session.progress = response.progress
    db.commit()
    
    # 返回 AgentResponse
    return response.model_dump()
```

**Step 3: 运行集成测试**

```bash
pytest tests/routes/test_sessions_v2.py -v
```

Expected: PASS（如果有认证问题，先跳过，后续修复）

**Step 4: 手动测试 API**

```bash
# 启动服务器
cd backend
uvicorn app.main:app --reload

# 在另一个终端测试
curl -X POST http://localhost:8100/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"agent_type": "dermatology"}'
```

**Step 5: 提交**

```bash
git add backend/app/routes/sessions.py backend/tests/routes/test_sessions_v2.py
git commit -m "refactor(routes): use AgentRouterV2 in sessions endpoint"
```

---

## Phase 3: iOS 客户端适配

### Task 6: 创建 AgentResponse Swift 模型

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Models/AgentResponse.swift`
- Test: 手动测试（iOS 单元测试可选）

**Step 1: 创建 AgentResponse 模型**

在 `ios/xinlingyisheng/xinlingyisheng/Models/AgentResponse.swift`:

```swift
import Foundation

// MARK: - Agent Response
struct AgentResponse: Codable {
    let message: String
    let stage: String
    let progress: Int
    let quickOptions: [String]
    let riskLevel: String?
    let eventId: String?
    let isNewEvent: Bool
    let shouldShowDossierPrompt: Bool
    let specialtyData: [String: AnyCodable]?
    let nextState: [String: AnyCodable]
    
    enum CodingKeys: String, CodingKey {
        case message
        case stage
        case progress
        case quickOptions = "quick_options"
        case riskLevel = "risk_level"
        case eventId = "event_id"
        case isNewEvent = "is_new_event"
        case shouldShowDossierPrompt = "should_show_dossier_prompt"
        case specialtyData = "specialty_data"
        case nextState = "next_state"
    }
}

// MARK: - AnyCodable (已存在则跳过)
// 用于处理动态 JSON 数据
```

**Step 2: 编译验证**

在 Xcode 中编译项目：
```
⌘ + B
```

Expected: 编译成功

**Step 3: 提交**

```bash
cd ios/xinlingyisheng
git add xinlingyisheng/Models/AgentResponse.swift
git commit -m "feat(ios): add AgentResponse model"
```

---

### Task 7: 重构 ConversationViewModel

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift`
- 或 Create: `ios/xinlingyisheng/xinlingyisheng/ViewModels/ConversationViewModel.swift`

**Step 1: 创建新的 ConversationViewModel**

在 `ios/xinlingyisheng/xinlingyisheng/ViewModels/ConversationViewModel.swift`:

```swift
import Foundation
import Combine

@MainActor
class ConversationViewModel: ObservableObject {
    // MARK: - 通用状态
    @Published var sessionId: String?
    @Published var agentType: AgentType?
    @Published var messages: [Message] = []
    @Published var isLoading = false
    
    // 从 AgentResponse 映射的字段
    @Published var stage: String = "greeting"
    @Published var progress: Int = 0
    @Published var quickOptions: [String] = []
    @Published var riskLevel: String?
    
    // MARK: - 专科数据（原始 JSON）
    @Published var specialtyData: [String: Any]?
    
    // MARK: - 病历事件
    @Published var eventId: String?
    @Published var isNewEvent: Bool = false
    @Published var shouldShowDossierPrompt: Bool = false
    
    private let apiService = APIService.shared
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - 初始化会话
    func initializeSession(doctorId: Int?, agentType: AgentType?) async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            let response = try await apiService.createUnifiedSession(
                doctorId: doctorId,
                agentType: agentType
            )
            self.sessionId = response.sessionId
            self.agentType = agentType
        } catch {
            print("[ConversationVM] Error creating session: \(error)")
        }
    }
    
    // MARK: - 发送消息
    func sendMessage(
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation
    ) async {
        guard let sessionId = sessionId else { return }
        
        isLoading = true
        defer { isLoading = false }
        
        // 添加用户消息到列表
        let userMessage = Message(
            id: UUID(),
            content: content,
            isFromUser: true,
            timestamp: Date()
        )
        messages.append(userMessage)
        
        do {
            // 调用 API（非流式版本，简化实现）
            let response = try await apiService.sendUnifiedMessage(
                sessionId: sessionId,
                content: content,
                attachments: attachments,
                action: action
            )
            
            // 更新通用状态
            self.stage = response.stage
            self.progress = response.progress
            self.quickOptions = response.quickOptions
            self.riskLevel = response.riskLevel
            self.eventId = response.eventId
            self.isNewEvent = response.isNewEvent
            self.shouldShowDossierPrompt = response.shouldShowDossierPrompt
            
            // 保存专科数据（不解析）
            if let specialtyData = response.specialtyData {
                self.specialtyData = specialtyData.mapValues { $0.value }
            }
            
            // 添加 AI 消息
            let aiMessage = Message(
                id: UUID(),
                content: response.message,
                isFromUser: false,
                timestamp: Date()
            )
            messages.append(aiMessage)
            
        } catch {
            print("[ConversationVM] Error sending message: \(error)")
        }
    }
}
```

**Step 2: 编译验证**

```
⌘ + B
```

Expected: 编译成功

**Step 3: 提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/ViewModels/ConversationViewModel.swift
git commit -m "feat(ios): add ConversationViewModel with unified response handling"
```

---

### Task 8: 创建专科数据渲染视图

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Views/Components/SpecialtyDataView.swift`

**Step 1: 创建 SpecialtyDataView**

```swift
import SwiftUI

struct SpecialtyDataView: View {
    let data: [String: Any]
    
    var body: some View {
        VStack(spacing: 12) {
            // 皮肤科数据
            if let diagnosisCard = data["diagnosis_card"] as? [String: Any] {
                DiagnosisCardView(data: diagnosisCard)
            }
            
            if let adviceHistory = data["advice_history"] as? [[String: Any]] {
                ForEach(Array(adviceHistory.enumerated()), id: \.offset) { _, advice in
                    AdviceCardView(data: advice)
                }
            }
            
            if let symptoms = data["symptoms"] as? [String] {
                SymptomsListView(symptoms: symptoms)
            }
            
            // 心血管科数据（预留）
            if let ecgAnalysis = data["ecg_analysis"] as? [String: Any] {
                ECGAnalysisView(data: ecgAnalysis)
            }
        }
    }
}

// MARK: - 症状列表视图（新增）
struct SymptomsListView: View {
    let symptoms: [String]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("收集到的症状")
                .font(.headline)
            
            ForEach(symptoms, id: \.self) { symptom in
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    Text(symptom)
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
}

// MARK: - 心电图分析视图（占位）
struct ECGAnalysisView: View {
    let data: [String: Any]
    
    var body: some View {
        Text("心电图分析（开发中）")
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)
    }
}
```

**Step 2: 编译验证**

```
⌘ + B
```

Expected: 编译成功

**Step 3: 提交**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/Components/SpecialtyDataView.swift
git commit -m "feat(ios): add SpecialtyDataView for dynamic specialty data rendering"
```

---

## Phase 4: 清理与文档

### Task 9: 废弃旧版 /derma 路由

**Files:**
- Modify: `backend/app/routes/derma.py`
- Modify: `backend/README.md`

**Step 1: 在旧路由添加废弃警告**

在 `backend/app/routes/derma.py` 顶部添加：

```python
"""
⚠️ 已废弃 (Deprecated)

本模块中的所有接口已被统一会话接口 /sessions 替代。
请使用 /sessions 接口，支持所有科室的智能体。

废弃时间: 2026-01-17
计划移除: v2.0

迁移指南:
- POST /derma/start → POST /sessions (agent_type="dermatology")
- POST /derma/continue → POST /sessions/{id}/messages
"""

import warnings
warnings.warn(
    "derma routes are deprecated, use /sessions instead",
    DeprecationWarning,
    stacklevel=2
)
```

**Step 2: 更新 README**

在 `backend/README.md` 添加：

```markdown
## ⚠️ API 变更说明

### 已废弃接口

以下接口已废弃，将在 v2.0 移除：

- `POST /derma/start` → 使用 `POST /sessions` (agent_type="dermatology")
- `POST /derma/continue` → 使用 `POST /sessions/{id}/messages`

### 推荐使用

✅ **统一会话接口** (支持所有科室):
- `POST /sessions` - 创建会话
- `POST /sessions/{id}/messages` - 发送消息
- `GET /sessions/{id}/messages` - 获取历史
```

**Step 3: 提交**

```bash
git add backend/app/routes/derma.py backend/README.md
git commit -m "docs: mark /derma routes as deprecated"
```

---

### Task 10: 更新 API 契约文档

**Files:**
- Modify: `docs/API_CONTRACT.md`

**Step 1: 更新文档**

在 `docs/API_CONTRACT.md` 中添加 AgentResponse 格式说明：

```markdown
### 统一智能体响应格式

所有智能体（皮肤科、心血管科等）返回统一格式：

```json
{
  "message": "AI 回复内容",
  "stage": "greeting | collecting | analyzing | diagnosing | completed",
  "progress": 80,
  "quick_options": ["继续描述", "上传照片"],
  "risk_level": "low | medium | high | emergency",
  "event_id": "uuid",
  "is_new_event": false,
  "should_show_dossier_prompt": false,
  "specialty_data": {
    // 专科特有数据（动态字段）
    "diagnosis_card": {...},  // 皮肤科
    "ecg_analysis": {...}     // 心血管科
  },
  "next_state": {
    // 智能体内部状态（前端无需关心）
  }
}
```

#### 专科数据格式

**皮肤科 (dermatology)**:
```json
{
  "diagnosis_card": {
    "summary": "诊断摘要",
    "conditions": [...]
  },
  "advice_history": [...],
  "symptoms": ["瘙痒", "红疹"]
}
```

**心血管科 (cardiology)**:
```json
{
  "ecg_analysis": {
    "heart_rate": 75,
    "rhythm": "正常"
  },
  "risk_assessment": {...}
}
```
```

**Step 2: 提交**

```bash
git add docs/API_CONTRACT.md
git commit -m "docs: update API contract with AgentResponse format"
```

---

## Phase 5: 测试与验证

### Task 11: 端到端测试

**Files:**
- Create: `backend/tests/e2e/test_dermatology_flow.py`

**Step 1: 编写端到端测试**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_dermatology_full_flow():
    """测试皮肤科完整问诊流程"""
    
    # 1. 登录获取 token（假设已有测试用户）
    login_resp = client.post("/auth/login", json={
        "phone": "13800138000",
        "code": "123456"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 创建皮肤科会话
    session_resp = client.post(
        "/sessions",
        json={"agent_type": "dermatology"},
        headers=headers
    )
    assert session_resp.status_code in [200, 201]
    session_id = session_resp.json()["session_id"]
    
    # 3. 第一轮对话 - 问候
    msg1_resp = client.post(
        f"/sessions/{session_id}/messages",
        json={"content": "你好"},
        headers=headers
    )
    assert msg1_resp.status_code == 200
    data1 = msg1_resp.json()
    assert data1["stage"] == "greeting"
    
    # 4. 第二轮对话 - 描述症状
    msg2_resp = client.post(
        f"/sessions/{session_id}/messages",
        json={"content": "我手臂有红疹，很痒"},
        headers=headers
    )
    data2 = msg2_resp.json()
    assert data2["stage"] in ["collecting", "diagnosing"]
    assert "specialty_data" in data2
    
    # 5. 第三轮对话 - 补充症状
    msg3_resp = client.post(
        f"/sessions/{session_id}/messages",
        json={"content": "还有脱皮现象"},
        headers=headers
    )
    data3 = msg3_resp.json()
    
    # 6. 验证诊断卡出现
    if data3["stage"] == "diagnosing":
        assert data3["specialty_data"] is not None
        assert "diagnosis_card" in data3["specialty_data"]
    
    print("✅ 皮肤科完整流程测试通过")
```

**Step 2: 运行测试**

```bash
pytest tests/e2e/test_dermatology_flow.py -v -s
```

Expected: PASS

**Step 3: 提交**

```bash
git add tests/e2e/test_dermatology_flow.py
git commit -m "test: add e2e test for dermatology flow"
```

---

### Task 12: iOS 手动测试清单

**Files:**
- Create: `docs/testing/ios-manual-test-checklist.md`

**Step 1: 创建测试清单**

```markdown
# iOS 手动测试清单

## 皮肤科问诊流程

### 前置条件
- [ ] 已登录测试账号
- [ ] 后端服务运行正常 (http://localhost:8100)

### 测试步骤

#### 1. 创建会话
- [ ] 点击"皮肤科问诊"
- [ ] 验证：进入对话界面
- [ ] 验证：显示问候消息

#### 2. 症状描述
- [ ] 输入："我手臂有红疹，很痒"
- [ ] 验证：AI 回复收集症状
- [ ] 验证：快捷选项显示"继续描述"、"上传照片"

#### 3. 补充症状
- [ ] 输入："还有脱皮现象"
- [ ] 验证：进度条更新
- [ ] 验证：症状列表显示（如果有 SpecialtyDataView）

#### 4. 诊断卡显示
- [ ] 继续描述症状直到诊断
- [ ] 验证：诊断卡出现
- [ ] 验证：显示诊断摘要
- [ ] 验证：快捷选项包含"生成病历"

#### 5. 图像上传（如果实现）
- [ ] 点击"上传照片"
- [ ] 选择图片
- [ ] 验证：图片上传成功
- [ ] 验证：AI 分析图片

### 预期结果
- ✅ 所有步骤正常完成
- ✅ UI 响应流畅
- ✅ 数据显示正确
- ✅ 无崩溃或错误

### 测试人员
- 姓名: _______
- 日期: _______
- 结果: ✅ 通过 / ❌ 失败
```

**Step 2: 提交**

```bash
git add docs/testing/ios-manual-test-checklist.md
git commit -m "docs: add iOS manual test checklist"
```

---

## 总结与下一步

### 完成标志

Phase 1-5 完成后，你应该有：

✅ **后端**
- 统一响应格式 (`AgentResponse`)
- 智能体基类 (`BaseAgent`)
- 智能体路由器 (`AgentRouterV2`)
- 重构后的皮肤科智能体
- 废弃旧版 `/derma` 路由

✅ **iOS**
- 新的 `ConversationViewModel`
- `AgentResponse` 模型
- `SpecialtyDataView` 动态渲染

✅ **文档**
- 架构设计文档
- API 契约更新
- 测试清单

✅ **测试**
- 单元测试覆盖核心模块
- 端到端测试验证流程

### 下一步计划

1. **新增心血管科智能体**（1-2天）
   - 实现 `CardiologyAgent`
   - 添加心电图解读功能
   - iOS 添加心血管科组件

2. **完善皮肤科功能**（2-3天）
   - 集成真实的 LLM 生成
   - 实现图像分析
   - 优化诊断逻辑

3. **性能优化**（1-2天）
   - 添加缓存
   - 优化数据库查询
   - 流式响应优化

4. **删除旧代码**（1天）
   - 完全移除 `/derma` 路由
   - 清理 `DermaSession` 模型
   - 更新所有文档

---

**预计总时间**: 10-12 个工作日

**关键里程碑**:
- Day 3: Phase 1 完成（基础架构）
- Day 6: Phase 2 完成（皮肤科重构）
- Day 8: Phase 3 完成（iOS 适配）
- Day 9: Phase 4 完成（清理文档）
- Day 10: Phase 5 完成（测试验证）
