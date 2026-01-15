# 皮肤科智能体重构设计

> 基于 LangGraph ReAct 模式，实现自然对话、渐进式诊断、RAG 增强的医疗智能体

## 1. 背景与目标

### 1.1 当前问题

| 问题 | 影响 |
|------|------|
| 固定的 greeting 节点 | 用户说"你好，我脸上长痘"也返回问候语 |
| 基于关键词判断诊断时机 | "帮我看看"触发诊断，缺乏语义理解 |
| 状态机模式 | greeting → collecting → diagnosis 固定流程 |
| 快捷选项固定 | 不能根据对话上下文动态生成 |
| 缺乏知识来源标注 | 无法展示专业文献支持 |

### 1.2 竞品分析（廖院士皮肤科智能体）

**核心功能亮点**：
1. **自然对话** - 用户直接描述问题，不返回问候语
2. **渐进式诊断** - 边问诊边给初步建议，不等信息收集完
3. **院士团队解读** - RAG 检索知识库，标注文献来源
4. **动态快捷选项** - 根据当前问题生成相关选项

### 1.3 设计目标

- **自然对话**：像真人医生一样灵活响应
- **渐进式诊断**：随时可以给建议，随时可以继续追问
- **知识增强**：调用专业知识库，标注来源
- **动态选项**：根据对话上下文生成快捷回复
- **API 兼容**：保持现有接口不变

## 2. 技术选型

### 2.1 LangGraph ReAct 模式

根据 [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch/)，ReAct Agent 的核心模式：

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
┌──────▼──────┐
│   agent     │ ← 调用 LLM（带工具绑定）
└──────┬──────┘
       │
       ▼
  should_continue?
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐  ┌─────┐
│tools│  │ END │
└──┬──┘  └─────┘
   │
   └────────► agent（循环）
```

**核心机制**：
- LLM 通过 `bind_tools()` 知道可用工具
- LLM 返回 `tool_calls` 时，执行工具并返回结果
- 工具结果作为 `ToolMessage` 传回 LLM
- LLM 再次决策，形成 Reasoning-Action 循环

### 2.2 为什么选择 ReAct 模式

| 维度 | 状态机模式（当前） | ReAct 模式（新设计） |
|------|------------------|---------------------|
| 决策方式 | 硬编码规则 | LLM 自主决策 |
| 流程灵活性 | 固定阶段 | 动态流转 |
| 工具调用 | 预定义时机 | LLM 按需调用 |
| 扩展性 | 改代码 | 加工具 |

## 3. 核心架构设计

### 3.1 状态图设计

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   agent     │ ← 核心：LLM + 工具绑定
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │should_continue│
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌──────▼──────┐   ┌─────▼─────┐
    │   tools   │   │    END      │   │(其他工具) │
    └─────┬─────┘   └─────────────┘   └─────┬─────┘
          │                                 │
          └─────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   agent     │ ← 循环回到 agent
                    └─────────────┘
```

### 3.2 工具设计

定义四个核心工具，LLM 根据对话需要自主调用：

```python
@tool
def analyze_skin_image(image_base64: str, chief_complaint: str) -> dict:
    """分析皮肤图片，识别皮损特征"""
    pass

@tool
def search_medical_knowledge(query: str, disease_type: str) -> dict:
    """检索皮肤科专业知识库，返回相关文献和建议"""
    pass

@tool
def generate_diagnosis(symptoms: List[str], location: str, duration: str) -> dict:
    """生成初步诊断建议，包括鉴别诊断和护理建议"""
    pass

@tool
def interpret_report(report_text: str, report_type: str) -> dict:
    """解读医学检验报告"""
    pass
```

### 3.3 状态定义

