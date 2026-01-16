# 多智能体医疗问诊系统架构设计 V2.0

**版本**: V2.0  
**设计日期**: 2026-01-17  
**状态**: 生产就绪  
**设计原则**: 简单实用、渐进式重构、避免过度设计

---

## 一、架构概览

### 1.1 设计目标

- ✅ 统一后端接口，废弃旧版 `/derma` 专用路由
- ✅ 支持多科室智能体扩展（皮肤科、心血管科、骨科等）
- ✅ 前后端解耦，通过统一响应格式实现灵活渲染
- ✅ 简单可测试，避免复杂的插件系统和元编程
- ✅ 渐进式迁移，不推倒重来

### 1.2 系统分层

```
┌─────────────────────────────────────────────────────────┐
│                   客户端层 (iOS/Web)                      │
│  - SwiftUI 视图                                          │
│  - ConversationViewModel (通用会话管理)                   │
│  - 专科数据解析 (switch specialtyData)                    │
└─────────────────────────────────────────────────────────┘
                         ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────┐
│                   统一路由层 (sessions.py)                │
│  - POST /sessions (创建会话)                             │
│  - POST /sessions/{id}/messages (发送消息)               │
│  - GET /sessions/{id}/messages (获取历史)                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              智能体路由器 (agent_router.py)               │
│  - 硬编码映射表: agent_type → Agent 类                    │
│  - 能力配置: actions, accepts_media                      │
│  - 简单工厂模式，无动态发现                                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   智能体层 (Agents)                       │
│  BaseAgent (抽象基类)                                     │
│  ├── DermatologyAgent (皮肤科)                           │
│  ├── CardiologyAgent (心血管科)                          │
│  ├── OrthopedicsAgent (骨科)                             │
│  └── GeneralAgent (通用)                                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   数据持久化层                            │
│  - Session (会话表)                                      │
│  - Message (消息表)                                      │
│  - agent_state: JSON 字段存储智能体状态                   │
└─────────────────────────────────────────────────────────┘
```

---

## 二、核心设计

### 2.1 统一响应协议

**设计原则**: 所有智能体返回统一格式，专科数据通过 `specialty_data` 扩展字段承载

```python
# backend/app/schemas/agent_response.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class AgentResponse(BaseModel):
    """统一智能体响应格式"""
    
    # ========== 基础字段（所有智能体必填） ==========
    message: str = Field(..., description="AI 回复内容")
    stage: str = Field(..., description="当前阶段: greeting, collecting, diagnosing, completed")
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    
    # ========== 可选字段 ==========
    quick_options: List[str] = Field(default=[], description="快捷回复选项")
    risk_level: Optional[str] = Field(None, description="风险等级: low, medium, high, emergency")
    
    # 病历事件相关
    event_id: Optional[str] = Field(None, description="关联的病历事件ID")
    is_new_event: bool = Field(False, description="是否创建了新病历事件")
    should_show_dossier_prompt: bool = Field(False, description="是否提示生成病历")
    
    # ========== 专科扩展数据（自由 JSON） ==========
    specialty_data: Optional[Dict[str, Any]] = Field(
        None,
        description="专科特有数据，例如: {'diagnosis_card': {...}, 'advice_history': [...]}"
    )
    
    # ========== 状态持久化 ==========
    next_state: Dict[str, Any] = Field(
        default={},
        description="下次调用需要的状态（会保存到 Session.agent_state）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "根据您的描述，可能是湿疹引起的瘙痒",
                "stage": "diagnosing",
                "progress": 80,
                "quick_options": ["继续描述", "上传照片", "生成病历"],
                "risk_level": "low",
                "specialty_data": {
                    "diagnosis_card": {
                        "summary": "手臂湿疹",
                        "conditions": [
                            {"name": "湿疹", "confidence": 0.85}
                        ]
                    },
                    "advice_history": [
                        {
                            "title": "护理建议",
                            "content": "保持皮肤清洁干燥"
                        }
                    ]
                },
                "next_state": {
                    "stage": "diagnosing",
                    "symptoms": ["瘙痒", "红疹"],
                    "questions_asked": 3
                }
            }
        }
```

**关键设计点**:
- `specialty_data` 是自由 JSON，不做强类型约束
- 皮肤科放 `diagnosis_card`、`advice_history`
- 心血管科放 `ecg_analysis`、`risk_assessment`
- iOS 根据 key 判断如何渲染

