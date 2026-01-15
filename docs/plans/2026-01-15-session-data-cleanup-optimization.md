# 会话数据清理与系统优化实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标**: 清理数据库中的旧数据和不完整病历，实施iOS客户端优化，确保会话聚合功能正常工作

**架构**: 后端已添加数据完整性验证，现在需要清理历史脏数据，并优化iOS客户端的用户体验，使"生成病历"功能只在信息收集完整后才可用

**技术栈**: Python (SQLAlchemy), Swift (SwiftUI), PostgreSQL

---

## Task 1: 数据库完全清理

**目标**: 删除所有测试数据，从干净状态开始

**Files:**
- Execute: `backend/scripts/cleanup_incomplete_events.py`
- Verify: 数据库查询验证

### Step 1: 预览将要删除的数据

**命令**:
```bash
cd backend
source venv/bin/activate
python scripts/cleanup_incomplete_events.py --full --dry-run
```

**预期输出**:
```
=== 数据库统计 ===
统一会话表 (sessions): 66 条
消息表 (messages): 137 条
病历事件表 (medical_events): 6 条
旧会话表:
  - derma_sessions: 10 条
  - diagnosis_sessions: 6 条

=== ⚠️  完全清理模式 ===
将删除:
  - 66 个会话
  - 137 条消息
  - 6 个病历事件

[预览模式] 使用 --full 参数且不带 --dry-run 来执行完全清理
```

### Step 2: 执行完全清理

**命令**:
```bash
python scripts/cleanup_incomplete_events.py --full
# 当提示时输入: YES
```

**交互**:
```
⚠️  确认要删除所有数据吗？这个操作不可恢复！输入 'YES' 确认: YES
```

**预期输出**:
```
✅ 已完全清理数据库

清理后的统计:
统一会话表 (sessions): 0 条
消息表 (messages): 0 条
病历事件表 (medical_events): 0 条
旧会话表:
  - derma_sessions: 0 条
  - diagnosis_sessions: 0 条
```

### Step 3: 验证清理结果

**命令**:
```bash
python -c "
from app.database import SessionLocal
from app.models.session import Session
from app.models.message import Message
from app.models.medical_event import MedicalEvent
from app.models.derma_session import DermaSession
from app.models.diagnosis_session import DiagnosisSession

db = SessionLocal()
try:
    print(f'Sessions: {db.query(Session).count()}')
    print(f'Messages: {db.query(Message).count()}')
    print(f'MedicalEvents: {db.query(MedicalEvent).count()}')
    print(f'DermaSessions: {db.query(DermaSession).count()}')
    print(f'DiagnosisSessions: {db.query(DiagnosisSession).count()}')
finally:
    db.close()
"
```

**预期输出**:
```
Sessions: 0
Messages: 0
MedicalEvents: 0
DermaSessions: 0
DiagnosisSessions: 0
```

### Step 4: 提交清理脚本改进

```bash
git add backend/scripts/cleanup_incomplete_events.py
git commit -m "feat: add database cleanup script with full cleanup mode"
```

---

## Task 2: 后端数据完整性验证优化

**目标**: 改进错误提示，让用户知道具体缺少什么信息

**Files:**
- Modify: `backend/app/routes/medical_events.py:474-490`

### Step 1: 改进验证逻辑，提供更详细的错误信息

**修改代码**:

```python
# 4. 数据完整性验证
# 检查是否收集到足够的信息才允许聚合
validation_errors = []

if not chief_complaint:
    validation_errors.append("尚未明确主诉")
if not symptoms or len(symptoms) == 0:
    validation_errors.append("尚未收集到症状信息")
if stage == "greeting":
    validation_errors.append("对话刚开始，请先描述您的问题")
elif stage == "collecting":
    if len(messages) < 3:
        validation_errors.append("对话信息太少，请继续描述症状")

if validation_errors:
    error_detail = "会话信息不完整: " + "、".join(validation_errors) + "。请继续对话后再生成病历。"
    logger.warning(f"Session {request.session_id} validation failed: {validation_errors}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_detail
    )
```

### Step 2: 测试验证逻辑

**创建测试脚本**: `backend/test_aggregate_validation.py`

