# 灵犀健康 - 项目状态

> **更新日期**: 2026-02-13
> **功能总数**: 247
> **通过**: 185 | **失败**: 2 | **待实现**: 60

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

### 🔴 高优先级（Failing）
- [ ] 语音服务错误 (`/ws/voice/status` 返回 500)
- [ ] API 类型不一致 (`event_id` 字符串 vs 整数)

### 🟡 中优先级（Pending P0）
- [ ] Xcode 项目文件更新（添加 Core/ 和 Features/）

### 🟢 低优先级（Pending P1/P2）
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
| feature-list.json | ✅ 保留 | 核心功能清单 |
| claude-progress.txt | ✅ 保留 | 会话级别日志 |
| README.md | ✅ 保留 | 项目概览 |
| docs/启动指南.md | ✅ 保留 | 详细启动说明 |
| docs/long-running-agent-workflow.md | ✅ 保留 | 工作流详细指南 |