```python
from typing import TypedDict, List, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class DermaAgentState(TypedDict):
    """皮肤科智能体状态"""
    # === 会话标识 ===
    session_id: str
    user_id: int
    
    # === 对话历史（LangGraph 自动管理）===
    messages: Annotated[List[BaseMessage], add_messages]
    
    # === 医学信息（LLM 提取并累积）===
    chief_complaint: str           # 主诉
    skin_location: str             # 皮损部位
    symptoms: List[str]            # 症状列表
    duration: str                  # 持续时间
    
    # === 分析结果 ===
    skin_analyses: List[dict]      # 图片分析历史
    knowledge_refs: List[dict]     # 知识库引用
    possible_conditions: List[dict] # 可能的诊断
    
    # === 输出控制 ===
    current_response: str          # 当前回复
    quick_options: List[dict]      # 动态快捷选项
    
    # === 待处理附件 ===
    pending_attachments: List[dict]
    
    # === 诊断相关 ===
    risk_level: str                # low/medium/high/emergency
    care_advice: str               # 护理建议
    need_offline_visit: bool       # 是否需要线下就诊
```

## 4. 核心节点实现

### 4.1 Agent 节点（核心）

```python
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

# System Prompt - 定义医生角色和行为
DERMA_SYSTEM_PROMPT = """你是一位经验丰富的皮肤科专家医生，正在与患者进行问诊对话。

## 角色定位
- 专业但亲和，用通俗易懂的语言解释医学概念
- 像真人医生一样自然对话，不使用固定模板

## 对话原则
1. **直接响应**：用户描述问题，直接回应，不要先问候
2. **渐进式诊断**：边问诊边给初步建议，不等信息收集完
3. **主动追问**：每次回复后追问 1-2 个关键问题
4. **工具调用**：需要时主动调用工具（图片分析、知识库检索）

## 信息收集要点
- 主诉：什么问题
- 部位：身体哪个位置
- 症状：红肿、瘙痒、疼痛、脱皮等
- 持续时间：多久了
- 诱因：可能的原因

## 输出要求
1. 回复要自然、简洁（2-4句话）
2. 每次回复后生成 3-4 个快捷选项供用户选择
3. 识别危急情况（如蜂窝织炎、带状疱疹）立即建议就医

## 可用工具
- analyze_skin_image: 分析皮肤图片
- search_medical_knowledge: 检索专业知识库
- generate_diagnosis: 生成诊断建议
- interpret_report: 解读检验报告

根据对话需要，自主决定是否调用工具。"""

def call_model(state: DermaAgentState, config: RunnableConfig):
    """Agent 核心节点：调用 LLM 进行对话和决策"""
    system_message = SystemMessage(content=DERMA_SYSTEM_PROMPT)
    
    # 构建上下文信息
    context = f"""
当前问诊信息：
- 主诉: {state.get('chief_complaint') or '未明确'}
- 部位: {state.get('skin_location') or '未明确'}
- 症状: {', '.join(state.get('symptoms', [])) or '未明确'}
- 持续时间: {state.get('duration') or '未明确'}
"""
    
    # 如果有待处理附件，添加提示
    if state.get('pending_attachments'):
        context += "\n⚠️ 用户上传了图片，请调用 analyze_skin_image 工具进行分析。"
    
    # 调用 LLM
    response = model.invoke(
        [system_message] + state["messages"],
        config
    )
    
    return {"messages": [response]}
```

### 4.2 工具节点

```python
import json
from langchain_core.messages import ToolMessage

tools_by_name = {tool.name: tool for tool in tools}

def tool_node(state: DermaAgentState):
    """执行工具调用"""
    outputs = []
    last_message = state["messages"][-1]
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # 执行工具
        tool_result = tools_by_name[tool_name].invoke(tool_args)
        
        # 更新状态（根据工具类型）
        if tool_name == "analyze_skin_image":
            state["skin_analyses"].append(tool_result)
        elif tool_name == "search_medical_knowledge":
            state["knowledge_refs"].append(tool_result)
        elif tool_name == "generate_diagnosis":
            state["possible_conditions"] = tool_result.get("conditions", [])
            state["risk_level"] = tool_result.get("risk_level", "low")
            state["care_advice"] = tool_result.get("care_advice", "")
            state["need_offline_visit"] = tool_result.get("need_offline_visit", False)
        
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result, ensure_ascii=False),
                name=tool_name,
                tool_call_id=tool_call["id"]
            )
        )
    
    return {"messages": outputs}
```

### 4.3 条件边

```python
def should_continue(state: DermaAgentState) -> str:
    """判断是否需要继续执行工具"""
    last_message = state["messages"][-1]
    
    # 如果 LLM 返回了 tool_calls，继续执行工具
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    
    # 否则结束
    return "end"
```

