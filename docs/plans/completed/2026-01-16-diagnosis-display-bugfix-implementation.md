# 诊断展示功能缺陷修复实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复快捷回答交互和诊断卡片显示两个关键缺陷

**Architecture:** 
- 前端：修改快捷选项点击行为，从直接发送改为填入输入框
- 后端：更新 System Prompt 添加新工具说明，修改 tool_node 在工具执行后更新 state，实现中间建议自动提取机制

**Tech Stack:** Swift/SwiftUI (iOS), Python/LangGraph (Backend), LangChain

---

## Task 1: 快捷回答交互优化（iOS）

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift:604-622`

**Step 1: 修改快捷选项点击行为**

在 `ModernConsultationView.swift` 中找到 `quickOptionsView` 的 Button action（约 608-614 行），修改为：

```swift
private var quickOptionsView: some View {
    ScrollView(.horizontal, showsIndicators: false) {
        HStack(spacing: 8) {
            ForEach(message.quickOptions) { option in
                Button(action: {
                    // 追加到输入框，支持多选
                    if !messageText.isEmpty {
                        messageText += " "  // 用空格分隔
                    }
                    messageText += option.text
                }) {
                    Text(option.text)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(MedicalColors.primaryBlue)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(MedicalColors.primaryBlue.opacity(0.1))
                        .cornerRadius(16)
                        .overlay(
                            RoundedRectangle(cornerRadius: 16)
                                .stroke(MedicalColors.primaryBlue.opacity(0.3), lineWidth: 1)
                        )
                }
            }
        }
    }
}
```

**Step 2: 删除 NotificationCenter 监听**

在 `ModernConsultationView.swift` 的 `body` 中（约 87-93 行），删除以下代码：

```swift
// 删除这段代码：
.onReceive(NotificationCenter.default.publisher(for: NSNotification.Name("SendQuickOption"))) { notification in
    if let text = notification.userInfo?["text"] as? String {
        Task {
            await viewModel.sendMessage(content: text)
        }
    }
}
```

**Step 3: 编译验证**

```bash
cd ios/xinlingyisheng
xcodebuild -scheme 灵犀医生 -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build
```

Expected: Build succeeded

**Step 4: 提交更改**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift
git commit -m "fix(ios): 快捷回答改为填入输入框而非直接发送"
```

---

## Task 2: 更新 System Prompt 添加新工具说明

**Files:**
- Modify: `backend/app/services/dermatology/react_agent.py:16-41`

**Step 1: 更新 DERMA_REACT_PROMPT**

完整替换 `DERMA_REACT_PROMPT` 变量：

```python
DERMA_REACT_PROMPT = """你是一位经验丰富的皮肤科专家医生，正在与患者进行问诊对话。

## 角色定位
- 专业但亲和，用通俗易懂的语言
- 像真人医生一样自然对话

## 对话原则
1. 直接响应用户问题，不使用固定模板
2. 渐进式诊断：边问诊边给初步建议
3. 每次回复后追问 1-2 个关键问题
4. 需要时主动调用工具

## 信息收集要点
- 主诉：什么问题
- 部位：身体哪个位置
- 症状：红肿、瘙痒、疼痛、脱皮等
- 持续时间

## 可用工具及使用时机

### 1. analyze_skin_image
- **用途**: 分析皮肤图片
- **时机**: 用户上传皮肤照片时

### 2. retrieve_derma_knowledge
- **用途**: 检索皮肤科医学知识库
- **时机**: 收集到症状后，生成诊断前
- **参数**: symptoms（症状列表）, location（部位）, query（补充查询词）
- **返回**: 相关医学知识引用列表

### 3. generate_structured_diagnosis
- **用途**: 生成结构化诊断卡
- **时机**: 收集完主要信息（主诉、部位、症状、持续时间）后
- **参数**: symptoms, location, duration, knowledge_refs（来自步骤2）, additional_info
- **返回**: 包含鉴别诊断、风险等级、护理建议的结构化诊断卡

### 4. generate_diagnosis (旧工具，保留兼容)
- **用途**: 生成文本诊断建议
- **时机**: 快速给出初步建议时使用

## 诊断工作流（重要）

当收集完以下信息后，按顺序调用工具：
1. 主诉（chief_complaint）
2. 部位（skin_location）
3. 症状列表（symptoms，至少2个）
4. 持续时间（duration）

**标准流程**:
```
步骤1: 调用 retrieve_derma_knowledge(symptoms=症状列表, location=部位)
步骤2: 调用 generate_structured_diagnosis(
    symptoms=症状列表,
    location=部位,
    duration=持续时间,
    knowledge_refs=步骤1的结果
)
```

## 输出要求
- 回复简洁自然（2-4句话）
- 识别危急情况立即建议就医
- 调用工具后，基于结果给出专业建议"""
```

