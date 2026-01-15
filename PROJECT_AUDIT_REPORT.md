# 项目结构审核报告

**审核日期**: 2026-01-15  
**重构完成日期**: 2026-01-15  
**审核范围**: home-health 全栈项目  
**审核人**: AI 产品经理 + iOS 开发专家

---

## 📋 执行摘要

~~本次审核发现项目存在**文档混乱、代码冗余、架构不一致**三大核心问题。~~

### ✅ 重构已完成

P1级问题已全部修复，项目结构已优化整理。

### 关键发现
- 🔴 **P0级问题**: 数据库架构不一致导致病历功能100%不可用 (**待修复** - 需要执行数据迁移脚本)
- ✅ ~~**P1级问题**: 文档和代码组织混乱~~ **已修复**
- ✅ ~~**优化建议**: 补充开发文档~~ **已完成**

---

## 🔴 严重问题 (P0 - 立即修复)

### 1. 数据库架构不一致 - 病历功能完全不可用

**问题描述**:
- iOS客户端使用统一的 `sessions` 表创建会话
- 后端病历聚合接口查询 `derma_sessions` 和 `diagnosis_sessions` 表
- 表不匹配导致永远查询不到数据，系统生成假数据填充

**影响范围**:
- ✗ 100%的病历生成功能不可用
- ✗ 所有科室受影响（皮肤科、心血管科、骨科、全科等）
- ✗ 已生成的病历资料均为假数据

**解决方案**:
参考 `PRD_会话架构重构方案.md` 第4-8章节，执行以下步骤:

1. **统一会话数据模型** (2天)
   - 使用 `sessions` 表 + `agent_state` JSON字段存储所有科室状态
   - 迁移 `derma_sessions` 和 `diagnosis_sessions` 数据到 `sessions`
   - 重构 `/api/medical-events/aggregate` 接口

2. **数据迁移** (1天)
   ```bash
   python backend/migrations/migrate_derma_sessions.py
   python backend/migrations/migrate_diagnosis_sessions.py
   python backend/migrations/verify_migration.py
   ```

3. **验证测试** (0.5天)
   - 测试所有科室的病历生成功能
   - 验证历史数据完整性

**优先级**: 🔴 P0 (最高优先级)  
**预计工时**: 3.5天

---

## 🟡 中等问题 (P1 - 本周内修复)

### 2. 文档组织混乱

**问题清单**:

| 问题 | 当前状态 | 建议操作 |
|------|---------|---------|
| PRD文档放在根目录 | `PRD_会话架构重构方案.md` (1186行)<br>`PRD_科室智能体问诊界面重构方案.md` (1127行) | 移动到 `docs/prd/` 目录 |
| 重复的iOS规范 | `/ios.md`<br>`/.windsurf/rules/ios.md` | 删除根目录的 `ios.md`，保留 `.windsurf/rules/ios.md` |
| 缺少关键文档 | ❌ `docs/API_CONTRACT.md`<br>❌ `docs/DEVELOPMENT_GUIDELINES.md`<br>❌ `docs/IOS_DEVELOPMENT_GUIDE.md` | 创建这些文档 |

**重构方案**:

```bash
# 创建文档目录结构
mkdir -p docs/{prd,api,guides,architecture}

# 移动PRD文档
mv PRD_会话架构重构方案.md docs/prd/
mv PRD_科室智能体问诊界面重构方案.md docs/prd/

# 删除重复文件
rm ios.md

# 创建缺失文档
touch docs/api/API_CONTRACT.md
touch docs/guides/DEVELOPMENT_GUIDELINES.md
touch docs/guides/IOS_DEVELOPMENT_GUIDE.md
```

**优先级**: 🟡 P1  
**预计工时**: 0.5天

---

### 3. 图片资源管理混乱

**问题描述**:
- `images/` 目录包含18个截图文件
- 同时存在原图和 `resized/` 子目录
- 缺少图片用途说明