### 2.2 智能体基类

**设计原则**: 最小化抽象，只定义必须实现的方法

```python
# backend/app/services/base/base_agent.py
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
            attachments: 附件列表 [{"type": "image", "base64": "..."}]
            action: 动作类型 (conversation, analyze_skin, interpret_report)
            on_chunk: 流式输出回调函数
            
        Returns:
            AgentResponse: 统一响应格式
        """
        pass
```

**就这一个方法！** 不需要：
- ❌ `get_capabilities()` - 能力配置直接写在 AgentRouter 里
- ❌ `create_initial_state()` - 第一次调用时 state 为空字典
- ❌ `validate_input()` - 在 `run()` 方法内部自己校验

### 2.3 智能体路由器

**设计原则**: 硬编码映射表，不使用装饰器、自动扫描等复杂机制

```python
# backend/app/services/agent_router.py
from typing import Dict, Type
from .base.base_agent import BaseAgent
from .dermatology.agent import DermatologyAgent
from .cardiology.agent import CardiologyAgent
from .general.agent import GeneralAgent

class AgentRouter:
    """智能体路由器 - 简单的工厂模式"""
    
    # ========== 硬编码注册表 ==========
    _AGENTS: Dict[str, Type[BaseAgent]] = {
        "dermatology": DermatologyAgent,
        "cardiology": CardiologyAgent,
        "general": GeneralAgent,
        # 新增科室在此添加
    }
    
    # ========== 能力配置（给前端查询用） ==========
    _CAPABILITIES: Dict[str, Dict] = {
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
        "general": {
            "display_name": "全科AI医生",
            "description": "通用医疗咨询",
            "actions": ["conversation"],
            "accepts_media": [],
        },
    }
    
    # ========== 科室映射表 ==========
    _DEPARTMENT_MAPPING: Dict[str, str] = {
        "皮肤科": "dermatology",
        "皮肤性病科": "dermatology",
        "心内科": "cardiology",
        "心血管内科": "cardiology",
        "骨科": "orthopedics",
        # 新增科室映射在此添加
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

**新增科室流程**:
1. 实现新的 Agent 类（继承 BaseAgent）
2. 在 `_AGENTS` 添加一行: `"orthopedics": OrthopedicsAgent`
3. 在 `_CAPABILITIES` 添加能力配置
4. 在 `_DEPARTMENT_MAPPING` 添加科室映射

### 2.4 智能体实现示例

```python
# backend/app/services/dermatology/agent.py
from ..base.base_agent import BaseAgent
from ...schemas.agent_response import AgentResponse
from typing import Dict, Any, List, Optional, Callable

class DermatologyAgent(BaseAgent):
    """皮肤科智能体"""
    
    def __init__(self):
        # 初始化工具（LLM、知识库等）
        from ..qwen_service import QwenService
        from ..qwen_vl_service import QwenVLService
        self.llm = QwenService()
        self.vision_llm = QwenVLService()
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str,
        attachments: List[Dict[str, Any]] = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> AgentResponse:
        """执行皮肤科问诊流程"""
        
        # 1. 从 state 恢复上下文
        stage = state.get("stage", "greeting")
        symptoms = state.get("symptoms", [])
        questions_asked = state.get("questions_asked", 0)
        
        # 2. 根据 action 分发到不同处理流程
        if action == "analyze_skin":
            return await self._analyze_skin_image(state, attachments, on_chunk)
        elif action == "interpret_report":
            return await self._interpret_report(state, attachments, on_chunk)
        else:
            return await self._conversation(state, user_input, on_chunk)
    
    async def _conversation(
        self,
        state: Dict[str, Any],
        user_input: str,
        on_chunk: Optional[Callable]
    ) -> AgentResponse:
        """对话问诊流程"""
        
        # 提取症状
        new_symptoms = await self._extract_symptoms(user_input)
        symptoms = state.get("symptoms", [])
        symptoms.extend(new_symptoms)
        
        # 判断阶段
        if len(symptoms) < 3:
            stage = "collecting"
            progress = len(symptoms) * 20
        else:
            stage = "diagnosing"
            progress = 80
        
        # 生成回复
        prompt = self._build_prompt(state, user_input, symptoms)
        message = await self._generate_response(prompt, on_chunk)
        
        # 构建专科数据
        specialty_data = None
        if stage == "diagnosing":
            diagnosis_card = await self._generate_diagnosis_card(symptoms)
            specialty_data = {
                "diagnosis_card": diagnosis_card,
                "symptoms": symptoms
            }
        
        return AgentResponse(
            message=message,
            stage=stage,
            progress=progress,
            quick_options=["继续描述", "上传照片", "生成病历"] if stage == "diagnosing" else ["继续描述"],
            risk_level="low",
            specialty_data=specialty_data,
            next_state={
                "stage": stage,
                "symptoms": symptoms,
                "questions_asked": state.get("questions_asked", 0) + 1
            }
        )
    
    async def _analyze_skin_image(self, state, attachments, on_chunk):
        """皮肤图像分析"""
        if not attachments:
            raise ValueError("皮肤分析需要上传图片")
        
        # 调用视觉大模型
        analysis = await self.vision_llm.analyze_skin(attachments[0])
        
        return AgentResponse(
            message=f"图像分析完成：{analysis['summary']}",
            stage="analyzing",
            progress=70,
            specialty_data={
                "image_analysis": analysis
            },
            next_state=state
        )
