# 中间建议和诊断卡片显示修复实施计划

> **状态:** ✅ 已完成
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复中间建议和诊断卡片不显示的问题，添加调试日志验证数据流

**Architecture:** 分两阶段实施 - 先添加调试日志验证数据流完整性，再根据调试结果修复显示问题。后端添加工具调用和状态更新日志，前端添加数据接收和UI渲染日志。

**Tech Stack:** Python, Swift, LangGraph, SwiftUI

---

## Task 1: 添加后端调试日志 - tool_node

**Files:**
- Modify: `backend/app/services/dermatology/react_agent.py:118-193`

**Step 1: 在 tool_node 开始处添加工具调用日志**

在 `tool_node` 函数的开始处，`if hasattr(last_message, "tool_calls")` 之前添加：

```python
def tool_node(state: DermaReActState) -> Dict[str, Any]:
    """工具节点：执行工具调用并更新状态"""
    outputs = []
    updates = {}  # 用于收集 state 更新
    last_message = state["messages"][-1]
    
    # === 调试日志：工具调用 ===
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"[DEBUG] tool_node 收到工具调用: {len(last_message.tool_calls)} 个")
        for tc in last_message.tool_calls:
            print(f"[DEBUG] - 工具名称: {tc['name']}")
            print(f"[DEBUG] - 工具参数: {tc['args']}")
    else:
        print(f"[DEBUG] tool_node: 没有工具调用")
    # === 日志结束 ===
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        ...
```

**Step 2: 在 generate_structured_diagnosis 分支添加结果日志**

在 `elif tool_name == "generate_structured_diagnosis":` 分支，执行工具后添加：

```python
elif tool_name == "generate_structured_diagnosis":
    # 更新诊断卡
    if isinstance(result, dict):
        # === 调试日志：诊断工具结果 ===
        print(f"[DEBUG] generate_structured_diagnosis 返回:")
        print(f"[DEBUG] - summary: {result.get('summary', 'N/A')[:50]}...")
        print(f"[DEBUG] - conditions: {len(result.get('conditions', []))} 个")
        print(f"[DEBUG] - risk_level: {result.get('risk_level', 'N/A')}")
        # === 日志结束 ===
        
        updates["diagnosis_card"] = result
        
        # === 调试日志：state 更新 ===
        print(f"[DEBUG] 已更新 state['diagnosis_card']")
        print(f"[DEBUG] - 包含字段: {list(result.keys())}")
        # === 日志结束 ===
        
        # 更新推理步骤
        if "reasoning_steps" in result:
            ...
```

**Step 3: 在 record_intermediate_advice 分支添加日志**

在 `elif tool_name == "record_intermediate_advice":` 分支，添加：

```python
elif tool_name == "record_intermediate_advice":
    # 记录中间建议
    if isinstance(result, dict):
        # === 调试日志：中间建议 ===
        print(f"[DEBUG] record_intermediate_advice 返回:")
        print(f"[DEBUG] - title: {result.get('title', 'N/A')}")
        print(f"[DEBUG] - content: {result.get('content', 'N/A')[:50]}...")
        # === 日志结束 ===
        
        advice_history = state.get("advice_history", [])
        updates["advice_history"] = advice_history + [result]
        
        # === 调试日志：state 更新 ===
        print(f"[DEBUG] 已更新 state['advice_history'], 当前数量: {len(updates['advice_history'])}")
        # === 日志结束 ===
        
        # 同步推理步骤
        current_steps = state.get("reasoning_steps", [])
        ...
```

**Step 4: 验证语法**

Run: `cd backend && source venv/bin/activate && python -c "from app.services.dermatology.react_agent import _build_derma_react_graph; print('Syntax OK')"`

Expected: `Syntax OK`

**Step 5: Commit**

```bash
git add backend/app/services/dermatology/react_agent.py
git commit -m "debug: 添加 tool_node 调试日志

- 记录工具调用信息
- 记录诊断工具返回结果
- 记录 state 更新情况"
```

---

## Task 2: 添加后端调试日志 - build_response

**Files:**
- Modify: `backend/app/routes/derma.py:198-248`

**Step 1: 在 advice_history 处理处添加日志**

在 `if state.get("advice_history"):` 分支添加：