**当前结构**:
```
images/
├── 1.png
├── 2.jpg
├── Simulator Screenshot - iPhone 17 Pro Max - 2025-12-31 at 22.41.46.png
├── Simulator Screenshot - iPhone 17 Pro Max - 2025-12-31 at 22.51.12.png
├── ... (14个截图)
└── resized/
    ├── Simulator Screenshot - iPhone 17 Pro Max - 2025-12-31 at 22.41.46.png
    └── ... (17个截图)
```

**重构方案**:

1. **按用途分类**:
```bash
mkdir -p docs/screenshots/{ios,web,design}
mkdir -p docs/assets/{logos,icons}

# 移动iOS截图
mv images/Simulator\ Screenshot*.png docs/screenshots/ios/

# 移动设计素材
mv images/1.png docs/assets/
mv images/2.jpg docs/assets/

# 删除重复的resized目录
rm -rf images/resized/
```

2. **创建说明文档**:
```markdown
# docs/screenshots/README.md

## iOS 截图
- `ios/` - iOS应用截图，用于PRD和开发文档
- 命名规则: `feature_name_YYYYMMDD.png`

## Web 截图
- `web/` - 管理后台截图

## 设计稿
- `design/` - UI设计稿和原型图
```

**优先级**: 🟡 P1  
**预计工时**: 0.5天

---

### 4. 后端废弃代码未清理

**问题描述**:
`backend/deprecated/` 目录包含9个废弃的Python文件:

```
backend/deprecated/
├── cardio_agent.py
├── cardio_agent_wrapper.py
├── cardio_agents.py
├── derma_agent.py
├── derma_agent_wrapper.py
├── derma_agents.py
├── diagnosis_agent.py
├── diagnosis_agent_wrapper.py
└── diagnosis_agents.py
```

**影响**:
- 增加代码库体积
- 可能误导新开发者
- 影响代码搜索效率

**解决方案**:

**选项A: 完全删除** (推荐)
```bash
rm -rf backend/deprecated/
```

**选项B: 归档到Git分支**
```bash
git checkout -b archive/deprecated-agents
git add backend/deprecated/
git commit -m "Archive deprecated agent implementations"
git push origin archive/deprecated-agents
git checkout main
rm -rf backend/deprecated/
git commit -m "Remove deprecated code (archived in archive/deprecated-agents)"
```

**优先级**: 🟡 P1  
**预计工时**: 0.5天

---

### 5. iOS项目结构问题

**问题描述**:
`LogoExporter.swift` 文件放在错误位置:

```
ios/xinlingyisheng/
├── xinlingyisheng/          # 主代码目录
│   ├── Components/
│   ├── Models/
│   ├── Services/
│   └── ...
├── xinlingyisheng.xcodeproj/
└── LogoExporter.swift       # ❌ 应该在 xinlingyisheng/Utilities/ 目录
```

**解决方案**:

```bash
cd ios/xinlingyisheng/
mv LogoExporter.swift xinlingyisheng/Utilities/

# 在Xcode中更新文件引用
# 1. 打开 xinlingyisheng.xcodeproj
# 2. 删除旧的 LogoExporter.swift 引用
# 3. 添加 Utilities/LogoExporter.swift
```

**优先级**: 🟡 P1  
**预计工时**: 0.5天

---

## 🟢 优化建议 (P2 - 本月内完成)

### 6. 创建缺失的开发文档

根据 `.windsurf/rules/ios.md` 中的要求，需要创建以下文档:

#### 6.1 API契约文档

**文件**: `docs/api/API_CONTRACT.md`

**内容大纲**:
```markdown
# API 接口契约

## 1. 通用规范
- 请求格式: JSON
- 响应格式: JSON
- 认证方式: Bearer Token
- 错误码规范

## 2. 用户认证接口
### POST /api/auth/login
### GET /api/auth/me

## 3. 会话管理接口
### POST /api/sessions
### POST /api/sessions/{id}/messages
### GET /api/sessions/{id}/messages

## 4. 病历管理接口
### POST /api/medical-events/aggregate
### GET /api/medical-events
### GET /api/medical-events/{id}

## 5. 数据模型定义
### Session
### Message
### MedicalEvent
```

#### 6.2 开发规范文档

