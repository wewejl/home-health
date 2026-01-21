# 医生分身系统完善 - 任务计划

## Phase 1: 查病查药数据导入 (P0) ✅ 已完成

### 数据源准备
- [x] 确认数据模型已完整（Disease、Drug 模型字段齐全）
- [x] 创建 `backend/scripts/import_medical_data.py` - 支持 CSV/JSON 导入
- [x] 创建 `backend/scripts/seed_extended_data.py` - 扩展种子数据

### 数据导入执行
- [x] 导入脚本已创建
- [x] 在服务器上执行数据导入
- [x] 验证疾病数据 ≥1000 条 (实际: 1701 条)
- [x] 验证药品数据 ≥500 条 (实际: 641 条)
- [x] 数据已提交到 Git
- [x] SSH 配置已保存 (~/.ssh/config)
- [x] 数据同步脚本已创建 (scripts/sync_data.sh)

---

## Phase 2: iOS 查病查药详情页 (P1) ✅ 已完成

### 疾病详情页
- [x] 创建 DiseaseDetailView.swift
- [x] 显示完整疾病信息（症状、病因、诊断、治疗、预防、护理）
- [x] 实现列表跳转到详情页

### 药品详情页
- [x] 创建 DrugDetailView.swift
- [x] 显示完整药品信息（功效作用、用药禁忌、用法用量）
- [x] 实现列表跳转到详情页

---

## Phase 3: 医生分身对话式采集 (P2) ✅ 已完成

### 后端 API
- [x] 创建 `/admin/doctors/{id}/persona-chat` 后端 API
- [x] 实现对话式采集流程逻辑 (persona_collection_service.py)

### 前端 UI (2026-01-21 完成)
- [x] `frontend/src/pages/admin/DoctorPersonaChat.tsx` - 对话式采集主页面
- [x] `frontend/src/pages/admin/DoctorPersonaChat.css` - 样式文件
- [x] `frontend/src/api/index.ts` - 添加 personaChatApi
- [x] `frontend/src/App.tsx` - 添加路由 `/admin/doctors/:id/persona`
- [x] `frontend/src/pages/Doctors.tsx` - 添加「配置分身」入口按钮

### 功能特性
- 7 个阶段进度可视化 (greeting → specialty → style → approach → prescription → advice → summary)
- 聊天式 UI (AI 消息左侧、用户消息右侧)
- 完成后显示生成的 Prompt 预览
- 确认保存 / 重新配置 / 返回列表操作
- 未完成离开时的保护提示

---

## Phase 4: 病历分析功能 (P2) ❌ 未开始

### 待实现
- [ ] 创建 `/admin/doctors/{id}/analyze-records` 端点
- [ ] 实现病历文件上传
- [ ] AI 分析提取特征（诊断思路、用药规律、随访习惯）
- [ ] 更新 `knowledge_base_id` 和 `ai_persona_prompt`
- [ ] Doctor 模型添加 `records_analyzed` 字段

---

## Phase 5: 其他界面功能 (P3) ⚠️ 部分完成

### iOS 患者端
- [x] 个人中心：ProfileView.swift (基础界面)
- [x] 个人中心：ProfileSetupView.swift (用户设置)
- [x] 问诊历史：SessionHistoryView.swift
- [ ] 病历资料夹：PDF 导出
- [ ] 病历资料夹：笔记添加/编辑
- [ ] 问医生：图片消息完整流程
- [ ] 问医生：语音消息完整流程
- [ ] 个人中心：设置页面
- [ ] 个人中心：意见反馈

### 管理后台
- [x] 知识库管理：Knowledge.tsx (文档列表)
- [x] 知识库管理：重新索引 (reindex API)
- [ ] 知识库管理：文档上传 (目前只支持文本输入)
- [x] 医生管理：Doctors.tsx 编辑功能
- [x] 医生管理：激活/停用 (Switch组件)
- [x] 医生管理：分身配置 (AI配置Tab: 模型/温度/Prompt/知识库)
- [x] 医生管理：对话式配置入口
- [x] 数据统计：Stats.tsx (趋势数据表格)
- [ ] 数据统计：真实数据图表 (目前是表格展示)
- [x] 反馈管理：Feedbacks.tsx

---

## 验收标准
- [x] 疾病库导入 ≥1000 条真实数据 (实际: 1701 条)
- [x] 药品库导入 ≥500 条真实数据 (实际: 641 条)
- [x] iOS 查病查药详情页可正常跳转 (DiseaseDetailView.swift + DrugDetailView.swift)
- [x] 对话式采集 UI 完成
- [ ] 对话式采集可在 15 分钟内完成 (待测试)
- [ ] 生成的 ai_persona_prompt 可用 (待测试)
- [ ] 病历分析可正确提取特征

---

## 已完成
- [x] Ralph 项目初始化
- [x] 计划文档导入
- [x] 数据导入脚本创建（import_medical_data.py + seed_extended_data.py + crawl_dxy_drugs.py）
- [x] 数据导入完成：1701 条疾病 + 641 条药品
- [x] nginx 添加患者端 API 代理支持
- [x] iOS API URL 更新为生产地址
- [x] GitHub 分支切换为 main
- [x] 服务器 SSH 配置保存 (~/.ssh/config)
- [x] 数据同步脚本创建 (scripts/sync_data.sh + deploy_data.sh)
- [x] Phase 3 前端对话式采集 UI 完成

## 代码实现情况总结

| Phase | 状态 | 说明 |
|-------|------|------|
| Phase 1 | ✅ 100% | 数据导入完成并部署到服务器 |
| Phase 2 | ✅ 100% | iOS 详情页已实现 (DiseaseDetailView.swift + DrugDetailView.swift) |
| Phase 3 | ✅ 100% | 后端 API + 前端对话式采集 UI 完成 |
| Phase 4 | ❌ 0% | 病历分析功能未开始 |
| Phase 5 | ⚠️ 65% | 部分功能已实现 (见上方详细列表) |

---

## 备注
- 优先级：P0 > P1 > P2 > P3
- 每完成一个任务，更新此文件标记 [x]
- 遇到问题在 Notes 中记录

## 下一步

### 优先级 1: Phase 4 病历分析功能 (P2)
- [ ] 创建 `/admin/doctors/{id}/analyze-records` 端点
- [ ] 实现病历文件上传 (PDF/图片)
- [ ] AI 分析提取特征（诊断思路、用药规律、随访习惯）
- [ ] 自动更新 `knowledge_base_id` 和 `ai_persona_prompt`
- [ ] 添加 `records_analyzed` 字段到 Doctor 模型

### 优先级 2: Phase 5 剩余功能 (P3)
- [ ] 知识库管理：文档上传 (文件上传组件)
- [ ] 数据统计：图表可视化 (ECharts/Recharts)
- [ ] iOS：病历资料夹 PDF 导出
- [ ] iOS：图片/语音消息完整流程