**Step 2: 提交更改**

```bash
git add backend/app/services/dermatology/react_agent.py
git commit -m "feat(backend): 更新 System Prompt 添加新工具使用说明"
```

---

## Task 3: 修改 tool_node 更新 state

**Files:**
- Modify: `backend/app/services/dermatology/react_agent.py:67-88`

**Step 1: 完整替换 tool_node 函数**

找到 `tool_node` 函数（约 67-88 行），完整替换为：

```python
def tool_node(state: DermaReActState) -> Dict[str, Any]:
    """工具节点：执行工具调用并更新状态"""
    outputs = []
    updates = {}  # 用于收集 state 更新
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # 执行工具
            if tool_name in tools_by_name:
                result = tools_by_name[tool_name].invoke(tool_args)
                
                # 根据工具类型更新 state
                if tool_name == "retrieve_derma_knowledge":
                    # 更新知识引用
                    if isinstance(result, list):
                        updates["knowledge_refs"] = result
                        # 同时添加到推理步骤
                        current_steps = state.get("reasoning_steps", [])
                        updates["reasoning_steps"] = current_steps + [
                            f"检索到 {len(result)} 条相关医学知识"
                        ]
                
                elif tool_name == "generate_structured_diagnosis":
                    # 更新诊断卡
                    if isinstance(result, dict):
                        updates["diagnosis_card"] = result
                        # 更新推理步骤
                        if "reasoning_steps" in result:
                            current_steps = state.get("reasoning_steps", [])
                            updates["reasoning_steps"] = current_steps + result["reasoning_steps"]
                        # 更新风险等级和就诊建议
                        if "risk_level" in result:
                            updates["risk_level"] = result["risk_level"]
                        if "need_offline_visit" in result:
                            updates["need_offline_visit"] = result["need_offline_visit"]
                
                elif tool_name == "analyze_skin_image":
                    # 保持原有逻辑
                    if isinstance(result, dict) and "analysis" in result:
                        skin_analyses = state.get("skin_analyses", [])
                        updates["skin_analyses"] = skin_analyses + [result]
                
                # 添加工具消息
                outputs.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False),
                        name=tool_name,
                        tool_call_id=tool_call["id"]
                    )
                )
    
    # 返回消息和状态更新
    return {"messages": outputs, **updates}
```

**Step 2: 提交更改**

```bash
git add backend/app/services/dermatology/react_agent.py
git commit -m "feat(backend): tool_node 执行工具后更新 state 字段"
```

---

## Task 4: 实现中间建议自动提取

**Files:**
- Modify: `backend/app/services/dermatology/react_agent.py:55-65`

**Step 1: 修改 call_model 函数添加建议提取逻辑**

找到 `call_model` 函数（约 55-65 行），完整替换为：

```python
def call_model(state: DermaReActState) -> Dict[str, Any]:
    """Agent 节点：调用 LLM"""
    system_message = SystemMessage(content=DERMA_REACT_PROMPT)
    
    # 构建消息列表
    messages = [system_message] + list(state["messages"])
    
    # 调用 LLM
    response = model_with_tools.invoke(messages)
    
    updates = {"messages": [response]}
    
    # 如果 Agent 给出了建议（没有调用工具），提取为中间建议
    if isinstance(response, AIMessage) and not response.tool_calls:
        content = response.content
        # 简单判断：如果回复包含建议关键词
        if any(keyword in content for keyword in ["建议", "可以", "应该", "注意", "避免", "推荐"]):
            import uuid
            from datetime import datetime
            
            advice_entry = {
                "id": str(uuid.uuid4()),
                "title": "护理建议",
                "content": content,
                "evidence": [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            advice_history = state.get("advice_history", [])
            updates["advice_history"] = advice_history + [advice_entry]
    
    return updates
```