**文件**: `docs/guides/DEVELOPMENT_GUIDELINES.md`

**内容大纲**:
```markdown
# 开发规范

## 1. 代码风格
- Python: PEP 8
- Swift: Swift Style Guide
- TypeScript: Airbnb Style Guide

## 2. Git工作流
- 分支命名: feature/*, bugfix/*, hotfix/*
- Commit规范: Conventional Commits

## 3. 测试要求
- 单元测试覆盖率 > 70%
- 集成测试必须通过

## 4. 代码审查流程
- PR模板
- 审查清单
```

#### 6.3 iOS开发指南

**文件**: `docs/guides/IOS_DEVELOPMENT_GUIDE.md`

**内容大纲**:
```markdown
# iOS 开发指南

## 1. 设计系统
- 颜色系统: DXYColors
- 字体系统: AdaptiveFont
- 间距系统: AdaptiveSize
- 圆角规范: ScaleFactor

## 2. 响应式布局
- 屏幕适配策略
- 动态字体支持
- 横竖屏适配

## 3. 编码规范
- SwiftUI最佳实践
- Combine使用规范
- 错误处理模式

## 4. 组件库
- 通用组件目录: Components/
- 组件使用示例
```

**优先级**: 🟢 P2  
**预计工时**: 2天

---

### 7. 统一环境配置

**问题描述**:
- `backend/.env.example` - 后端环境变量示例
- `.env.docker` - Docker环境变量
- 缺少统一的配置说明文档

**解决方案**:

创建 `docs/guides/ENVIRONMENT_SETUP.md`:

```markdown
# 环境配置指南

## 1. 后端环境变量

### 开发环境
复制 `backend/.env.example` 到 `backend/.env`:
\`\`\`bash
cp backend/.env.example backend/.env
\`\`\`

必填配置:
- `DATABASE_URL`: 数据库连接字符串
- `JWT_SECRET_KEY`: JWT密钥
- `LLM_API_KEY`: 大模型API密钥

### Docker环境
使用 `.env.docker` 文件，包含:
- 数据库配置
- 服务端口映射
- 网络配置

## 2. 前端环境变量

创建 `frontend/.env`:
\`\`\`
VITE_API_BASE_URL=http://localhost:8000
\`\`\`

## 3. iOS配置

编辑 `ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift`:
\`\`\`swift
static let baseURL = "http://localhost:8000"
\`\`\`
```

**优先级**: 🟢 P2  
**预计工时**: 0.5天

---

### 8. 补充iOS编码规范文档

**问题描述**:
`.windsurf/rules/ios.md` 中提到 `ios/xinlingyisheng/IOS_CODING_RULES.md`，但该文件不存在。

**解决方案**:

创建 `ios/xinlingyisheng/IOS_CODING_RULES.md`:

```markdown
# iOS 编码规范

## 强制性代码规范

### 1. 框架导入规范
- 使用框架前必须先导入
- 常用框架: SwiftUI, Combine, AVFoundation, Photos, PhotosUI

### 2. 数据模型使用规范
- 使用项目内结构体/枚举/类前，必须通过 `grep_search`/`read_file` 查阅真实定义
- 禁止凭记忆编写初始化参数或字段

### 3. Preview 规范
- Preview中使用的数据模型必须与真实结构完全一致
- 严禁伪造字段或缺少必填属性

### 4. 组件组织规范
- 新增组件放入既有目录结构: Components/PhotoCapture, Services, Models
- 沿用项目既定的颜色/字体/间距/圆角系统

### 5. 编译验证规范
- **每次修改完iOS代码后必须立即编译 (⌘+B)**
- 编译失败时:
  1. 阅读Xcode报错信息
  2. 使用工具查阅真实代码定义
  3. 评估改动影响
  4. 修复后再次编译
```

**优先级**: 🟢 P2  
**预计工时**: 0.5天

---

## 📊 重构优先级总结