```python
# 添加中间建议历史
if state.get("advice_history"):
    # === 调试日志 ===
    print(f"[DEBUG] build_response: 处理 advice_history")
    print(f"[DEBUG] - 数量: {len(state['advice_history'])}")
    for i, adv in enumerate(state['advice_history']):
        print(f"[DEBUG] - [{i}] title: {adv.get('title', 'N/A')}")
    # === 日志结束 ===
    
    response_data["advice_history"] = [
        DermaAdviceSchema(
            id=adv.get("id", ""),
            title=adv.get("title", ""),
            content=adv.get("content", ""),
            evidence=adv.get("evidence", []),
            timestamp=adv.get("timestamp", "")
        ) for adv in state["advice_history"]
    ]
else:
    # === 调试日志 ===
    print(f"[DEBUG] build_response: state 中没有 advice_history")
    # === 日志结束 ===
```

**Step 2: 在 diagnosis_card 处理处添加日志**

在 `if state.get("diagnosis_card"):` 分支添加：

```python
# 添加诊断卡
if state.get("diagnosis_card"):
    card = state["diagnosis_card"]
    
    # === 调试日志 ===
    print(f"[DEBUG] build_response: 处理 diagnosis_card")
    print(f"[DEBUG] - summary: {card.get('summary', 'N/A')[:50]}...")
    print(f"[DEBUG] - conditions: {len(card.get('conditions', []))} 个")
    print(f"[DEBUG] - risk_level: {card.get('risk_level', 'N/A')}")
    # === 日志结束 ===
    
    response_data["diagnosis_card"] = DermaDiagnosisCardSchema(
        summary=card.get("summary", ""),
        conditions=[
            DermaConditionSchema(
                name=c.get("name", ""),
                confidence=c.get("confidence", 0.0),
                rationale=c.get("rationale", [])
            ) for c in card.get("conditions", [])
        ],
        risk_level=card.get("risk_level", "low"),
        need_offline_visit=card.get("need_offline_visit", False),
        urgency=card.get("urgency"),
        care_plan=card.get("care_plan", []),
        references=[
            DermaKnowledgeRefSchema(
                id=ref.get("id", ""),
                title=ref.get("title", ""),
                snippet=ref.get("snippet", ""),
                source=ref.get("source"),
                link=ref.get("link")
            ) for ref in card.get("references", [])
        ],
        reasoning_steps=card.get("reasoning_steps", [])
    )
else:
    # === 调试日志 ===
    print(f"[DEBUG] build_response: state 中没有 diagnosis_card")
    print(f"[DEBUG] - state 包含的字段: {list(state.keys())}")
    # === 日志结束 ===
```

**Step 3: 验证语法**

Run: `cd backend && source venv/bin/activate && python -c "from app.routes.derma import build_response; print('Import OK')"`

Expected: `Import OK`

**Step 4: Commit**

```bash
git add backend/app/routes/derma.py
git commit -m "debug: 添加 build_response 调试日志

- 记录 advice_history 处理情况
- 记录 diagnosis_card 处理情况
- 记录 state 字段信息"
```

---

## Task 3: 添加前端调试日志 - ViewModel

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift:481-493`

**Step 1: 在 handleComplete 函数添加数据接收日志**

在 `// 更新诊断展示增强字段` 注释后添加：

```swift
// 更新诊断展示增强字段
// === 调试日志：数据接收 ===
print("[DEBUG] handleComplete 收到响应")
print("[DEBUG] - adviceHistory: \(response.adviceHistory?.count ?? 0) 条")
print("[DEBUG] - diagnosisCard: \(response.diagnosisCard != nil ? "有" : "无")")
print("[DEBUG] - knowledgeRefs: \(response.knowledgeRefs?.count ?? 0) 条")
print("[DEBUG] - reasoningSteps: \(response.reasoningSteps?.count ?? 0) 步")
// === 日志结束 ===

if let history = response.adviceHistory {
    adviceHistory = history
    // === 调试日志 ===
    print("[DEBUG] 已更新 adviceHistory: \(history.count) 条")
    for (i, adv) in history.enumerated() {
        print("[DEBUG] - [\(i)] \(adv.title)")
    }
    // === 日志结束 ===
}
if let card = response.diagnosisCard {
    diagnosisCard = card
    // === 调试日志 ===
    print("[DEBUG] 已更新 diagnosisCard:")
    print("[DEBUG] - summary: \(card.summary)")
    print("[DEBUG] - conditions: \(card.conditions.count) 个")
    print("[DEBUG] - riskLevel: \(card.riskLevel)")
    // === 日志结束 ===
} else {
    // === 调试日志 ===
    print("[DEBUG] API 响应中没有 diagnosisCard")
    // === 日志结束 ===
}
if let refs = response.knowledgeRefs {
    knowledgeRefs = refs
    print("[DEBUG] 已更新 knowledgeRefs: \(refs.count) 条")
}
if let steps = response.reasoningSteps {
    reasoningSteps = steps
    print("[DEBUG] 已更新 reasoningSteps: \(steps.count) 步")
}
```