```

---

## 三、iOS 客户端架构

### 3.1 通用会话层

```swift
// ios/xinlingyisheng/xinlingyisheng/ViewModels/ConversationViewModel.swift

import Foundation
import Combine

@MainActor
class ConversationViewModel: ObservableObject {
    // ========== 通用状态 ==========
    @Published var sessionId: String?
    @Published var agentType: AgentType?
    @Published var messages: [Message] = []
    @Published var isLoading = false
    
    // 从 AgentResponse 映射的通用字段
    @Published var stage: String = "greeting"
    @Published var progress: Int = 0
    @Published var quickOptions: [String] = []
    @Published var riskLevel: String?
    
    // ========== 专科数据（原始 JSON） ==========
    @Published var specialtyData: [String: Any]?
    
    private let apiService = APIService.shared
    
    func sendMessage(
        content: String,
        attachments: [MessageAttachment] = [],
        action: AgentAction = .conversation
    ) async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            // 发送消息，接收 AgentResponse
            let response = try await apiService.sendUnifiedMessageStreaming(
                sessionId: sessionId!,
                content: content,
                attachments: attachments,
                action: action
            )
            
            // 更新通用状态
            self.stage = response.stage
            self.progress = response.progress
            self.quickOptions = response.quickOptions
            self.riskLevel = response.riskLevel
            
            // 保存专科数据（不解析，交给视图层处理）
            self.specialtyData = response.specialtyData
            
        } catch {
            print("[ConversationVM] Error: \(error)")
        }
    }
}
```

### 3.2 视图层处理专科数据

```swift
// ios/xinlingyisheng/xinlingyisheng/Views/ConversationView.swift

struct ConversationView: View {
    @StateObject var viewModel = ConversationViewModel()
    
    var body: some View {
        VStack {
            // 消息列表
            ScrollView {
                ForEach(viewModel.messages) { message in
                    MessageBubble(message: message)
                }
                
                // 根据 specialtyData 渲染专科组件
                if let specialtyData = viewModel.specialtyData {
                    SpecialtyDataView(data: specialtyData)
                }
            }
            
            // 快捷选项
            if !viewModel.quickOptions.isEmpty {
                QuickOptionsBar(options: viewModel.quickOptions) { option in
                    await viewModel.sendMessage(content: option)
                }
            }
            
            // 输入框
            MessageInputBar(onSend: { content in
                await viewModel.sendMessage(content: content)
            })
        }
        .navigationTitle(viewModel.agentType?.displayName ?? "AI问诊")
    }
}

// 专科数据渲染器
struct SpecialtyDataView: View {
    let data: [String: Any]
    
