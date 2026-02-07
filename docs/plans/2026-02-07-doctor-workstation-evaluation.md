# 医生工作站方案评估报告

> 评估日期: 2026-02-07
> 评估目标: 整体评估医生工作站设计方案的合理性

---

## 一、现有系统架构分析

### 1.1 用户体系现状

| 表名 | 用途 | 登录能力 | 现状 |
|------|------|----------|------|
| `users` | 患者/普通用户 | ✅ 有 `password_hash` | 生产使用 |
| `admin_users` | 管理员/工作人员 | ✅ 有 `password_hash` | 生产使用 |
| `doctors` | AI医生配置 | ❌ **无登录字段** | 仅作为AI分身配置 |

### 1.2 数据关联现状

```
┌─────────────┐
│   users     │ ← 患者
└──────┬──────┘
       │
       ├─→ sessions (doctor_id → doctors.id) ✓
       │
       └─→ medical_orders (doctor_id → admin_users.id) ⚠️
              └─→ task_instances
              └─→ completion_records
```

**核心问题**: 同一个 `doctor_id` 字段在不同表中指向不同的表！

---

## 二、方案合理性评估

### 2.1 架构设计 - ⚠️ 部分合理，存在隐患

| 决策 | 评估 | 说明 |
|------|------|------|
| 独立的前端 `/doctor/*` | ✅ 合理 | 职责分离，易于维护 |
| 独立的 API `/api/doctor/*` | ✅ 合理 | API 命名空间清晰 |
| 扩展 `doctors` 表添加登录 | ⚠️ 有风险 | 见下文分析 |
| 创建独立的 `frontend/doctor/` | ❓ 可优化 | 见建议 |

### 2.2 数据模型设计 - ❌ 存在严重问题

#### 问题 1: doctor_id 语义混乱

```python
# Session.doctor_id → doctors.id (AI医生分身)
doctor_id = Column(Integer, ForeignKey("doctors.id"))

# MedicalOrder.doctor_id → admin_users.id (真实医生)
doctor_id = Column(Integer, ForeignKey("admin_users.id"))
```

**影响**: 代码语义不清晰，容易混淆"AI医生"和"真实医生"。

#### 问题 2: 扩展 doctors 表添加登录的合理性存疑

现有 `doctors` 表的核心用途是 **AI 分身配置**：

```python
# Doctor 模型的核心字段
ai_persona_prompt = Column(Text, nullable=True)      # AI 提示词
ai_model = Column(String(50), default="qwen-plus")  # AI 模型
ai_temperature = Column(Float, default=0.7)         # AI 温度
agent_type = Column(String(20), default="simple")   # 智能体类型
```

**问题**: 将"真实医生登录"和"AI分身配置"混在一个表里，概念混淆。

---

## 三、根本问题分析

### 3.1 概念混淆

方案中存在三个不同的"医生"概念：

| 概念 | 对应表 | 用途 |
|------|--------|------|
| AI医生分身 | `doctors` | 患者咨询的AI对话角色 |
| 真实医生 | (未定义) | 看病、下医嘱的真实医生 |
| 管理员 | `admin_users` | 后台管理用户 |

**当前方案错误地假设**: `doctors` 表 = 真实医生

实际上: `doctors` 表 = AI 分身配置

### 3.2 需求澄清

医生工作台的"医生"指的是谁？

1. **如果是指"真实医生"** (人类医生，看病下医嘱):
   - 需要新建 `real_doctors` 或 `physicians` 表
   - 或在 `admin_users` 中增加角色区分

2. **如果是指"AI分身管理员"** (管理AI医生配置的人):
   - 不需要新表，直接用 `admin_users`
   - 当前 `doctors` 表只是配置，不是人

---

## 四、改进建议

### 方案 A: 明确概念（推荐）

#### 4.1 数据模型调整

```
users          → 患者
admin_users    → 管理员 + 真实医生 (通过 role 区分)
doctors        → AI 分身配置 (保持现状)
```

**调整 `admin_users` 表**:

