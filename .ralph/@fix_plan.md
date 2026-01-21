# 医生分身系统完善 - 任务计划

## Phase 1: 查病查药数据导入 (P0)

### 数据源准备
- [x] 确认数据模型已完整（Disease、Drug 模型字段齐全）
- [x] 创建 `backend/scripts/import_medical_data.py` - 支持 CSV/JSON 导入
- [x] 创建 `backend/scripts/seed_extended_data.py` - 扩展种子数据

### 数据导入执行
- [x] 导入脚本已创建
- [ ] 在服务器上执行: `python3 scripts/seed_extended_data.py`
- [ ] 验证疾病数据 ≥1000 条
- [ ] 验证药品数据 ≥500 条

---

## Phase 2: iOS 查病查药详情页 (P1)

### 疾病详情页
- [ ] 创建 DiseaseDetailView.swift
- [ ] 显示完整疾病信息（症状、病因、诊断、治疗、预防、护理）
- [ ] 实现列表跳转到详情页

### 药品详情页
- [ ] 创建 MedicationDetailView.swift
- [ ] 显示完整药品信息（适应症、禁忌、用量、副作用、注意事项）
- [ ] 实现列表跳转到详情页

---

## Phase 3: 医生分身对话式采集 (P2)

### 后端 API
- [ ] 创建 `/admin/doctors/{id}/persona-chat` WebSocket 端点
- [ ] 实现对话式采集流程逻辑
- [ ] 实时生成并更新 `ai_persona_prompt`
- [ ] 支持医生确认/调整

### 采集维度实现
- [ ] 问诊顺序提取
- [ ] 关注重点提取
- [ ] 沟通风格识别
- [ ] 处方习惯分析
- [ ] 生活建议模板

### 前端界面
- [ ] 管理后台：对话式采集页面
- [ ] 实时对话 UI
- [ ] 生成结果预览/编辑

### 数据模型更新
- [ ] Doctor 模型添加 `persona_completed` 字段
- [ ] 更新 Doctor schema

---

## Phase 4: 病历分析功能 (P2)

### 后端 API
- [ ] 创建 `/admin/doctors/{id}/analyze-records` 端点
- [ ] 实现病历文件上传
- [ ] AI 分析提取特征（诊断思路、用药规律、随访习惯）
- [ ] 更新 `knowledge_base_id` 和 `ai_persona_prompt`

### 前端界面
- [ ] 管理后台：病历上传页面
- [ ] 分析结果展示

### 数据模型更新
- [ ] Doctor 模型添加 `records_analyzed` 字段
- [ ] 更新 Doctor schema

---

## Phase 5: 其他界面功能 (P3)

### iOS 患者端
- [ ] 病历资料夹：PDF 导出
- [ ] 病历资料夹：笔记添加/编辑
- [ ] 问医生：图片消息完整流程
- [ ] 问医生：语音消息完整流程
- [ ] 个人中心：设置页面
- [ ] 个人中心：意见反馈

### 管理后台
- [ ] 知识库管理：文档上传
- [ ] 知识库管理：重新索引
- [ ] 知识库管理：文档列表
- [ ] 医生管理：编辑功能
- [ ] 医生管理：激活/停用
- [ ] 医生管理：分身配置
- [ ] 数据统计：真实数据图表
- [ ] 数据统计：趋势分析

---

## 验收标准
- [ ] 疾病库导入 ≥1000 条真实数据
- [ ] 药品库导入 ≥500 条真实数据
- [ ] iOS 查病查药详情页可正常跳转
- [ ] 对话式采集可在 15 分钟内完成
- [ ] 生成的 ai_persona_prompt 可用
- [ ] 病历分析可正确提取特征

---

## 已完成
- [x] Ralph 项目初始化
- [x] 计划文档导入
- [x] 数据导入脚本创建（import_medical_data.py + seed_extended_data.py）
- [x] nginx 添加患者端 API 代理支持
- [x] iOS API URL 更新为生产地址
- [x] GitHub 分支切换为 main

---

## 备注
- 优先级：P0 > P1 > P2 > P3
- 每完成一个任务，更新此文件标记 [x]
- 遇到问题在 Notes 中记录

## 下一步
在服务器上执行扩展数据导入：
```bash
cd /opt/home-health/source/backend
python3 scripts/seed_extended_data.py
```