### 4.4 完整图定义

```python
from langgraph.graph import StateGraph, END, START

def build_derma_agent():
    """构建皮肤科智能体状态图"""
    
    # 定义工具
    tools = [
        analyze_skin_image,
        search_medical_knowledge,
        generate_diagnosis,
        interpret_report
    ]
    
    # 绑定工具到 LLM
    model_with_tools = model.bind_tools(tools)
    
    # 创建状态图
    workflow = StateGraph(DermaAgentState)
    
    # 添加节点
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    # 设置入口点
    workflow.add_edge(START, "agent")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END
        }
    )
    
    # 工具执行后回到 agent
    workflow.add_edge("tools", "agent")
    
    # 编译图
    return workflow.compile()

# 单例模式
_derma_graph = None

def get_derma_graph():
    global _derma_graph
    if _derma_graph is None:
        _derma_graph = build_derma_agent()
    return _derma_graph
```

## 5. 工具详细设计

### 5.1 图片分析工具

```python
from langchain_core.tools import tool

@tool
def analyze_skin_image(image_base64: str, chief_complaint: str = "") -> dict:
    """
    分析皮肤图片，识别皮损特征。
    
    Args:
        image_base64: 图片的 base64 编码
        chief_complaint: 患者主诉，帮助分析
    
    Returns:
        dict: 包含分析结果的字典
            - description: 皮损描述
            - morphology: 形态特征（斑、丘疹、水疱等）
            - color: 颜色特征
            - distribution: 分布特征
            - suggested_conditions: 可能的疾病
    """
    # 使用多模态 LLM 分析图片
    multimodal_llm = LLMProvider.get_multimodal_llm()
    
    messages = [
        SystemMessage(content="""你是皮肤科影像专家。分析皮肤照片，描述皮损特征。

分析要点：
- 形态：斑、丘疹、水疱、结节等
- 颜色：红、褐、紫、白等
- 分布：局限性、泛发性、对称性
- 边界：清楚或模糊

输出 JSON 格式。"""),
        HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": image_base64}},
            {"type": "text", "text": f"请分析这张皮肤图片。患者主诉：{chief_complaint or '未说明'}"}
        ])
    ]
    
    response = multimodal_llm.invoke(messages)
    return parse_image_analysis(response.content)
```

### 5.2 知识库检索工具（RAG）

```python
@tool
def search_medical_knowledge(query: str, disease_type: str = "") -> dict:
    """
    检索皮肤科专业知识库，返回相关文献和建议。
    
    Args:
        query: 检索关键词或问题
        disease_type: 疾病类型（可选）
    
    Returns:
        dict: 包含检索结果
            - references: 引用的文献列表
            - summary: 综合摘要
            - recommendations: 专业建议
    """
    # TODO: 接入向量数据库（如 Chroma、Pinecone）
    # 这里是示例实现
    
    # 1. 向量检索相关文档
    docs = vector_store.similarity_search(query, k=5)
    
    # 2. 构建引用信息
    references = []
    for i, doc in enumerate(docs):
        references.append({
            "id": i + 1,
            "title": doc.metadata.get("title", "未知来源"),
            "source": doc.metadata.get("source", ""),
            "content_snippet": doc.page_content[:200]
        })
    
    # 3. 使用 LLM 综合文档生成回答
    context = "\n\n".join([doc.page_content for doc in docs])
    
    summary_prompt = f"""基于以下专业文献，回答问题：{query}

文献内容：
{context}

要求：
1. 综合多篇文献给出专业回答
2. 标注引用来源（如 [1]、[2]）
3. 给出具体的护理或治疗建议
"""
    
    summary = llm.invoke(summary_prompt).content
    
    return {
        "references": references,
        "summary": summary,
        "reference_count": len(references)
    }
```

### 5.3 诊断生成工具