    var body: some View {
        VStack(spacing: 12) {
            // 皮肤科数据
            if let diagnosisCard = data["diagnosis_card"] as? [String: Any] {
                DiagnosisCardView(data: diagnosisCard)
            }
            
            if let adviceHistory = data["advice_history"] as? [[String: Any]] {
                ForEach(adviceHistory, id: \.self) { advice in
                    AdviceCardView(data: advice)
                }
            }
            
            // 心血管科数据
            if let ecgAnalysis = data["ecg_analysis"] as? [String: Any] {
                ECGAnalysisView(data: ecgAnalysis)
            }
            
            if let riskAssessment = data["risk_assessment"] as? [String: Any] {
                RiskAssessmentView(data: riskAssessment)
            }
        }
    }
}
```

**关键设计点**:
- `ConversationViewModel` 只管理通用状态
- `specialtyData` 保持原始 JSON 格式
- 视图层用简单的 `if let` 判断渲染对应组件
- 新增科室只需添加一个 `if let` 分支

---

## 四、目录结构

```
backend/app/
├── routes/
│   └── sessions.py                  # 统一路由（保留）
├── services/
│   ├── base/
│   │   └── base_agent.py            # 智能体基类（1个方法）
│   ├── agent_router.py              # 智能体路由器（硬编码映射表）
│   ├── dermatology/
│   │   └── agent.py                 # 皮肤科智能体
│   ├── cardiology/
│   │   └── agent.py                 # 心血管科智能体
│   ├── orthopedics/
│   │   └── agent.py                 # 骨科智能体
│   └── general/
│       └── agent.py                 # 通用智能体
├── schemas/
│   └── agent_response.py            # 统一响应格式
└── models/
    ├── session.py                   # Session.agent_state 存储状态
    └── message.py

ios/xinlingyisheng/xinlingyisheng/
├── ViewModels/
│   └── ConversationViewModel.swift  # 通用会话层
├── Views/
│   ├── ConversationView.swift       # 主视图
│   └── Components/
│       ├── MessageBubble.swift
│       ├── DiagnosisCardView.swift  # 皮肤科组件
│       ├── AdviceCardView.swift
│       ├── ECGAnalysisView.swift    # 心血管科组件
│       └── RiskAssessmentView.swift
└── Models/
    ├── AgentResponse.swift          # 响应模型
    └── Message.swift