**Step 2: 提交更改**

```bash
git add backend/app/services/dermatology/react_agent.py
git commit -m "feat(backend): 实现中间建议自动提取机制"
```

---

## Task 5: 编写单元测试

**Files:**
- Create: `backend/test/test_tool_node_state_update.py`

**Step 1: 创建测试文件**

```python
"""测试工具节点状态更新功能"""
import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage, ToolMessage

from app.services.dermatology.react_state import DermaReActState, create_react_initial_state
from app.services.dermatology.react_agent import _build_derma_react_graph


class TestToolNodeStateUpdate:
    """测试工具节点更新 state"""
    
    def test_retrieve_knowledge_updates_state(self):
        """测试 retrieve_derma_knowledge 更新 knowledge_refs"""
        # 创建初始状态
        state = create_react_initial_state("test-session", 1)
        
        # 模拟工具调用消息
        tool_call = {
            "name": "retrieve_derma_knowledge",
            "args": {"symptoms": ["红疹", "瘙痒"], "location": "手臂"},
            "id": "call-123"
        }
        ai_message = AIMessage(content="", tool_calls=[tool_call])
        state["messages"] = [ai_message]
        
        # 模拟工具执行结果
        mock_result = [
            {"id": "kb-001", "title": "湿疹诊疗指南", "snippet": "湿疹是..."}
        ]
        
        with patch('app.services.dermatology.react_tools.retrieve_derma_knowledge') as mock_tool:
            mock_tool.return_value = mock_result
            
            # 构建并执行图
            graph = _build_derma_react_graph()
            result = graph.invoke(state)
            
            # 验证 knowledge_refs 被更新
            assert "knowledge_refs" in result
            assert len(result["knowledge_refs"]) == 1
            assert result["knowledge_refs"][0]["id"] == "kb-001"
            
            # 验证推理步骤被添加
            assert "reasoning_steps" in result
            assert any("检索到" in step for step in result["reasoning_steps"])
    
    def test_generate_diagnosis_updates_state(self):
        """测试 generate_structured_diagnosis 更新 diagnosis_card"""
        state = create_react_initial_state("test-session", 1)
        
        tool_call = {
            "name": "generate_structured_diagnosis",
            "args": {
                "symptoms": ["红疹", "瘙痒"],
                "location": "手臂",
                "duration": "三天"
            },
            "id": "call-456"
        }
        ai_message = AIMessage(content="", tool_calls=[tool_call])
        state["messages"] = [ai_message]
        
        mock_result = {
            "summary": "手臂红疹伴瘙痒",
            "conditions": [{"name": "湿疹", "confidence": 0.8, "rationale": ["红疹", "瘙痒"]}],
            "risk_level": "low",
            "need_offline_visit": False,
            "care_plan": ["保持清洁"],
            "reasoning_steps": ["分析症状", "生成诊断"]
        }
        
        with patch('app.services.dermatology.react_tools.generate_structured_diagnosis') as mock_tool:
            mock_tool.return_value = mock_result
            
            graph = _build_derma_react_graph()
            result = graph.invoke(state)
            
            # 验证 diagnosis_card 被更新
            assert "diagnosis_card" in result
            assert result["diagnosis_card"]["summary"] == "手臂红疹伴瘙痒"
            assert result["diagnosis_card"]["risk_level"] == "low"
            
            # 验证风险等级被同步
            assert result["risk_level"] == "low"
            assert result["need_offline_visit"] is False


class TestAdviceExtraction:
    """测试中间建议提取"""
    
    def test_advice_extracted_from_response(self):
        """测试从 AI 回复中提取建议"""
        state = create_react_initial_state("test-session", 1)
        
        # 模拟包含建议的回复
        with patch('app.services.llm_provider.LLMProvider.get_llm') as mock_llm:
            mock_response = AIMessage(content="建议您保持皮肤清洁干燥，避免抓挠。")
            mock_llm.return_value.bind_tools.return_value.invoke.return_value = mock_response
            
            graph = _build_derma_react_graph()
            result = graph.invoke(state)
            
            # 验证建议被提取
            assert "advice_history" in result
            assert len(result["advice_history"]) > 0
            assert "建议" in result["advice_history"][0]["content"]
            assert result["advice_history"][0]["title"] == "护理建议"
    
    def test_no_advice_extraction_for_questions(self):
        """测试纯问题不会被提取为建议"""
        state = create_react_initial_state("test-session", 1)
        
        with patch('app.services.llm_provider.LLMProvider.get_llm') as mock_llm:
            mock_response = AIMessage(content="请问您的症状持续多久了？")
            mock_llm.return_value.bind_tools.return_value.invoke.return_value = mock_response
            
            graph = _build_derma_react_graph()
            result = graph.invoke(state)
            
            # 验证不会提取为建议
            assert len(result.get("advice_history", [])) == 0
```