```python
@tool
def generate_diagnosis(
    symptoms: List[str],
    location: str,
    duration: str,
    image_analysis: str = "",
    knowledge_refs: str = ""
) -> dict:
    """
    综合问诊信息生成诊断建议。
    
    Args:
        symptoms: 症状列表
        location: 皮损部位
        duration: 持续时间
        image_analysis: 图片分析结果（可选）
        knowledge_refs: 知识库参考（可选）
    
    Returns:
        dict: 诊断结果
            - conditions: 鉴别诊断列表
            - risk_level: 风险等级
            - care_advice: 护理建议
            - need_offline_visit: 是否需要线下就诊
    """
    diagnosis_prompt = f"""作为皮肤科专家，请根据以下信息给出诊断建议：

症状：{', '.join(symptoms)}
部位：{location}
持续时间：{duration}
{f'图片分析：{image_analysis}' if image_analysis else ''}
{f'参考文献：{knowledge_refs}' if knowledge_refs else ''}

请输出 JSON 格式：
{{
    "conditions": [
        {{"name": "疾病名", "probability": "likely/possible/unlikely", "basis": "诊断依据"}}
    ],
    "risk_level": "low/medium/high/emergency",
    "care_advice": "具体护理建议",
    "need_offline_visit": true/false,
    "offline_visit_reason": "就诊原因（如需要）"
}}
"""
    
    result = llm.with_structured_output(DiagnosisOutput).invoke(diagnosis_prompt)
    return result.model_dump()
```

## 6. 动态快捷选项生成

### 6.1 设计方案

在每次 LLM 回复后，自动生成与当前对话相关的快捷选项。

```python
class AgentResponse(BaseModel):
    """Agent 回复结构"""
    message: str = Field(description="回复消息")
    quick_options: List[str] = Field(
        description="3-4个快捷回复选项，简短（2-6个字）",
        default_factory=list
    )
    extracted_info: dict = Field(
        description="从对话中提取的医学信息",
        default_factory=dict
    )
```

### 6.2 Prompt 设计

```python
QUICK_OPTIONS_SUFFIX = """

在回复结束后，请生成 3-4 个快捷回复选项：
- 选项要简短（2-6个字）
- 与当前问题相关
- 覆盖常见回答
- 符合口语表达

例如：
- AI 问"症状持续多久了" → ["刚开始", "几天了", "一周以上", "很久了"]
- AI 问"有其他症状吗" → ["有瘙痒", "有疼痛", "有脱皮", "没有了"]
"""
```

### 6.3 后处理

```python
def extract_quick_options(response: str) -> List[dict]:
    """从 LLM 回复中提取快捷选项"""
    # 使用结构化输出或正则提取
    extractor = llm.with_structured_output(QuickOptionsExtractor)
    result = extractor.invoke(f"从以下回复中提取快捷选项：\n{response}")
    
    return [
        {"text": opt, "value": opt, "category": "reply"}
        for opt in result.options
    ]
```

## 7. RAG 知识库设计

### 7.1 知识库结构

```
knowledge_base/
├── dermatology/
│   ├── diseases/           # 疾病知识
│   │   ├── eczema.md       # 湿疹
│   │   ├── psoriasis.md    # 银屑病
│   │   └── ...
│   ├── treatments/         # 治疗方案
│   ├── medications/        # 用药指南
│   └── guidelines/         # 诊疗指南
```

### 7.2 向量化和检索

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

def init_knowledge_base():
    """初始化皮肤科知识库"""
    embeddings = OpenAIEmbeddings()
    
    # 加载文档
    docs = load_medical_documents("knowledge_base/dermatology/")
    
    # 创建向量存储
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory="./chroma_db/dermatology"
    )
    
    return vector_store