| 优先级 | 任务 | 预计工时 | 状态 |
|--------|------|----------|------|
| 🔴 P0 | 修复数据库架构不一致 | 3.5天 | ⏳ 待执行 |
| ✅ P1 | 整理文档结构 | 0.5天 | ✅ 已完成 |
| ✅ P1 | 清理图片资源 | 0.5天 | ✅ 已完成 |
| ✅ P1 | 删除废弃代码 | 0.5天 | ✅ 已完成 |
| ✅ P1 | 修复iOS项目结构 | 0.5天 | ✅ 已完成 |
| ✅ P2 | 创建开发文档 | 2天 | ✅ 已完成 |
| ✅ P2 | 统一环境配置 | 0.5天 | ✅ 已完成 |
| ✅ P2 | 补充iOS编码规范 | 0.5天 | ✅ 已完成 |

**已完成**: 7/8 项 (5天工时)  
**剩余**: P0 数据库架构修复 (3.5天)

---

## 🎯 推荐实施路线图

### Week 1: 紧急修复 (P0)
**Day 1-3**: 修复数据库架构
- 统一会话数据模型
- 数据迁移
- 接口重构

**Day 4**: 验证测试
- 功能测试
- 数据完整性验证

### Week 2: 结构优化 (P1)
**Day 5**: 文档和代码整理
- 移动PRD文档
- 清理图片资源
- 删除废弃代码
- 修复iOS项目结构

**Day 6-7**: 补充开发文档 (P2)
- API契约文档
- 开发规范文档
- iOS开发指南
- 环境配置指南

### Week 3: 持续优化
- 代码审查
- 性能优化
- 文档完善

---

## ✅ 验收标准

### P0 验收标准
- [ ] 所有科室的病历生成功能正常工作
- [ ] 历史数据迁移成功，无数据丢失
- [ ] 新旧接口兼容性测试通过

### P1 验收标准
- [ ] 文档目录结构清晰，无重复文件
- [ ] 图片资源分类明确，有说明文档
- [ ] 废弃代码已删除或归档
- [ ] iOS项目结构符合规范

### P2 验收标准
- [ ] 开发文档完整，覆盖API、规范、指南
- [ ] 环境配置文档清晰，新人可快速上手
- [ ] iOS编码规范文档完善

---

## 📝 附录

### A. 推荐的目录结构

```
home-health/
├── backend/
│   ├── app/
│   ├── migrations/
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── ios/
│   └── xinlingyisheng/
│       ├── xinlingyisheng/
│       │   ├── Components/
│       │   ├── Models/
│       │   ├── Services/
│       │   ├── ViewModels/
│       │   ├── Views/
│       │   └── Utilities/
│       ├── xinlingyisheng.xcodeproj/
│       └── IOS_CODING_RULES.md
├── docs/
│   ├── prd/
│   │   ├── PRD_会话架构重构方案.md
│   │   └── PRD_科室智能体问诊界面重构方案.md
│   ├── api/
│   │   ├── API_CONTRACT.md
│   │   ├── AI_ALGORITHM_DESIGN.md
│   │   └── AI_API_DOCUMENTATION.md
│   ├── guides/
│   │   ├── DEVELOPMENT_GUIDELINES.md
│   │   ├── IOS_DEVELOPMENT_GUIDE.md
│   │   └── ENVIRONMENT_SETUP.md
│   ├── architecture/
│   │   └── SYSTEM_ARCHITECTURE.md
│   ├── screenshots/
│   │   ├── ios/
│   │   ├── web/
│   │   └── README.md
│   └── assets/
│       ├── logos/
│       └── icons/
├── .windsurf/
│   ├── rules/
│   │   └── ios.md
│   └── skills/
├── .env.docker
├── .gitignore
├── README.md
├── docker-compose.yml
└── PROJECT_AUDIT_REPORT.md (本文档)
```

### B. 参考资料

- [PRD_会话架构重构方案.md](docs/prd/PRD_会话架构重构方案.md) - 数据库重构详细方案
- [PRD_科室智能体问诊界面重构方案.md](docs/prd/PRD_科室智能体问诊界面重构方案.md) - UI/UX重构方案
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/best-practices/)

---

**报告生成时间**: 2026-01-15  
**下次审核建议**: 2026-02-15 (完成重构后)