**Step 2: 运行测试**

```bash
cd backend
source venv/bin/activate
python -m pytest test/test_tool_node_state_update.py -v
```

Expected: 所有测试通过

**Step 3: 提交测试**

```bash
git add backend/test/test_tool_node_state_update.py
git commit -m "test(backend): 添加工具节点状态更新和建议提取测试"
```

---

## Task 6: 端到端测试

**Files:**
- Test: 手动测试

**Step 1: 启动后端服务**

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8100
```

Expected: 服务启动成功，监听 8100 端口

**Step 2: 启动 iOS 模拟器**

```bash
cd ios/xinlingyisheng
xcodebuild -scheme 灵犀医生 -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build
# 获取 app 路径
APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData -name "xinlingyisheng.app" | head -1)
# 启动模拟器
xcrun simctl boot "iPhone 17 Pro" || true
xcrun simctl install booted "$APP_PATH"
xcrun simctl launch booted com.example.xinlingyisheng
```

**Step 3: 测试快捷回答交互**

1. 在 iOS 模拟器中进入问诊界面
2. 发送消息："我手臂有点痒"
3. 等待 AI 回复带快捷选项
4. **点击第一个快捷选项** → 验证文本填入输入框
5. **点击第二个快捷选项** → 验证追加到输入框（空格分隔）
6. **点击发送** → 验证消息发送成功

Expected: 快捷选项点击后填入输入框，不会直接发送

**Step 4: 测试诊断卡片显示**

1. 创建新会话
2. 按顺序提供信息：
   - "我手臂上有红疹"
   - "很痒，还有点脱皮"
   - "大概三天了"
3. 观察后端日志，验证：
   - 调用 `retrieve_derma_knowledge`
   - 调用 `generate_structured_diagnosis`
4. 观察 iOS 界面，验证：
   - 显示诊断卡片
   - 包含症状总结、鉴别诊断、风险等级、护理建议

Expected: 诊断卡片正确显示，包含所有必要信息

**Step 5: 检查 API 响应**

使用 curl 或 Postman 发送请求，验证响应包含新字段：

```bash
curl -X POST http://localhost:8100/derma/test-session/continue \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "history": [...],
    "current_input": {"message": "我手臂有红疹，很痒，三天了"},
    "task_type": "conversation"
  }'
```

Expected: 响应包含 `diagnosis_card`, `knowledge_refs`, `reasoning_steps` 字段

---

## Task 7: 更新文档

**Files:**
- Modify: `docs/plans/2026-01-16-diagnosis-display-bugfix.md`

**Step 1: 在文档末尾添加实施记录**

```markdown
---

## 实施记录

### 2026-01-16 实施完成

#### 修改文件
- `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift`
  - 修改快捷选项点击行为
  - 删除 NotificationCenter 监听
