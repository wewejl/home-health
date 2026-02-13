# 灵犀健康 - 项目状态

> **更新日期**: 2026-02-14
> **功能总数**: 52
> **通过**: 51 | **失败**: 0 | **待实现**: 1

---

## 快速开始（每次会话必读）

### 第一步：获取上下文（Getting Up to Speed）

```bash
pwd              # 确认在项目根目录
cat STATUS.md     # 阅读本文档
cat feature-list.json | jq '.metadata'   # 查看功能状态
git log --oneline -5    # 查看最近提交
git status        # 检查工作区状态
```

### 第二步：启动服务（如需要）

```bash
./init.sh         # 启动所有服务
# 或
./init.sh --backend-only    # 仅后端
```

### 第三步：选择任务

从 feature-list.json 中选择状态为 `failing` 或 `pending` 的功能。

**优先级**: failing > pending(P0) > pending(P1) > pending(P2)

---

## 当前待办

### 🟡 待实现 (1项)

**iOS (1项)**:
- `xcode_project_update`: Xcode 项目文件更新（添加 Core/ 和 Features/）
  - *注：此任务为搁置的重构计划，Core/ 和 Features/ 目录未实际创建*

---

## 📊 功能统计说明

`feature-list.json` 追踪的是**顶层模块功能**（52个），而非每个子功能。

**已完成模块示例**：
- 后端：认证、会话、医嘱、事件、语音、科室管理、医生管理、统计等（19个）
- 前端：登录、仪表盘、科室、医生、疾病、药品、知识库、统计等（18个）
- iOS：认证、首页、问诊、医嘱、病历夹、个人中心、知识库等（15个）

详见 `feature-list.json`

---

## 最近完成

### 2026-02-13
- ✅ 长期 Agent 管理工具创建
- ✅ iOS 安全架构重构完成

---

## 项目结构

```
project/
├── backend/          # Python FastAPI 后端
├── frontend/         # React + TypeScript 前端
├── ios/              # Swift + SwiftUI iOS 应用
├── docs/             # 文档
├── scripts/          # 工具脚本
├── feature-list.json # 功能清单（核心）
├── STATUS.md         # 本文件（项目状态）
├── init.sh           # 启动脚本
└── claude-progress.txt # 会话日志
```

---

## 端口信息

| 服务 | 端口 | 地址 |
|------|------|------|
| 后端 API | 8100 | http://localhost:8100 |
| 后端文档 | 8100 | http://localhost:8100/docs |
| 前端 | 5173 | http://localhost:5173 |
| PostgreSQL | 5432 | localhost:5432 |

---

## 快捷命令

```bash
# 后端
docker-compose logs -f backend    # 查看后端日志
docker exec home_health-backend pytest  # 运行测试

# 前端
cd frontend && npm run dev        # 启动前端
cd frontend && npm run build      # 构建前端

# iOS
bash scripts/ios/verify-security.sh  # 安全验证
cd ios/xinlingyisheng && xcodebuild build  # 编译
```

---

## 文档映射

| 旧文档 | 状态 | 替代方案 |
|--------|------|----------|
| PROGRESS.md | ❌ 太大 | 归档，使用 STATUS.md |
| docs/功能清单.md | ❌ 已删除 | 使用 feature-list.json |
| feature-list.json | ✅ 保留 | 核心功能清单 |
| claude-progress.txt | ✅ 保留 | 会话级别日志 |
| README.md | ✅ 保留 | 项目概览 |
| docs/启动指南.md | ✅ 保留 | 详细启动说明 |
| docs/long-running-agent-workflow.md | ✅ 保留 | 工作流详细指南 |
