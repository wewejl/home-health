# 医生分身系统完善 - 技术需求规范

## 一、查病查药真实数据方案

### 1.1 数据源

| 数据类型 | 数据源 | 数量 | 字段要求 |
|---------|--------|------|---------|
| **疾病数据** | ICD-10 国家标准编码 | ~1.4万条 | 编码、名称、分类、科室关联 |
| **药品数据** | 国家药监局数据库 | ~15万条 | 批准文号、生产企业、适应症 |

### 1.2 数据模型要求

#### Disease 模型需补充字段
```python
overview: str      # 疾病概述
symptoms: str      # 症状描述
causes: str        # 病因分析
diagnosis: str     # 诊断方法
treatment: str     # 治疗方案
prevention: str    # 预防措施
care: str          # 护理建议
```

#### Medication 模型需补充字段
```python
indications: str           # 适应症
contraindications: str     # 禁忌症
dosage: str               # 用法用量
side_effects: str         # 副作用
precautions: str          # 注意事项
```

### 1.3 数据导入脚本要求

**文件路径**: `backend/scripts/import_medical_data.py`

**功能要求**:
- 支持 ICD-10 CSV 格式导入
- 支持药监局数据库格式导入
- 批量处理，显示进度条
- 错误日志记录到 `logs/import_errors.log`
- 保留原有种子数据
- 支持增量更新（不重复导入）

---

## 二、iOS 查病查药详情页

### 2.1 DiseaseDetailView.swift

**文件路径**: `ios/xinlingyisheng/Views/Consultation/DiseaseDetailView.swift`

**UI 要求**:
- 使用 `DXYColors.primaryPurple` 主题色
- 使用 `AdaptiveFont` 自适应字体
- 使用 `ScaleFactor.padding` 自适应间距

**显示内容**:
- 疾病名称（标题）
- 疾病概述
- 症状
- 病因
- 诊断方法
- 治疗方案
- 预防措施
- 护理建议

### 2.2 MedicationDetailView.swift

**文件路径**: `ios/xinlingyisheng/Views/Consultation/MedicationDetailView.swift`

**UI 要求**: 同 DiseaseDetailView

**显示内容**:
- 药品名称（标题）
- 适应症
- 禁忌症
- 用法用量
- 副作用
- 注意事项

### 2.3 列表跳转

在现有的查病查药列表中添加点击跳转逻辑。

---

## 三、医生分身对话式采集功能

### 3.1 后端 WebSocket API

**端点**: `/admin/doctors/{id}/persona-chat`

**功能**:
- WebSocket 长连接对话
- AI 引导式提问（预设问题模板）
- 实时提取特征并更新 `ai_persona_prompt`
- 支持医生确认/调整

**对话流程**:
```
1. AI: 问候，介绍流程
2. AI: "当患者说[症状]时，您通常会怎么问？"
3. 医生: 回答
4. AI: 追问细节
5. ... (重复)
6. AI: 生成 ai_persona_prompt 摘要
7. 医生: 确认/调整
8. 完成
```

### 3.2 采集维度

| 维度 | 预设问题 | 生成内容 |
|------|----------|----------|
| 问诊顺序 | "当患者说XXX时，您会怎么问？" | prompt 中的问诊流程 |
| 关注重点 | "您最关注哪些症状/指标？" | prompt 中的重点关注项 |
| 沟通风格 | "您习惯怎么跟患者沟通？" | prompt 中的语气设定 |
| 处方习惯 | "您用药保守还是积极？" | prompt 中的用药原则 |
| 生活建议 | "您常给患者什么建议？" | prompt 中的建议模板 |

### 3.3 前端界面

**管理后台页面**: `frontend/src/pages/admin/DoctorPersonaChat.tsx`

**功能**:
- 实时聊天界面
- 对话历史展示
- AI 生成结果预览
- 编辑/确认按钮

### 3.4 数据模型更新

**Doctor 模型新增字段**:
```python
persona_completed: bool = False  # 对话采集是否完成
records_analyzed: bool = False   # 病历分析是否完成
```

---

## 四、病历分析功能

### 4.1 后端 API

**端点**: `POST /admin/doctors/{id}/analyze-records`

**请求**:
```json
{
  "records": [
    {
      "patient_complaint": "主诉",
      "diagnosis": "诊断",
      "prescription": "处方",
      "follow_up": "随访"
    }
  ]
}
```

**响应**:
```json
{
  "analysis": {
    "diagnostic_patterns": ["常见诊断思路1", "常见诊断思路2"],
    "prescription_habits": ["用药习惯1"],
    "follow_up_style": "随访习惯描述"
  },
  "updated_persona_prompt": "补充后的完整 prompt"
}
```

### 4.2 前端界面

**管理后台页面**: `frontend/src/pages/admin/DoctorRecordAnalysis.tsx`

**功能**:
- 上传病历文件（JSON/CSV）
- 显示分析结果
- 一键应用到 ai_persona_prompt

---

## 五、验收标准

### 5.1 数据导入
- [ ] 疾病库 ≥1000 条真实数据
- [ ] 药品库 ≥500 条真实数据
- [ ] 数据完整无缺失
- [ ] 科室关联正确

### 5.2 iOS 详情页
- [ ] 疾病详情页正确显示所有字段
- [ ] 药品详情页正确显示所有字段
- [ ] 列表点击可跳转
- [ ] UI 符合设计规范

### 5.3 对话式采集
- [ ] 15分钟内可完成采集
- [ ] 生成的 ai_persona_prompt 可用
- [ ] 支持修改确认

### 5.4 病历分析
- [ ] 正确上传病历
- [ ] 正确提取特征
- [ ] 正确更新知识库