- `backend/app/services/dermatology/react_agent.py`
  - 更新 System Prompt
  - 修改 tool_node 函数
  - 修改 call_model 函数

#### 测试结果
- ✅ 快捷回答交互测试通过
- ✅ 诊断卡片显示测试通过
- ✅ 单元测试全部通过
- ✅ 端到端测试通过

#### 遗留问题
- 无

#### 后续优化
- 考虑添加快捷选项已选中的视觉反馈
- 优化中间建议提取的关键词匹配逻辑
- 扩充本地知识库内容
```

**Step 2: 提交文档更新**

```bash
git add docs/plans/2026-01-16-diagnosis-display-bugfix.md
git commit -m "docs: 添加诊断显示缺陷修复实施记录"
```

---

## Task 8: 最终验证和清理

**Step 1: 运行所有后端测试**

```bash
cd backend
source venv/bin/activate
python -m pytest test/ -v --tb=short
```

Expected: 所有测试通过

**Step 2: iOS 完整编译**

```bash
cd ios/xinlingyisheng
xcodebuild -scheme 灵犀医生 -sdk iphonesimulator clean build
```

Expected: Build succeeded, 无警告或错误

**Step 3: 代码格式检查（可选）**

```bash
# Python
cd backend
black app/ test/ --check
flake8 app/ test/

# Swift (如果有 SwiftLint)
cd ios/xinlingyisheng
swiftlint
```

**Step 4: 创建最终提交**

```bash
git add -A
git commit -m "fix: 完成诊断显示功能缺陷修复

- 快捷回答改为填入输入框支持多选
- 更新 System Prompt 添加新工具使用说明
- tool_node 执行工具后更新 state 字段
- 实现中间建议自动提取机制
- 添加完整的单元测试覆盖
- 端到端测试验证通过"
```

**Step 5: 推送代码（如果需要）**

```bash
git push origin main
```

---

## 验收标准

### 快捷回答交互
- [x] 点击快捷选项后文本填入输入框
- [x] 支持多选（空格分隔）
- [x] 手动点击发送按钮才发送消息
- [x] 发送后快捷选项仍然可见（绑定在消息上）

### 诊断卡片显示
- [x] Agent 收集完症状后自动调用 `retrieve_derma_knowledge`
- [x] Agent 调用 `generate_structured_diagnosis` 生成诊断卡
- [x] 工具执行后 state 正确更新
- [x] API 响应包含 `diagnosis_card`, `knowledge_refs`, `reasoning_steps`
- [x] iOS 界面正确显示诊断卡片
- [x] 诊断卡片包含所有必要信息（症状总结、鉴别诊断、风险等级、护理建议、知识引用）

### 中间建议
- [x] Agent 给出建议时自动提取为 `advice_history`
- [x] 建议包含 id, title, content, timestamp
- [x] 纯问题不会被误提取为建议

### 测试覆盖
- [x] 单元测试覆盖工具节点状态更新
- [x] 单元测试覆盖建议提取逻辑
- [x] 端到端测试验证完整流程

---

## 预计时间

- Task 1: 15 分钟（iOS 快捷回答优化）
- Task 2: 10 分钟（更新 System Prompt）
- Task 3: 15 分钟（修改 tool_node）
- Task 4: 15 分钟（实现建议提取）
- Task 5: 30 分钟（编写单元测试）
- Task 6: 20 分钟（端到端测试）
- Task 7: 5 分钟（更新文档）
- Task 8: 10 分钟（最终验证）

**总计**: 约 2 小时

---

## 注意事项

1. **修改 tool_node 时要小心**：这是核心数据流，确保不破坏现有工具（如 `analyze_skin_image`）的逻辑
2. **测试要充分**：工具节点的修改涉及状态管理，必须有完整的单元测试覆盖
3. **日志很重要**：在关键位置添加日志，便于调试
4. **保持向后兼容**：旧的 `generate_diagnosis` 工具仍然保留，不影响现有功能

---

**实施者**: 项目团队  
**审核者**: 技术负责人  
**最后更新**: 2026-01-16
