# ReAct 智能体架构设计文档

> **创建日期:** 2026-01-20  
> **状态:** 已确认，待实施

## 1. 设计目标

将现有的"伪智能体"（硬编码规则 + AI 文本生成）重构为**真正的 ReAct Agent**，让 AI 自主决策、调用工具、判断信息充分性。

### 核心改变

| 维度 | 现有实现 | ReAct 实现 |
|------|----------|-----------|
| **决策逻辑** | 硬编码 if-else | AI 输出结构化 JSON |
| **症状提取** | 关键词匹配 | AI 自己维护 medical_context |
| **流程控制** | 固定状态机 | AI 自主循环（Observe→Think→Act） |
| **工具调用** | 无 | 5个工具（知识/风险/图像/病历/药物） |
| **终止条件** | `len(symptoms) >= 3` | AI 判断信息充分性 |
| **LLM** | 通义千问（仅文本生成） | 通义千问（Function Calling） + qwen-vl |

---

## 2. 核心架构

### 2.1 ReAct 循环

```
┌─────────────────────────────────────────────────────────┐
│                    ReAct 循环                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ Observe  │ →  │  Think   │ →  │   Act    │          │
│  │ 观察输入  │    │ 推理决策  │    │ 执行工具  │          │
│  └──────────┘    └──────────┘    └──────────┘          │
│       ↑                                  │              │
│       └──────────────────────────────────┘              │
│                    循环直到 AI 判断完成                   │
└─────────────────────────────────────────────────────────┘
```

**核心流程：**
1. **Observe**：接收用户输入（文字/图片）
2. **Think**：AI 分析当前状态，输出结构化 JSON 决定下一步
3. **Act**：调用工具（查知识库/分析图片/评估风险等）
4. **循环**：直到 AI 决定 `{"action": "respond", "ready_to_diagnose": true}`

### 2.2 LangGraph 状态图

```
START
  ↓
[agent_reasoning]  ← AI 推理节点（调用通义千问 + Function Calling）
  ↓
[should_continue?]  ← 条件判断：AI 决定的 action 是什么？
  ↓
  ├─→ "use_tool" → [tool_executor] → 回到 [agent_reasoning]
  ├─→ "respond" → [generate_response] → END
  └─→ "diagnose" → [generate_diagnosis] → END
```

---

## 3. 工具定义

### 3.1 工具列表

| 工具 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `search_medical_knowledge` | 查询医学知识库 | query, specialty | 医学知识文本 |
| `assess_risk` | 评估疾病风险等级 | symptoms, patient_info | risk_level, score |
| `analyze_skin_image` | 分析皮肤图像 | image_base64, context | findings, conditions |
| `generate_medical_dossier` | 生成结构化病历 | patient_data | dossier_id, content |
| `search_medication` | 查询推荐用药 | condition, contraindications | medications, warnings |

### 3.2 工具接口

```python
@tool
def search_medical_knowledge(query: str, specialty: str = "dermatology") -> str:
    """查询医学知识库"""
    pass

@tool
def assess_risk(symptoms: List[str], patient_info: dict) -> dict:
    """评估疾病风险等级"""
    pass

@tool
def analyze_skin_image(image_base64: str, context: str) -> dict:
    """分析皮肤图像（调用 qwen-vl）"""
    pass

@tool
def generate_medical_dossier(patient_data: dict) -> dict:
    """生成结构化病历"""
    pass

@tool
def search_medication(condition: str, contraindications: List[str]) -> dict:
    """查询推荐用药"""
    pass
```

---

## 4. AI 决策格式

AI 通过 Function Calling 输出结构化 JSON：

### 4.1 调用工具

```json
{
  "thought": "患者描述了红疹和瘙痒，需要查询湿疹的典型症状来对比",
  "action": "use_tool",
  "tool": "search_medical_knowledge",
  "tool_input": {
    "query": "湿疹的典型症状和好发部位",
    "specialty": "dermatology"
  }
}
```