```

---

## 五、迁移计划

### Phase 1: 基础架构（2-3天）

**目标**: 建立新架构基础，不影响现有功能

1. **创建统一响应格式**
   - 创建 `schemas/agent_response.py`
   - 定义 `AgentResponse` 模型
   - 编写单元测试

2. **创建智能体基类**
   - 创建 `services/base/base_agent.py`
   - 定义 `BaseAgent` 抽象类
   - 只包含 `run()` 一个方法

3. **创建智能体路由器**
   - 创建 `services/agent_router.py`
   - 硬编码注册表和能力配置
   - 保留原有的 `infer_agent_type()` 逻辑

**验收标准**:
- ✅ 新旧代码可以并存
- ✅ 所有测试通过
- ✅ 不影响现有功能

### Phase 2: 重构皮肤科智能体（3-4天）

**目标**: 将现有 DermatologyAgent 迁移到新架构

1. **重构智能体实现**
   - 让 `DermatologyAgent` 继承 `BaseAgent`
   - 实现 `run()` 方法，返回 `AgentResponse`
   - 保持原有业务逻辑不变

2. **修改路由层**
   - `sessions.py` 使用 `AgentRouter.get_agent()`
   - 处理 `AgentResponse` 格式
   - 保持 SSE 流式响应

3. **测试验证**
   - 端到端测试皮肤科问诊流程
   - 验证诊断卡、建议等功能正常
   - 性能测试（响应时间不变）

**验收标准**:
- ✅ 皮肤科功能完全正常
- ✅ iOS 客户端无需修改
- ✅ 响应格式符合 `AgentResponse`

### Phase 3: iOS 适配（2-3天）

**目标**: iOS 客户端适配新响应格式

1. **更新数据模型**
   - 创建 `AgentResponse.swift`
   - 解析 `specialty_data` 字段

2. **重构 ViewModel**
   - 重命名 `UnifiedChatViewModel` → `ConversationViewModel`
   - 移除硬编码的专科字段
   - 添加 `specialtyData` 属性

3. **更新视图层**
   - 创建 `SpecialtyDataView`
   - 用 `if let` 判断渲染对应组件
   - 保持 UI 外观不变

**验收标准**:
- ✅ iOS 功能完全正常
- ✅ UI 外观与之前一致
- ✅ 代码更清晰易维护

### Phase 4: 清理旧代码（1天）

**目标**: 删除废弃代码，完成迁移

1. **删除旧路由**
   - 删除 `routes/derma.py`
   - 删除 `DermaSession` 模型
   - 更新文档

2. **更新文档**
   - 更新 `API_CONTRACT.md`
   - 更新 `README.md`
   - 添加迁移说明

**验收标准**:
- ✅ 旧代码完全删除
- ✅ 文档更新完成
- ✅ 所有测试通过

### Phase 5: 新增心血管科（2-3天）

**目标**: 验证架构扩展性

1. **实现心血管科智能体**
   - 创建 `services/cardiology/agent.py`
   - 实现心电图解读功能
   - 在 `AgentRouter` 注册

2. **iOS 添加心血管科组件**
   - 创建 `ECGAnalysisView`
   - 在 `SpecialtyDataView` 添加渲染逻辑

3. **端到端测试**
   - 测试心血管科问诊流程
   - 验证心电图解读功能

**验收标准**:
- ✅ 心血管科功能正常
- ✅ 新增科室成本低（< 1天）
- ✅ 架构扩展性验证通过

---

## 六、技术决策记录

### 决策 1: 使用硬编码注册表而非装饰器

**背景**: 需要注册多个智能体

**选项**:
- A. 装饰器 + 自动扫描
- B. 硬编码映射表

**决策**: 选择 B（硬编码映射表）

**理由**:
- ✅ 简单直观，一目了然
- ✅ 易于测试和调试
- ✅ 不需要复杂的元编程
- ✅ 发布前可完全测试，无运行时发现

### 决策 2: specialty_data 使用自由 JSON 而非强类型

**背景**: 不同科室需要不同的数据结构

**选项**:
- A. 为每个科室定义专门的 Schema
- B. 使用自由 JSON 字段

**决策**: 选择 B（自由 JSON）

**理由**:
- ✅ 灵活性高，易于扩展
- ✅ 前后端解耦
- ✅ 新增科室无需修改基础 Schema
- ⚠️ 缺点: 类型安全性降低（可通过文档和测试弥补）

### 决策 3: BaseAgent 只定义一个 run() 方法

**背景**: 需要定义智能体接口

**选项**:
- A. 定义多个抽象方法（get_capabilities, create_state, validate_input 等）
- B. 只定义一个 run() 方法

**决策**: 选择 B（一个方法）

**理由**:
- ✅ 最小化抽象，降低复杂度
- ✅ 子类实现更灵活
- ✅ 能力配置在 AgentRouter 统一管理
- ✅ 状态管理用普通字典，无需专门的 State 类

### 决策 4: iOS 不做复杂分层

**背景**: 需要处理专科数据

**选项**:
- A. 创建 Extension 层（DermatologyExtension, CardiologyExtension）
- B. 视图层直接用 if-let 判断

**决策**: 选择 B（视图层判断）

**理由**:
- ✅ 简单直观，代码集中
- ✅ 新增科室只需添加一个 if-let
- ✅ 避免过度抽象
- ⚠️ 缺点: 视图层代码稍多（可接受）

---

## 七、风险与应对

### 风险 1: 迁移过程中功能回归

**应对**:
- 保持新旧代码并存，渐进式迁移
- 每个 Phase 完成后进行完整测试
- 保留回滚能力（Git 分支管理）

### 风险 2: specialty_data 缺少类型约束

**应对**:
- 在 `API_CONTRACT.md` 详细定义各科室数据格式
- 编写集成测试验证数据结构
- iOS 解析时做防御性编程（可选绑定）

### 风险 3: 性能影响

**应对**:
- 在 Phase 2 进行性能基准测试
- 监控响应时间和内存使用
- 必要时优化序列化/反序列化逻辑

---

## 八、成功指标

### 代码质量
- ✅ 后端核心代码 < 500 行（base_agent.py + agent_router.py）
- ✅ 新增科室成本 < 1 天
- ✅ 单元测试覆盖率 > 80%

### 功能完整性
- ✅ 所有现有功能正常
- ✅ 皮肤科、心血管科问诊流程完整
- ✅ iOS UI 与之前一致

### 可维护性
- ✅ 新人能在 1 小时内理解架构
- ✅ 文档完整清晰
- ✅ 代码结构清晰，易于调试

---

## 九、相关文档

- [API 契约文档](../API_CONTRACT.md)
- [开发规范](../DEVELOPMENT_GUIDELINES.md)
- [iOS 开发指南](../IOS_DEVELOPMENT_GUIDE.md)

---

**文档维护者**: 项目团队  
**最后更新**: 2026-01-17  
**下次审查**: 每个 Phase 完成后更新