```python
# 添加角色类型
class AdminRole(str, enum.Enum):
    ADMIN = "admin"          # 系统管理员
    DOCTOR = "doctor"        # 真实医生
    EDITOR = "editor"        # 内容编辑
    REVIEWER = "reviewer"    # 审核员

# 在 AdminUser 中
role = Column(String(20), default="editor")
doctor_attributes = Column(JSON, nullable=True)  # 医生专属属性
```

#### 4.2 医嘱关联调整

```python
# MedicalOrder.doctor_id 保持指向 admin_users
# 但语义变为:
# - 当 ai_generated=True 时，关联到创建医嘱的管理员
# - 当 ai_generated=False 时，关联到真实的医生用户
```

#### 4.3 前端架构

**不需要新建 `frontend/doctor/` 目录**，而是在现有 admin 后台中：

```
frontend/src/
├── pages/
│   ├── admin/           # 管理员专用
│   ├── doctor/          # 医生工作台 (新建)
│   └── ...              # 其他共享页面
```

### 方案 B: 创建独立的真实医生表

#### 4.1 新建 `physicians` 表

```python
class Physician(Base):
    __tablename__ = "physicians"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("admin_users.id"))  # 关联登录账号
    name = Column(String(50), nullable=False)
    title = Column(String(50))  # 主治医师/主任医师等
    specialty = Column(String(100))
    license_no = Column(String(50))  # 医师资格证号
    ...
```

#### 4.2 调整医嘱关联

```python
# MedicalOrder 添加新字段
physician_id = Column(Integer, ForeignKey("physicians.id"), nullable=True)
# doctor_id 保留，用于历史数据兼容
```

---

## 五、具体问题列表

### 5.1 设计文档问题

| 问题 | 严重程度 | 位置 |
|------|----------|------|
| 假设 `doctors` 表 = 真实医生 | 🔴 高 | 设计文档第55行 |
| `doctor_id` 外键不一致说明不清晰 | 🟡 中 | 实施计划第22行 |
| 前端架构过度分离 | 🟡 中 | 设计文档第52行 |
| 缺少"真实医生" vs "AI分身"的区分 | 🔴 高 | 整体 |

### 5.2 实施计划问题

| 问题 | 严重程度 | 位置 |
|------|----------|------|
| Task 1: 扩展 doctors 表可能导致概念混乱 | 🔴 高 | Phase 0 |
| 缺少数据迁移计划 | 🟡 中 | 无 |
| 测试模式假设可能不适用生产 | 🟡 中 | Task 4 |

---

## 六、建议的实施路径

### 短期（MVP）

1. **澄清需求**: 医生工作台的"医生"是谁？
2. **选择方案 A**: 在 `admin_users` 中增加 `DOCTOR` 角色
3. **前端复用**: 在现有 `frontend/` 中添加 `pages/doctor/` 目录
4. **保持外键**: `MedicalOrder.doctor_id` 继续指向 `admin_users`

### 长期（如果需要）

1. 创建 `physicians` 表存储真实医生信息
2. `doctors` 表重命名为 `ai_personas` 更清晰
3. 建立医生 -> AI 分身的关联关系

---

## 七、结论

### 7.1 当前方案评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 需求理解 | 3/10 | 混淆了AI分身和真实医生 |
| 架构设计 | 5/10 | 前端过度分离，后端外键混乱 |
| 实施可行性 | 6/10 | 可以实施，但会留下技术债 |
| 长期可维护性 | 4/10 | 概念混淆会导致后续维护困难 |

### 7.2 建议

**不建议按当前方案实施**，建议：

1. ✅ 先澄清"医生"的定义
2. ✅ 选择方案 A（扩展 admin_users 角色）
3. ✅ 重命名相关概念以更清晰
4. ❌ 不要修改 `doctors` 表添加登录字段

---

## 八、待确认问题

在开始实施前，需要确认：

1. 医生工作台的"医生"是真实人类医生还是AI分身管理员？
2. 真实医生是否需要独立于 `admin_users` 的表？
3. `doctors` 表的未来定位：仅AI配置还是也包括真实医生？