```python
#!/usr/bin/env python3
"""测试聚合接口的数据完整性验证"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.session import Session
from app.models.user import User
import uuid

def test_incomplete_session():
    """测试不完整会话的验证"""
    db = SessionLocal()
    try:
        # 创建测试用户
        user = db.query(User).first()
        if not user:
            print("错误: 需要至少一个用户")
            return
        
        # 创建不完整的会话
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user.id,
            agent_type="dermatology",
            agent_state={
                "session_id": str(uuid.uuid4()),
                "user_id": user.id,
                "chief_complaint": "",  # 空主诉
                "symptoms": [],  # 空症状
                "stage": "greeting",
                "messages": []
            }
        )
        db.add(session)
        db.commit()
        
        print(f"✅ 创建测试会话: {session.id}")
        print(f"   主诉: '{session.agent_state.get('chief_complaint')}'")
        print(f"   症状: {session.agent_state.get('symptoms')}")
        print(f"   阶段: {session.agent_state.get('stage')}")
        print(f"\n现在可以测试聚合接口，应该返回详细的验证错误")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_incomplete_session()
```

### Step 3: 运行测试

```bash
cd backend
python test_aggregate_validation.py
```

### Step 4: 提交改进

```bash
git add backend/app/routes/medical_events.py
git add backend/test_aggregate_validation.py
git commit -m "feat: improve aggregate validation with detailed error messages"
```

---

## Task 3: iOS客户端按钮优化

**目标**: 根据对话状态动态显示"生成病历"按钮

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift`
- Modify: `ios/xinlingyisheng/xinlingyisheng/Components/PhotoCapture/ChatNavBarV2.swift`

### Step 1: 在 ViewModel 中添加按钮可用性判断

**修改**: `ViewModels/UnifiedChatViewModel.swift`

在 `UnifiedChatViewModel` 类中添加计算属性：

```swift
// MARK: - 生成病历按钮可用性
var canGenerateDossier: Bool {
    // 至少需要5条消息（用户3条 + AI 2条）
    guard messages.count >= 5 else { return false }
    
    // 如果对话已完成，始终可以生成
    if isConversationCompleted { return true }
    
    // 检查是否有足够的对话轮次
    let userMessages = messages.filter { $0.sender == .user }
    return userMessages.count >= 3
}

var dossierButtonTooltip: String {
    if canGenerateDossier {
        return "根据本次对话生成结构化病历"
    } else {
        return "请继续对话收集更多信息后再生成病历"
    }
}
```

### Step 2: 修改 ChatNavBarV2 使用新的判断逻辑

**修改**: `Components/PhotoCapture/ChatNavBarV2.swift`

找到生成病历按钮部分，修改为：

```swift
// 生成病历按钮（仅当有回调且可用时显示）
if let onGenerate = onGenerateDossier {
    Button(action: {
        if viewModel.canGenerateDossier {
            onGenerate()
        }
    }) {
        Image(systemName: "doc.text.fill")
            .font(.system(size: ScaleFactor.fontSize(16)))
            .foregroundColor(viewModel.canGenerateDossier ? DXYColors.primary : DXYColors.textTertiary)
            .frame(width: ScaleFactor.size(44), height: ScaleFactor.size(44))
            .contentShape(Rectangle())
    }
    .disabled(!viewModel.canGenerateDossier)
    .accessibilityLabel("生成病历")
    .accessibilityHint(viewModel.dossierButtonTooltip)
}
```

### Step 3: 添加确认对话框

在 `UnifiedChatViewModel` 中修改 `manuallyGenerateDossier` 方法：

```swift
// MARK: - 手动生成病历
@Published var showGenerateConfirmation = false
@Published var generateConfirmationMessage = ""

func requestGenerateDossier() {
    // 检查是否可以生成
    if !canGenerateDossier {
        errorMessage = "对话信息不足，请继续描述您的症状"
        showError = true
        return
    }
    
    // 如果消息较少，显示确认对话框
    if messages.count < 8 {
        generateConfirmationMessage = "当前对话较少，生成的病历可能不够详细。是否继续生成？"
        showGenerateConfirmation = true
    } else {
        // 直接生成
        Task {
            await manuallyGenerateDossier()
        }
    }
}

func confirmGenerateDossier() {
    showGenerateConfirmation = false
    Task {
        await manuallyGenerateDossier()
    }
}