**Step 2: 编译验证**

Run: `cd ios/xinlingyisheng && xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 15' build`

Expected: BUILD SUCCEEDED

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift
git commit -m "debug(ios): 添加 ViewModel 数据接收日志

- 记录 API 响应中的诊断数据
- 记录 ViewModel 状态更新"
```

---

## Task 4: 添加前端调试日志 - View

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift:178-186`

**Step 1: 在诊断卡片显示处添加日志**

修改诊断卡片显示部分：

```swift
// 诊断卡片
if let diagnosisCard = viewModel.diagnosisCard {
    DiagnosisSummaryCard(
        card: diagnosisCard,
        onViewDossier: { viewDossier() }
    )
    .padding(.horizontal, MedicalSpacing.lg)
    .transition(.move(edge: .bottom).combined(with: .opacity))
    .onAppear {
        // === 调试日志 ===
        print("[DEBUG] DiagnosisSummaryCard 已渲染")
        print("[DEBUG] - summary: \(diagnosisCard.summary)")
        print("[DEBUG] - conditions: \(diagnosisCard.conditions.count) 个")
        // === 日志结束 ===
    }
} else {
    // === 调试日志：诊断卡片未显示 ===
    VStack {
        Text("诊断卡片未显示")
            .font(.caption)
            .foregroundColor(.red)
        Text("diagnosisCard = nil")
            .font(.caption2)
            .foregroundColor(.gray)
    }
    .padding()
    .background(Color.yellow.opacity(0.1))
    .onAppear {
        print("[DEBUG] diagnosisCard 为 nil，未渲染卡片")
        print("[DEBUG] - messages.count: \(viewModel.messages.count)")
        print("[DEBUG] - adviceHistory.count: \(viewModel.adviceHistory.count)")
    }
    // === 日志结束 ===
}
```

**Step 2: 在中间建议显示位置添加占位日志**

在诊断卡片之前添加：

```swift
// 中间建议卡片（待实现）
if !viewModel.adviceHistory.isEmpty {
    VStack {
        Text("中间建议: \(viewModel.adviceHistory.count) 条")
            .font(.caption)
            .foregroundColor(.blue)
        Text("UI 组件待实现")
            .font(.caption2)
            .foregroundColor(.gray)
    }
    .padding()
    .background(Color.blue.opacity(0.1))
    .onAppear {
        print("[DEBUG] 检测到 \(viewModel.adviceHistory.count) 条中间建议，但 UI 组件未实现")
        for (i, adv) in viewModel.adviceHistory.enumerated() {
            print("[DEBUG] - [\(i)] \(adv.title): \(adv.content)")
        }
    }
}
```

**Step 3: 编译验证**

Run: `cd ios/xinlingyisheng && xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 15' build`

Expected: BUILD SUCCEEDED

**Step 4: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift
git commit -m "debug(ios): 添加 View 渲染日志和占位提示

- 诊断卡片渲染状态日志
- 中间建议占位提示
- nil 状态可视化提示"
```

---

## Task 5: 测试验证数据流

**Files:**
- Test: 完整对话流程

**Step 1: 启动后端服务**

Run: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`

Expected: 服务启动，监听 8000 端口

**Step 2: 启动 iOS 应用**

Run: 在 Xcode 中运行应用到模拟器

Expected: 应用启动成功

**Step 3: 执行测试对话**

执行以下对话流程：
1. 用户: "我手臂上有红疹"
2. 等待 AI 回复
3. 用户: "很痒，还有点脱皮"
4. 等待 AI 回复
5. 用户: "大概三天了"
6. 等待 AI 回复

**Step 4: 收集后端日志**