### 4.2 继续追问

```json
{
  "thought": "已知症状：红疹、瘙痒。缺少关键信息：部位、持续时间、诱因",
  "action": "respond",
  "response": "请问红疹主要出现在身体哪个部位？持续多长时间了？",
  "quick_options": ["手臂", "腿部", "躯干", "全身多处"],
  "medical_context_update": {
    "symptoms": ["红疹", "瘙痒"],
    "missing_info": ["部位", "持续时间", "诱因"]
  }
}
```

### 4.3 进入诊断

```json
{
  "thought": "已收集充分信息，症状符合接触性皮炎，可以进行诊断",
  "action": "diagnose",
  "ready_reason": "症状描述完整，有明确诱因，符合诊断标准"
}
```

---

## 5. 状态定义

```python
class ReActAgentState(TypedDict):
    # 会话标识
    session_id: str
    user_id: int
    agent_type: str
    
    # 对话历史（LangGraph 管理）
    messages: Annotated[List, add_messages]
    
    # AI 决策输出
    agent_decision: dict  # AI 的结构化决策
    
    # 工具调用
    tool_results: List[dict]  # 工具返回结果
    pending_tool_calls: List[dict]  # 待执行的工具调用
    
    # 医学上下文（AI 自己维护）
    medical_context: dict
    
    # 响应输出
    current_response: str
    quick_options: List[str]
    
    # 附件
    attachments: List[dict]
```

---

## 6. 实施计划

### 阶段1：基础设施

1. **扩展 QwenService**
   - 添加 `chat_with_tools()` 方法支持 Function Calling
   - 定义工具 schema

2. **实现5个工具**
   - 创建 `backend/app/services/agents/tools/` 目录
   - 实现各工具的基础版本

3. **创建 ReActAgent 基类**
   - 实现 ReAct 循环逻辑
   - 处理工具调用和结果

### 阶段2：皮肤科智能体重构

1. **创建 DermatologyReActAgent**
   - 继承 ReActAgent 基类
   - 配置皮肤科专用 prompt 和工具

2. **删除硬编码逻辑**
   - 移除 `_decide_next_node` 中的 if-else
   - 移除 `symptom_keywords` 匹配逻辑

### 阶段3：测试和验证

1. **单元测试**
   - 测试各工具独立功能
   - 测试 ReAct 循环正确性

2. **集成测试**
   - 端到端测试问诊流程
   - 验证 AI 决策质量

---

## 7. 文件结构

```
backend/app/services/agents/
├── __init__.py
├── base.py                    # 现有基类（保留）
├── react_base.py              # 新增：ReAct 基类
├── router.py
├── tools/                     # 新增：工具目录
│   ├── __init__.py
│   ├── knowledge.py           # search_medical_knowledge
│   ├── risk.py                # assess_risk
│   ├── image.py               # analyze_skin_image
│   ├── dossier.py             # generate_medical_dossier
│   └── medication.py          # search_medication
├── dermatology/
│   ├── __init__.py
│   ├── agent.py               # 现有实现（保留作为降级）
│   └── react_agent.py         # 新增：ReAct 版本
├── cardiology/
├── general/
└── orthopedics/
```

---

## 8. 风险控制

1. **保留旧代码**：ReAct 版本并行运行，可随时回退
2. **日志记录**：记录所有 AI 的 `thought`，便于调试和审计
3. **成本监控**：监控 token 消耗，设置单次对话上限
4. **降级策略**：工具调用失败时，AI 可选择继续文字问诊

---

## 9. 验收标准

- [ ] AI 自主决定何时追问、何时诊断（无硬编码阈值）
- [ ] AI 能正确调用工具并使用结果
- [ ] 删除所有 `if len(symptoms) >= 3` 类型的判断
- [ ] 图像分析通过工具调用（而非硬编码节点）
- [ ] 医学上下文由 AI 自己维护
- [ ] 基础测试通过