func manuallyGenerateDossier() async {
    guard let sessionId = sessionId else { return }
    guard let agentType = agentType else { return }
    
    do {
        let response = try await medicalEventService.aggregateSession(
            sessionId: sessionId,
            sessionType: agentType.rawValue
        )
        
        eventId = response.event_id
        isNewEvent = response.is_new_event
        shouldShowDossierPrompt = true
        isConversationCompleted = true
        
        print("[UnifiedChatVM] 病历生成成功: eventId=\(response.event_id), isNew=\(response.is_new_event)")
    } catch {
        handleError(error)
    }
}
```

### Step 4: 在视图中添加确认对话框

在使用 `UnifiedChatViewModel` 的视图中添加：

```swift
.alert("确认生成病历", isPresented: $viewModel.showGenerateConfirmation) {
    Button("取消", role: .cancel) {
        viewModel.showGenerateConfirmation = false
    }
    Button("继续生成") {
        viewModel.confirmGenerateDossier()
    }
} message: {
    Text(viewModel.generateConfirmationMessage)
}
```

### Step 5: 编译验证

```bash
cd ios/xinlingyisheng
xcodebuild -scheme xinlingyisheng -destination 'platform=iOS Simulator,name=iPhone 15 Pro' clean build
```

**预期**: 编译成功，无错误

### Step 6: 提交iOS改进

```bash
git add ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift
git add ios/xinlingyisheng/xinlingyisheng/Components/PhotoCapture/ChatNavBarV2.swift
git commit -m "feat(ios): add smart dossier button with validation and confirmation"
```

---

## Task 4: 端到端测试

**目标**: 验证完整的对话到病历生成流程

### Step 1: 启动后端服务

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8100
```

**预期**: 服务启动在 http://localhost:8100

### Step 2: 创建测试会话并对话

**使用 curl 测试**:

```bash
# 1. 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8100/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","password":"password123"}' \
  | jq -r '.access_token')

# 2. 创建会话
SESSION_ID=$(curl -s -X POST http://localhost:8100/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"dermatology"}' \
  | jq -r '.session_id')

echo "会话ID: $SESSION_ID"

# 3. 发送第一条消息
curl -X POST "http://localhost:8100/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"我皮肤很痒，有红疹"}' | jq

# 4. 发送第二条消息
curl -X POST "http://localhost:8100/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"主要在手臂和腿上，已经持续3天了"}' | jq

# 5. 发送第三条消息
curl -X POST "http://localhost:8100/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"晚上特别痒，抓了之后有点破皮"}' | jq
```

### Step 3: 尝试过早聚合（应该失败）

```bash
# 尝试聚合（此时信息可能还不完整）
curl -X POST http://localhost:8100/medical-events/aggregate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"session_type\":\"dermatology\"}" | jq
```

**预期输出**（如果信息不完整）:
```json
{
  "detail": "会话信息不完整: 尚未明确主诉、尚未收集到症状信息。请继续对话后再生成病历。"
}
```

### Step 4: 继续对话直到信息完整

```bash
# 继续发送消息，让智能体提取更多信息
curl -X POST "http://localhost:8100/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"没有接触过什么特殊的东西，就是突然开始痒的"}' | jq
```

### Step 5: 检查会话状态

```bash
python -c "
from app.database import SessionLocal
from app.models.session import Session
import json

db = SessionLocal()
try:
    session = db.query(Session).filter(Session.id == '$SESSION_ID').first()
    if session:
        state = session.agent_state
        print('主诉:', state.get('chief_complaint', '无'))
        print('症状:', state.get('symptoms', []))
        print('部位:', state.get('skin_location', '无'))
        print('持续时间:', state.get('duration', '无'))
        print('阶段:', state.get('stage', '无'))
finally:
    db.close()
"
```

### Step 6: 成功聚合

```bash
# 再次尝试聚合（应该成功）
curl -X POST http://localhost:8100/medical-events/aggregate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"session_type\":\"dermatology\"}" | jq
```

**预期输出**:
```json
{
  "event_id": "1",
  "message": "会话已聚合到病历事件",
  "is_new_event": true,
  "session_summary": {
    "chief_complaint": "皮肤瘙痒伴红疹",
    "symptoms": ["pruritus", "rash"],
    "risk_level": "low",
    "message_count": 8,
    "has_images": false
  }
}
```

### Step 7: 验证病历事件

```bash
# 获取病历事件详情
EVENT_ID=$(curl -s -X POST http://localhost:8100/medical-events/aggregate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SESSION_ID\",\"session_type\":\"dermatology\"}" \
  | jq -r '.event_id')

curl -X GET "http://localhost:8100/medical-events/$EVENT_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**预期**: 返回完整的病历事件，包含会话数据、主诉、症状、对话历史

### Step 8: 记录测试结果

创建测试报告: `backend/test_results_2026-01-15.md`

```markdown
# 端到端测试报告

**测试日期**: 2026-01-15
**测试人员**: 系统测试

## 测试场景1: 信息不完整时聚合

- ✅ 后端正确拒绝，返回详细错误信息
- ✅ 错误信息清晰指出缺少哪些信息

## 测试场景2: 完整对话后聚合

- ✅ 成功创建病历事件
- ✅ agent_state 中的信息正确提取
- ✅ 对话历史完整保存
- ✅ 主诉和症状正确显示