观察后端控制台，查找：
- `[DEBUG] tool_node 收到工具调用`
- `[DEBUG] generate_structured_diagnosis 返回`
- `[DEBUG] 已更新 state['diagnosis_card']`
- `[DEBUG] build_response: 处理 diagnosis_card`

**Step 5: 收集前端日志**

观察 Xcode 控制台，查找：
- `[DEBUG] handleComplete 收到响应`
- `[DEBUG] 已更新 diagnosisCard`
- `[DEBUG] DiagnosisSummaryCard 已渲染` 或 `[DEBUG] diagnosisCard 为 nil`
- `[DEBUG] 检测到 X 条中间建议`

**Step 6: 记录测试结果**

创建测试报告文件：

```bash
cat > docs/plans/2026-01-16-debug-test-results.md << 'EOF'
# 调试测试结果

## 测试时间
2026-01-16

## 后端日志
```
[粘贴后端日志]
```

## 前端日志
```
[粘贴前端日志]
```

## 问题定位
- [ ] Agent 是否调用了诊断工具？
- [ ] state 是否正确更新？
- [ ] API 响应是否包含数据？
- [ ] iOS 是否正确接收？
- [ ] UI 是否正确渲染？

## 下一步行动
[根据日志分析结果填写]
EOF
```

**Step 7: Commit 测试结果**

```bash
git add docs/plans/2026-01-16-debug-test-results.md
git commit -m "test: 记录调试测试结果

- 后端日志输出
- 前端日志输出
- 问题定位分析"
```

---

## Task 6: 根据测试结果修复问题

**Files:**
- 待定（根据测试结果确定）

**Step 1: 分析日志，定位问题**

根据测试结果，确定问题所在：

**场景 A: Agent 未调用工具**
- 原因：System Prompt 不够清晰
- 修复：优化 DERMA_REACT_PROMPT

**场景 B: state 未更新**
- 原因：tool_node 逻辑问题
- 修复：检查条件判断

**场景 C: API 响应缺失**
- 原因：build_response 序列化问题
- 修复：检查 Schema 定义

**场景 D: iOS 未接收**
- 原因：网络或解析问题
- 修复：检查 API 调用和解码

**场景 E: UI 未渲染**
- 原因：条件判断或数据绑定问题
- 修复：检查 SwiftUI 逻辑

**Step 2: 实施对应修复**

根据定位结果，执行相应的修复任务（具体步骤待测试后确定）

**Step 3: 回归测试**

重复 Task 5 的测试流程，验证修复效果

**Step 4: Commit 修复**

```bash
git add [修改的文件]
git commit -m "fix: 修复诊断卡片显示问题

- [具体修复内容]
- 验证测试通过"
```

---

## Task 7: 实现中间建议 UI 组件（如果需要）

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Views/Components/AdviceCardView.swift`
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift:178`

**Step 1: 创建 AdviceCardView 组件**

```swift
import SwiftUI

/// 中间建议卡片
struct AdviceCardView: View {
    let advice: AdviceEntry
    @State private var isExpanded = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: MedicalSpacing.sm) {
            // 标题栏
            HStack {
                Image(systemName: "lightbulb.fill")
                    .foregroundColor(MedicalColors.statusWarning)
                    .font(.system(size: 16))
                
                Text(advice.title)
                    .font(MedicalTypography.h5)
                    .foregroundColor(MedicalColors.textPrimary)
                
                Spacer()
                
                if !advice.evidence.isEmpty {
                    Button(action: { isExpanded.toggle() }) {
                        Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                            .foregroundColor(MedicalColors.textSecondary)
                            .font(.system(size: 14))
                    }
                }
            }
            
            // 建议内容
            Text(advice.content)
                .font(MedicalTypography.bodyMedium)
                .foregroundColor(MedicalColors.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
            
            // 依据（可展开）
            if isExpanded && !advice.evidence.isEmpty {
                VStack(alignment: .leading, spacing: MedicalSpacing.xs) {
                    Text("依据:")
                        .font(MedicalTypography.caption)
                        .foregroundColor(MedicalColors.textMuted)
                    
                    ForEach(advice.evidence, id: \.self) { item in
                        HStack(alignment: .top, spacing: 4) {
                            Text("•")
                                .foregroundColor(MedicalColors.textMuted)
                            Text(item)
                                .font(MedicalTypography.caption)
                                .foregroundColor(MedicalColors.textMuted)
                        }
                    }
                }
                .padding(.top, MedicalSpacing.xs)
            }
            
            // 时间戳
            Text(formatTimestamp(advice.timestamp))
                .font(MedicalTypography.caption)
                .foregroundColor(MedicalColors.textMuted)
        }
        .padding(MedicalSpacing.md)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(MedicalColors.statusWarning.opacity(0.05))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(MedicalColors.statusWarning.opacity(0.2), lineWidth: 1)
        )
    }
    
    private func formatTimestamp(_ timestamp: String) -> String {
        // 简单格式化，实际可以用 DateFormatter
        return timestamp.components(separatedBy: "T").first ?? timestamp
    }
}

// MARK: - Preview
struct AdviceCardView_Previews: PreviewProvider {
    static var previews: some View {
        AdviceCardView(
            advice: AdviceEntry(
                id: "1",
                title: "初步护理建议",
                content: "建议保持皮肤清洁干燥，避免抓挠患处。可以使用温和的保湿霜。",
                evidence: ["湿疹护理指南", "皮肤科临床实践"],
                timestamp: "2026-01-16T14:30:00"
            )
        )
        .padding()
    }
}
```