```

### 7.3 "院士团队解读"卡片

前端展示格式：

```json
{
    "type": "knowledge_card",
    "title": "院士团队解读",
    "badge": "权威",
    "subtitle": "医学思考路径由专业知识库提供",
    "metadata": {
        "model_call": "皮肤科专业知识库",
        "analysis_method": "根据医学专业文献分析",
        "thinking_path": "接触性皮炎的丘疹皮损形态",
        "reference_count": 8
    },
    "content": "生殖器部位出现无渗出的小疙瘩...",
    "sections": [
        {
            "title": "可能的原因与处理建议",
            "items": ["常见诱因", "基础护理", "就医指征"]
        }
    ],
    "show_detail_link": true
}
```

## 8. API 适配层

### 8.1 保持现有接口兼容

```python
class DermaReActWrapper(BaseAgent):
    """
    皮肤科 ReAct Agent 适配器
    
    实现 BaseAgent 接口，内部使用 ReAct 模式
    """
    
    def __init__(self):
        self._graph = get_derma_graph()
    
    async def create_initial_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """创建初始状态"""
        return {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "chief_complaint": "",
            "skin_location": "",
            "symptoms": [],
            "duration": "",
            "skin_analyses": [],
            "knowledge_refs": [],
            "possible_conditions": [],
            "current_response": "",
            "quick_options": [],
            "pending_attachments": [],
            "risk_level": "low",
            "care_advice": "",
            "need_offline_visit": False
        }
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        attachments: list = None,
        action: str = "conversation",
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """运行智能体"""
        
        # 添加用户消息
        if user_input:
            state["messages"].append(HumanMessage(content=user_input))
        
        # 处理附件
        if attachments:
            for att in attachments:
                if att.get("type", "").startswith("image"):
                    state["pending_attachments"].append(att)
        
        # 运行状态图
        if on_chunk:
            # 流式输出
            final_state = await self._run_with_stream(state, on_chunk)
        else:
            final_state = await self._graph.ainvoke(state)
        
        # 提取回复和快捷选项
        last_message = final_state["messages"][-1]
        if hasattr(last_message, "content"):
            final_state["current_response"] = last_message.content
            final_state["quick_options"] = extract_quick_options(last_message.content)
        
        return final_state
    
    async def _run_with_stream(self, state, on_chunk):
        """流式输出运行"""
        final_state = state
        
        async for event in self._graph.astream_events(state, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    await on_chunk(chunk.content)
            elif event["event"] == "on_chain_end":
                if "output" in event["data"]:
                    final_state = event["data"]["output"]
        
        return final_state
```

## 9. 对话流程示例

### 9.1 场景：用户首次描述问题

**用户**："我鸡鸡皮肤过敏"

**Agent 处理**：
1. `call_model` 接收消息
2. LLM 分析：用户描述了皮肤问题，需要了解更多信息
3. LLM 不调用工具，直接回复
4. 返回回复 + 快捷选项

**回复**："请问您出现过敏症状多久了？"

**快捷选项**：["刚开始", "几天了", "一周以上", "很久了"]

### 9.2 场景：收集到足够信息后

**用户**："没有渗出"

**Agent 处理**：
1. `call_model` 接收消息
2. LLM 分析：信息足够，可以给初步建议
3. LLM 调用 `search_medical_knowledge("生殖器部位无渗出小疙瘩", "接触性皮炎")`
4. `tool_node` 执行检索
5. 返回 `ToolMessage` 给 LLM
6. LLM 综合知识库结果，生成诊断建议

**回复**：
```
根据您的描述，近期出现的生殖器部位皮肤过敏可能与接触性刺激有关...

[院士团队解读卡片]
- 模型调用：皮肤科专业知识库
- 引用文献：8篇
- 医学思考路径：接触性皮炎的丘疹皮损形态
```

## 10. 实施计划

### 10.1 阶段一：核心框架（3天）

- [ ] 实现 ReAct Agent 基础框架
- [ ] 实现工具绑定和调用
- [ ] 实现状态管理
- [ ] 完成 API 适配层

### 10.2 阶段二：工具实现（3天）

- [ ] 图片分析工具（复用现有 VL 模型）
- [ ] 诊断生成工具
- [ ] 动态快捷选项生成

### 10.3 阶段三：RAG 知识库（5天）

- [ ] 知识库文档整理
- [ ] 向量化存储
- [ ] 检索工具实现
- [ ] "院士团队解读"卡片格式

### 10.4 阶段四：测试和优化（2天）

- [ ] 对话流程测试
- [ ] 性能优化
- [ ] A/B 测试对比

## 11. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| LLM 决策不稳定 | 对话流程不可控 | 添加 guardrails，必要时 fallback |
| 工具调用延迟 | 响应变慢 | 并行调用、缓存优化 |
| RAG 知识不足 | 回答质量下降 | 持续扩充知识库 |
| Token 消耗增加 | 成本上升 | 优化 Prompt、缓存策略 |

---

**文档版本**: v1.0  
**创建日期**: 2026-01-15  
**作者**: AI 架构设计