## 测试场景3: 数据完整性

- ✅ sessions 表正确保存 agent_state
- ✅ messages 表正确保存对话历史
- ✅ medical_events 表正确保存聚合结果

## 结论

所有测试通过 ✅
```

---

## Task 5: 文档更新

**目标**: 更新相关文档，记录改进内容

### Step 1: 更新 API_CONTRACT.md

在 `docs/API_CONTRACT.md` 的聚合接口部分添加错误响应说明：

```markdown
#### 错误响应

**400 Bad Request** - 会话信息不完整

```json
{
  "detail": "会话信息不完整: 尚未明确主诉、尚未收集到症状信息。请继续对话后再生成病历。"
}
```

**可能的验证错误**:
- "尚未明确主诉" - chief_complaint 为空
- "尚未收集到症状信息" - symptoms 数组为空
- "对话刚开始，请先描述您的问题" - stage 为 "greeting"
- "对话信息太少，请继续描述症状" - 消息数少于3条
```

### Step 2: 更新 CHANGELOG.md

```markdown
## [Unreleased]

### Added
- 数据库清理脚本，支持完全清理模式
- 聚合接口数据完整性验证，提供详细错误信息
- iOS 客户端智能按钮，根据对话状态动态显示
- 生成病历前的确认对话框

### Changed
- 改进聚合验证逻辑，提供更友好的错误提示
- 优化 agent_state 数据提取流程

### Fixed
- 修复过早聚合导致病历信息不完整的问题
- 清理旧的测试数据和空壳病历事件

### Documentation
- 添加完整的会话数据流全局分析文档
- 更新 API 契约文档，补充错误响应说明
```

### Step 3: 提交文档更新

```bash
git add docs/API_CONTRACT.md
git add CHANGELOG.md
git add backend/test_results_2026-01-15.md
git commit -m "docs: update API contract and changelog with validation improvements"
```

---

## Task 6: 最终验证和清理

### Step 1: 运行完整测试套件

```bash
cd backend
pytest tests/ -v
```

**预期**: 所有测试通过

### Step 2: 检查代码质量

```bash
# 检查 Python 代码风格
flake8 app/ --max-line-length=120

# 检查类型提示
mypy app/ --ignore-missing-imports
```

### Step 3: 验证数据库状态

```bash
python scripts/cleanup_incomplete_events.py --stats
```

**预期输出**:
```
=== 数据库统计 ===

统一会话表 (sessions): 1 条  # 测试会话
消息表 (messages): 8 条       # 测试消息
病历事件表 (medical_events): 1 条  # 测试病历
旧会话表:
  - derma_sessions: 0 条
  - diagnosis_sessions: 0 条
```

### Step 4: 创建最终提交

```bash
git add -A
git commit -m "feat: complete session data cleanup and optimization

- Add full database cleanup script
- Improve aggregate validation with detailed errors
- Add iOS smart dossier button with confirmation
- Update documentation and add test reports

Closes #[issue-number]"
```

### Step 5: 推送到远程仓库

```bash
git push origin main
```

---

## 验收标准

### 后端
- ✅ 数据库清理脚本可以完全清理所有数据
- ✅ 聚合接口正确验证数据完整性
- ✅ 错误信息清晰指出缺少哪些信息
- ✅ 完整对话后可以成功生成病历

### iOS客户端
- ✅ "生成病历"按钮根据对话状态动态显示
- ✅ 信息不足时按钮禁用并显示提示
- ✅ 对话较少时显示确认对话框
- ✅ 编译无错误和警告

### 数据完整性
- ✅ agent_state 正确保存主诉、症状等信息
- ✅ 聚合时正确读取 agent_state
- ✅ 病历事件包含完整的会话数据
- ✅ 无旧数据污染

### 文档
- ✅ API 契约文档更新
- ✅ CHANGELOG 记录所有改动
- ✅ 测试报告完整
- ✅ 架构分析文档准确

---

## 回滚计划

如果出现问题，可以回滚：

```bash
# 恢复数据库备份（如果有）
pg_restore -d home_health backup_before_cleanup.sql

# 回滚代码
git revert HEAD
git push origin main
```

---

## 注意事项

1. **数据备份**: 执行完全清理前，确认不需要保留任何数据
2. **测试环境**: 先在测试环境验证，再在生产环境执行
3. **用户通知**: 如果是生产环境，提前通知用户数据清理
4. **监控**: 清理后监控系统运行状态
5. **文档**: 及时更新所有相关文档

---

**计划创建时间**: 2026-01-15  
**预计执行时间**: 2-3小时  
**风险等级**: 中（涉及数据删除）