**Step 2: 在 ModernConsultationView 中使用**

替换之前的占位代码：

```swift
// 中间建议卡片
ForEach(viewModel.adviceHistory) { advice in
    AdviceCardView(advice: advice)
        .padding(.horizontal, MedicalSpacing.lg)
        .transition(.move(edge: .bottom).combined(with: .opacity))
}
```

**Step 3: 编译验证**

Run: `cd ios/xinlingyisheng && xcodebuild -scheme xinlingyisheng -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 15' build`

Expected: BUILD SUCCEEDED

**Step 4: Commit**

```bash
git add ios/xinlingyisheng/xinlingyisheng/Views/Components/AdviceCardView.swift ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift
git commit -m "feat(ios): 实现中间建议卡片 UI 组件

- 创建 AdviceCardView 组件
- 支持依据展开/折叠
- 集成到 ModernConsultationView"
```

---

## Task 8: 清理调试日志

**Files:**
- Modify: `backend/app/services/dermatology/react_agent.py`
- Modify: `backend/app/routes/derma.py`
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift`
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift`

**Step 1: 移除或注释后端调试日志**

将所有 `# === 调试日志 ===` 到 `# === 日志结束 ===` 之间的代码注释掉或删除

**Step 2: 移除或注释前端调试日志**

将所有 `// === 调试日志 ===` 到 `// === 日志结束 ===` 之间的代码注释掉

**Step 3: 移除占位提示 UI**

删除 "诊断卡片未显示" 的黄色提示框

**Step 4: 验证编译**

Run: 
```bash
cd backend && source venv/bin/activate && python -c "from app.services.dermatology.react_agent import get_derma_react_graph; print('Backend OK')"
cd ios/xinlingyisheng && xcodebuild -scheme xinlingyisheng -sdk iphonesimulator build
```

Expected: 
```
Backend OK
BUILD SUCCEEDED
```

**Step 5: Commit**

```bash
git add backend/app/services/dermatology/react_agent.py backend/app/routes/derma.py ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift
git commit -m "chore: 清理调试日志

- 移除临时调试日志
- 保留核心功能代码"
```

---

## 验收清单

### 功能验收
- [ ] 中间建议卡片正确显示
- [ ] 诊断卡片正确显示
- [ ] 数据流完整（后端 → API → iOS → UI）
- [ ] 调试日志帮助定位问题
- [ ] UI 组件样式符合设计系统

### 测试验收
- [ ] 完整对话流程测试通过
- [ ] 日志输出符合预期
- [ ] 无编译错误和警告
- [ ] UI 渲染流畅无卡顿

### 代码质量
- [ ] 代码符合项目规范
- [ ] 调试日志已清理
- [ ] 提交信息清晰
- [ ] 无遗留 TODO 或临时代码

---

## 后续优化

1. **中间建议样式优化** - 根据建议类型使用不同颜色
2. **诊断卡片交互增强** - 添加展开/折叠动画
3. **数据持久化** - 保存建议和诊断到本地
4. **性能优化** - 大量建议时的渲染优化

---

**计划创建时间**: 2026-01-16  
**预计完成时间**: 2-3 小时  
**风险等级**: 中
