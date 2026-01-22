# Phase 5 剩余功能实施计划

**创建日期:** 2026-01-22
**状态:** 🚧 进行中

---

## 一、项目现状

### 1.1 已完成 (Phase 1-4)

| Phase | 功能 | 状态 |
|-------|------|------|
| Phase 1 | 查病查药数据导入 (1701 疾病 + 641 药品) | ✅ |
| Phase 2 | iOS 查病查药详情页 | ✅ |
| Phase 3 | 医生分身对话式采集 UI | ✅ |
| Phase 4 | 病历分析功能 | ✅ |
| - | LangGraph 架构重构 | ✅ |
| - | ReAct 智能体设计 | ✅ |
| - | 流式响应设计 | ✅ |
| - | 代码审核修复 | ✅ |

### 1.2 待完成 (Phase 5)

| 优先级 | 功能 | 组件 | 预计工时 |
|--------|------|------|----------|
| P3 | 知识库文档上传 | 管理后台 | 2-3h |
| P3 | 数据统计图表 | 管理后台 | 3-4h |
| P3 | 病历笔记编辑 | iOS | 2-3h |
| P3 | 图片消息 | iOS | 2-3h |
| P3 | 语音消息 | iOS | 4-6h |
| P4 | 短信网关 | 后端 | 2-3h |
| P4 | 埋点系统 | 全栈 | 3-4h |

---

## 二、实施计划

### 2.1 管理后台: 知识库文档上传 (P3)

**目标:** 支持上传 PDF/Word/图片文档，自动提取文本并入库

**涉及文件:**
- `backend/app/routes/admin_knowledge.py` - 添加文件上传 API
- `frontend/src/pages/Knowledge.tsx` - 添加上传 UI

**技术要点:**
- 使用 multipart/form-data 处理文件上传
- 后端: PyPDF2 / python-docx 提取文本
- 前端: Ant Design Upload + Upload.Dragger
- 文件大小限制: 10MB

---

### 2.2 管理后台: 数据统计图表 (P3)

**目标:** 将表格数据可视化，使用图表展示趋势

**涉及文件:**
- `frontend/src/pages/Dashboard.tsx` (或类似页面)

**技术要点:**
- 使用 ECharts 或 Recharts
- 图表类型: 折线图 (问诊量趋势)、饼图 (科室分布)
- 数据从现有 API 获取

---

### 2.3 iOS: 病历笔记编辑 (P3)

**目标:** 在病历资料夹中添加/编辑笔记

**涉及文件:**
- `ios/xinlingyisheng/xinlingyisheng/ViewModels/MedicalDossierViewModel.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/MedicalDossierDetailView.swift`

**技术要点:**
- 添加笔记编辑 UI (TextField + TextEditor)
- 调用后端 API 保存笔记
- 遵循 iOS 设计规范 (DXYColors, AdaptiveFont)

---

### 2.4 iOS: 图片消息 (P3)

**目标:** 问医生支持发送/接收图片

**涉及文件:**
- `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift`
- `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift`

**技术要点:**
- PhotosUI 框架选择图片
- multipart/form-data 上传
- 消息类型扩展 (image 类型)

---

### 2.5 iOS: 语音消息 (P3)

**目标:** 问医生支持语音消息

**参考文档:** `docs/plans/completed/2026-01-18-voice-call-implementation-plan.md`

**涉及文件:**
- `ios/xinlingyisheng/xinlingyisheng/Services/RealtimeSpeechService.swift` (新建)
- `ios/xinlingyisheng/xinlingyisheng/Services/SpeechSynthesisService.swift` (新建)
- `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift` (扩展)

**技术要点:**
- Speech Framework 实现语音识别
- AVAudioEngine 录制音频
- VAD (语音活动检测)
- TTS 语音播报

---

### 2.6 生产配置: 短信网关 (P4)

**目标:** 接入阿里云短信服务

**涉及文件:**
- `backend/app/services/sms_service.py`

**技术要点:**
- 替换模拟短信为真实 API
- 配置 ALIYUN_SMS_ACCESS_KEY_ID/SECRET
- 模板管理

---

### 2.7 生产配置: 埋点系统 (P4)

**目标:** 接入用户行为分析系统

**涉及文件:**
- 多处 `// TODO: 接入正式埋点系统` 注释位置

**技术要点:**
- 选择埋点方案 (神策/GrowingIO/自建)
- 定义事件规范
- iOS/前端/后端统一事件格式

---

## 三、待清理事项

### 3.1 文档清理

`docs/plans/` 根目录下存在重复文件（已在 completed/ 添加状态标记），需手动删除：

```bash
rm docs/plans/2026-01-18-voice-mode-professional.md
```

### 3.2 临时文件清理

```bash
rm docs/plans/organize.sh
rm docs/plans/153c6c800c3dd4191cef0b2f8525b304.jpg
```

---

## 四、下次循环任务

**推荐顺序:**
1. 知识库文档上传 (P3，后端 + 前端，影响用户体验)
2. 数据统计图表 (P3，仅前端，快速见效)
3. iOS 图片消息 (P3，需求明确)
4. iOS 语音消息 (P3，有设计文档参考)
5. iOS 笔记编辑 (P3)
6. 短信网关 (P4，生产配置)
7. 埋点系统 (P4，生产配置)

---

## 五、状态标记说明

- ✅ 已完成
- 🚧 进行中
- ⏳ 待开始
- 🚫 已取消
